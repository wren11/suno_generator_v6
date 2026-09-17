"""Fine-tune distilgpt2 on original lyric verses (Hugging Face Causal LM)."""

from __future__ import annotations

import json
import os
import time

import torch
from torch.utils.data import DataLoader, Dataset
from transformers import AutoModelForCausalLM, get_cosine_schedule_with_warmup

from .corpus import build_all
from .paths import CORPUS_JSONL, EXPORT, MAX_LEN, METRICS, RUNS, STATUS, TRAIN_LOG
from .tokenize import load_tokenizer, train_tokenizer

BASE_MODEL = "distilgpt2"
TRAIN_MAX_LEN = 256


class LyricDataset(Dataset):
    def __init__(self, records: list[dict], tokenizer, max_len: int):
        self.ids: list[torch.Tensor] = []
        self.prompt_lens: list[int] = []
        overflow = 0
        for rec in records:
            text = rec.get("text") or ""
            prompt = rec.get("prompt") or ""
            if not text.strip():
                continue
            full = tokenizer(text, add_special_tokens=False)["input_ids"]
            p_ids = tokenizer(prompt, add_special_tokens=False)["input_ids"] if prompt else []
            if len(full) > max_len:
                overflow += 1
                full = full[:max_len]
            if len(full) < 16:
                continue
            plen = min(len(p_ids), max(0, len(full) - 8))
            self.ids.append(torch.tensor(full, dtype=torch.long))
            self.prompt_lens.append(int(plen))
        self.overflow = overflow

    def __len__(self) -> int:
        return len(self.ids)

    def __getitem__(self, i: int) -> tuple[torch.Tensor, int]:
        return self.ids[i], self.prompt_lens[i]


def collate(batch: list[tuple[torch.Tensor, int]], pad_id: int, max_len: int = TRAIN_MAX_LEN):
    m = min(max(x.size(0) for x, _ in batch), max_len)
    ids = torch.full((len(batch), m), pad_id, dtype=torch.long)
    mask = torch.zeros((len(batch), m), dtype=torch.long)
    labels = torch.full((len(batch), m), -100, dtype=torch.long)
    for i, (x, plen) in enumerate(batch):
        n = min(x.size(0), m)
        ids[i, :n] = x[:n]
        mask[i, :n] = 1
        cut = min(max(plen, 0), n - 1)
        labels[i, cut:n] = x[cut:n]
    return ids, mask, labels


def write_status(**kw) -> None:
    STATUS.parent.mkdir(parents=True, exist_ok=True)
    cur = {}
    if STATUS.exists():
        try:
            cur = json.loads(STATUS.read_text())
        except json.JSONDecodeError:
            cur = {}
    cur.update(kw)
    cur["updated_at"] = time.time()
    STATUS.write_text(json.dumps(cur, indent=2))


