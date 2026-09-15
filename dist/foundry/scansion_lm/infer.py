"""Run Scansion-LM inference from the Hugging Face checkpoint.

The causal LM writes sung lines. The sandwich encoder wraps those lines in
MasterofSFL metatags. No assembler lyrics, no canned title-hooks.
"""

from __future__ import annotations

import re
from functools import lru_cache

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

from .assemble import form_spec, pack_generation, wrap_lyrics
from .paths import EXPORT, MAX_LEN

_MTIME = None
BASE_MODEL = "distilgpt2"

KINDS = ("Verse", "Chorus", "Bridge", "Pre-Chorus", "Hook")


@lru_cache(maxsize=1)
def _load_bundle_cached(source: str):
    tok = AutoTokenizer.from_pretrained(source)
    model = AutoModelForCausalLM.from_pretrained(source)
    if tok.pad_token_id is None:
        tok.pad_token = tok.eos_token or "<|endoftext|>"
    model.eval()
    if hasattr(model.config, "use_cache"):
        model.config.use_cache = True
    return tok, model


def _export_path() -> str | None:
    weights = EXPORT / "model.safetensors"
    alt = EXPORT / "pytorch_model.bin"
    path = weights if weights.exists() else alt
    if path.exists() and (EXPORT / "config.json").exists():
        return str(EXPORT)
    return None


def load_bundle():
    global _MTIME
    src = _export_path() or BASE_MODEL
    if src != BASE_MODEL:
        mt = (EXPORT / "model.safetensors").stat().st_mtime if (EXPORT / "model.safetensors").exists() else 0.0
        if _MTIME != mt:
            _load_bundle_cached.cache_clear()
            _MTIME = mt
    return _load_bundle_cached(src)


def ready() -> bool:
    return _export_path() is not None