def train(
    steps: int = 300,
    batch_size: int = 1,
    lr: float = 3e-5,
    corpus_n: int = 640,
    resume: bool = False,
    rebuild: bool = True,
) -> dict:
    torch.set_num_threads(min(8, os.cpu_count() or 4))
    RUNS.mkdir(parents=True, exist_ok=True)
    write_status(phase="extract", training=True, step=0, loss=None, error=None, resume=resume)
    if rebuild:
        build_all(corpus_n)
    write_status(phase="tokenize")
    train_tokenizer()
    tok = load_tokenizer()
    records = []
    with open(CORPUS_JSONL, "r", encoding="utf-8") as f:
        for l in f:
            l = l.strip()
            if l:
                try:
                    records.append(json.loads(l))
                except Exception:
                    pass
    ds = LyricDataset(records, tok, TRAIN_MAX_LEN)
    pad_id = tok.pad_token_id if tok.pad_token_id is not None else tok.eos_token_id
    bos_id = tok.bos_token_id if tok.bos_token_id is not None else pad_id
    eos_id = tok.eos_token_id if tok.eos_token_id is not None else pad_id
    loader = DataLoader(
        ds,
        batch_size=batch_size,
        shuffle=True,
        collate_fn=lambda b: collate(b, pad_id, TRAIN_MAX_LEN),
        drop_last=True,
    )
    saved_cfg = {}
    if (EXPORT / "config.json").exists():
        try:
            saved_cfg = json.loads((EXPORT / "config.json").read_text())
        except json.JSONDecodeError:
            saved_cfg = {}
    same_arch = (
        saved_cfg.get("n_embd") == 768
        and saved_cfg.get("n_layer") == 6
        and saved_cfg.get("vocab_size") in (50257, 50258, 50259, 50260)
    )
    if resume and same_arch and (EXPORT / "model.safetensors").exists():
        model = AutoModelForCausalLM.from_pretrained(str(EXPORT))
    else:
        model = AutoModelForCausalLM.from_pretrained(BASE_MODEL)
    if model.get_input_embeddings().weight.size(0) != len(tok):
        model.resize_token_embeddings(len(tok), mean_resizing=False)
    for p in model.parameters():
        p.requires_grad = False
    n_layer = int(model.config.n_layer)
    for i in range(max(0, n_layer - 4), n_layer):
        for p in model.transformer.h[i].parameters():
            p.requires_grad = True
    for p in model.transformer.ln_f.parameters():
        p.requires_grad = True
    model.config.bos_token_id = bos_id
    model.config.eos_token_id = eos_id
    model.config.pad_token_id = pad_id
    model.config.architectures = ["GPT2LMHeadModel"]
    model.config.use_cache = False
    if hasattr(model.config, "task_specific_params"):
        model.config.task_specific_params = {
            "text-generation": {"do_sample": True, "max_new_tokens": 80, "temperature": 0.85}
        }
    device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
    model.to(device)
    model.train()
    trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
    opt = torch.optim.AdamW(
        [p for p in model.parameters() if p.requires_grad],
        lr=lr,
        betas=(0.9, 0.95),
        weight_decay=0.01,
    )
    warmup = max(8, steps // 10)
    sched = get_cosine_schedule_with_warmup(opt, warmup, max(steps, warmup + 1))
    params = sum(p.numel() for p in model.parameters())
    write_status(
        phase="train",
        params=params,
        trainable=trainable,
        examples=len(ds),
        step=0,
        vocab=len(tok),
        overflow=ds.overflow,
    )
    METRICS.write_text("")
    t0 = time.time()
    step = 0
    running = 0.0
    it = iter(loader)
    log = TRAIN_LOG.open("a", encoding="utf-8")
    try:
        while step < steps:
            try:
                batch = next(it)
            except StopIteration:
                it = iter(loader)
                batch = next(it)
            ids, mask, labels = batch
            ids, mask, labels = ids.to(device), mask.to(device), labels.to(device)
            out = model(input_ids=ids, attention_mask=mask, labels=labels)
            loss = out.loss
            loss.backward()
            torch.nn.utils.clip_grad_norm_([p for p in model.parameters() if p.requires_grad], 1.0)
            opt.step()
            sched.step()
            opt.zero_grad()
            step += 1
            running = 0.9 * running + 0.1 * float(loss.item()) if step > 1 else float(loss.item())
            if step % 5 == 0 or step == 1:
                rec = {"step": step, "loss": float(loss.item()), "avg": running, "sec": time.time() - t0}
                with METRICS.open("a", encoding="utf-8") as mf:
                    mf.write(json.dumps(rec) + "\n")
                write_status(
                    phase="train",
                    step=step,
                    steps=steps,
                    loss=rec["loss"],
                    avg=running,
                    params=params,
                    vocab=len(tok),
                    examples=len(ds),
                )
                log.write(f"step {step}/{steps} loss={rec['loss']:.4f} avg={running:.4f}\n")
                log.flush()
    finally:
        log.close()
    write_status(phase="export", training=True)
    EXPORT.mkdir(parents=True, exist_ok=True)
    model.eval()
    model.config.use_cache = True
    model.to("cpu")
    model.save_pretrained(str(EXPORT), safe_serialization=True)
    tok.save_pretrained(str(EXPORT))
    from .export_bundle import finalize_export

    info = finalize_export(tok)
    write_status(
        phase="ready",
        training=False,
        trained=True,
        step=step,
        steps=steps,
        loss=running,
        params=params,
        vocab=len(tok),
        examples=len(ds),
        export=str(EXPORT),
        elapsed=time.time() - t0,
        overflow=ds.overflow,
        hub_ok=bool(info.get("verify", {}).get("ok")),
        trainable=trainable,
    )
    return {
        "steps": step,
        "loss": running,
        "params": params,
        "examples": len(ds),
        "vocab": len(tok),
        "overflow": ds.overflow,
        "export": info,
        "max_len": MAX_LEN,
        "train_max_len": TRAIN_MAX_LEN,
    }


if __name__ == "__main__":
    print(json.dumps(train(), indent=2))