def generate_continuation(
    prompt: str,
    max_new: int = 80,
    temperature: float = 0.85,
    do_sample: bool = True,
) -> tuple[str, str]:
    """Return (new_text, full_text) from the checkpoint."""
    tok, model = load_bundle()
    room = max(64, MAX_LEN - 8)
    enc = tok(prompt, return_tensors="pt", add_special_tokens=False, truncation=False)
    ids = enc["input_ids"]
    if ids.shape[1] > room:
        keep_head = min(48, room // 3)
        keep_tail = room - keep_head
        ids = torch.cat([ids[:, :keep_head], ids[:, -keep_tail:]], dim=1)
        enc = {"input_ids": ids, "attention_mask": torch.ones_like(ids)}
    prompt_len = int(enc["input_ids"].shape[1])
    new_tokens = max(12, min(max_new, MAX_LEN - prompt_len - 2))
    eos = tok.eos_token_id if tok.eos_token_id is not None else tok.pad_token_id
    gen_kw: dict = {
        "max_new_tokens": new_tokens,
        "pad_token_id": tok.pad_token_id,
        "eos_token_id": eos,
        "use_cache": True,
        "repetition_penalty": 1.12,
        "no_repeat_ngram_size": 4,
    }
    if do_sample and temperature > 0:
        gen_kw.update(do_sample=True, top_k=50, top_p=0.92, temperature=float(temperature))
    else:
        gen_kw.update(do_sample=False)
    with torch.no_grad():
        out = model.generate(**enc, **gen_kw)
    full = tok.decode(out[0], skip_special_tokens=False)
    new = tok.decode(out[0][prompt_len:], skip_special_tokens=False)
    for sp in ("<|endoftext|>", "<|end|>", "<|sheet|>", "<|brief|>"):
        if sp in new:
            new = new.split(sp, 1)[0]
    return new, full


def generate_text(prompt: str, max_new: int = 80, temperature: float = 0.85, do_sample: bool = True) -> str:
    new, _ = generate_continuation(prompt, max_new=max_new, temperature=temperature, do_sample=do_sample)
    return new


def _cut_block(text: str, kind: str) -> str:
    others = [k for k in KINDS if k != kind]
    for o in others:
        needle = f"\n{o}:"
        if needle in text:
            text = text.split(needle, 1)[0]
    if "\nTitle:" in text:
        text = text.split("\nTitle:", 1)[0]
    if "\nIdea:" in text:
        text = text.split("\nIdea:", 1)[0]
    return text


_BANNED = re.compile(
    r"twitter|wikipedia|http|www\.|subscribe|click here|looking forward to the game|"
    r"custom version|\.com\b|youtube|facebook",
    re.I,
)


def _is_lyric_line(ln: str) -> bool:
    if not ln:
        return False
    if _BANNED.search(ln):
        return False
    if re.search(r"[_]{3,}|[-]{4,}|[=]{3,}", ln):
        return False
    if re.search(r"[가-힣一-龥ぁ-ゟ]", ln):
        return False
    letters = len(re.findall(r"[A-Za-z]", ln))
    if letters < 6 or letters / max(len(ln), 1) < 0.5:
        return False
    words = re.findall(r"[A-Za-z']+", ln)
    if not (2 <= len(words) <= 16):
        return False
    return True


def _lyric_lines_from_text(chunk: str, kind: str, n: int) -> list[str]:
    chunk = _cut_block(chunk or "", kind)
    out: list[str] = []
    seen: set[str] = set()
    for raw in chunk.replace(".", ".\n").splitlines():
        ln = raw.strip().strip('"').strip("'")
        if not ln:
            continue
        if ln.endswith(":") and len(ln.split()) <= 4:
            continue
        if ln.startswith(("Title:", "Idea:", "STYLE:", "LYRICS:", "POV:", "GENRE:")):
            continue
        if ln.startswith("[") or ln.startswith("<|"):
            continue
        ln = re.sub(r"^[\W_]+", "", ln).strip()
        ln = re.sub(r"\s+", " ", ln)
        if len(ln) > 100:
            ln = ln[:100].rsplit(" ", 1)[0].strip()
        if not _is_lyric_line(ln):
            continue
        key = ln.lower()
        if key in seen:
            continue
        seen.add(key)
        out.append(ln)
        if len(out) >= n:
            break
    return out[:n]


def _first_clause(text: str) -> str:
    raw = re.split(r"[.;\n]", text or "")
    for c in raw:
        c = c.strip().strip('"')
        if len(c) >= 8 and re.search(r"[A-Za-z]{3,}", c):
            return c[0].upper() + c[1:] if c[0].islower() else c
    return (text or "").strip()[:80]


def lyric_header(composer: dict, kind: str, running: str = "") -> str:
    title = (composer.get("title") or "Untitled").strip() or "Untitled"
    idea = (composer.get("idea") or "Write a specific story that fits the pocket.").strip()
    if running:
        return running if running.endswith("\n") else running + "\n"
    return f"Title: {title}\nIdea: {idea}\n"


def generate_lyric_lines(composer: dict, kind: str, n: int, running: str = "") -> list[str]:
    """Generate n sung lines with the causal LM. Every kept line is model output."""
    header = lyric_header(composer, kind, running)
    prompt = header + f"{kind}:\n"
    lines: list[str] = []
    attempts = (
        (0.7, True, 140),
        (0.85, True, 180),
        (0.95, True, 200),
        (1.05, True, 220),
        (0.0, False, 140),
        (0.9, True, 240),
        (1.1, True, 200),
        (0.8, True, 180),
    )
    for t, sample, tokens in attempts:
        chunk, _ = generate_continuation(
            prompt if not lines else prompt + "\n".join(lines) + "\n",
            max_new=tokens,
            temperature=t,
            do_sample=sample,
        )
        for ln in _lyric_lines_from_text(chunk, kind, n):
            if ln.lower() not in {x.lower() for x in lines}:
                lines.append(ln)
            if len(lines) >= n:
                break
        if len(lines) >= n:
            break
    if len(lines) < n:
        stem = _first_clause(composer.get("idea") or "") or (composer.get("title") or "Tonight")
        for t in (0.85, 1.0, 0.7, 0.0):
            chunk, _ = generate_continuation(stem + f"\n{kind}:\n", max_new=160, temperature=t, do_sample=t > 0)
            for ln in _lyric_lines_from_text(chunk.replace(". ", ".\n"), kind, n):
                if ln.lower() not in {x.lower() for x in lines}:
                    lines.append(ln)
                if len(lines) >= n:
                    break
            if len(lines) >= n:
                break
            sent = chunk.strip().split("\n")[0].strip()
            sent = re.sub(r"\s+", " ", sent)[:100]
            if _is_lyric_line(sent) and sent.lower() not in {x.lower() for x in lines}:
                lines.append(sent)
            if len(lines) >= n:
                break
    if not lines:
        raise RuntimeError("Scansion-LM produced no lyric lines from the checkpoint.")
    return lines[:n]


def generate_sheet_from_lm(composer: dict, live_style: str = "", dna: str = "") -> dict:
    from .eval_guide import score_sheet

    spec = form_spec(composer)
    blocks: list[tuple[str, list[str]]] = []
    raw_chunks: list[str] = []
    for tag, kind, n in spec:
        last_err = ""
        lines: list[str] = []
        for _try in range(3):
            try:
                lines = generate_lyric_lines(composer, kind, n)
                if lines:
                    break
            except Exception as exc:
                last_err = str(exc)
                lines = []
        if not lines:
            raise RuntimeError(last_err or f"Checkpoint wrote no {kind} lines.")
        blocks.append((tag, lines))
        raw_chunks.append(tag + "\n" + "\n".join(lines))
    style, lyrics, title = wrap_lyrics(composer, blocks, live_style, dna)
    packed = pack_generation(composer, style, lyrics, title, raw="\n---\n".join(raw_chunks))
    sc = score_sheet(style, lyrics)
    packed["guideScore"] = {
        "passed": sc["passed"],
        "total": sc["total"],
        "score": sc["score"],
        "checks": sc["checks"],
    }
    return packed


def infer_composer(
    composer: dict,
    live_style: str = "",
    dna: str = "",
    iterate_hint: str = "",
    previous_lyrics: str = "",
) -> dict:
    from .eval_guide import score_sheet

    composer = dict(composer)
    if iterate_hint:
        idea = (composer.get("idea") or "").strip()
        composer["idea"] = (idea + f" Rewrite toward: {iterate_hint}").strip()
        if previous_lyrics and "[Chorus" in previous_lyrics:
            composer["idea"] += " Keep the title hook in the chorus."
    packed = generate_sheet_from_lm(composer, live_style, dna)
    if iterate_hint:
        packed["whyItWorks"] += f" Iterate: {iterate_hint}"
        sc = score_sheet(packed["stylePrompt"], packed["lyrics"])
        packed["guideScore"] = {
            "passed": sc["passed"],
            "total": sc["total"],
            "score": sc["score"],
            "checks": sc["checks"],
        }
    return packed
