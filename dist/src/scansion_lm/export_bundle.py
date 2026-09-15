"""Write a complete Hugging Face folder: weights, tokenizer, card, LFS, license."""

from __future__ import annotations

import json
import re
import shutil
from pathlib import Path

from .paths import EXPORT, LICENSE, MAX_LEN, METRICS, MODEL_CARD, STATUS, TOKENIZER_DIR

FRONTMATTER = """---
language:
  - en
license: apache-2.0
library_name: transformers
pipeline_tag: text-generation
base_model: distilgpt2
tags:
  - gpt2
  - lyrics
  - suno
  - music
  - scansion
  - text-generation
widget:
  - text: "Title: Heat Line\\nIdea: A man scraping survival out of desert heat, stubborn will over panic.\\nVerse:\\n"
    example_title: Desert verse
  - text: "Title: As It Stays\\nIdea: Driving the empty freeway after a fight you cannot unsay.\\nChorus:\\n"
    example_title: Night chorus
---
"""

LICENSE_TEXT = """Apache License
Version 2.0, January 2004
http://www.apache.org/licenses/LICENSE-2.0

Copyright 2026 Scansion

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""


def _last_metrics() -> dict:
    if not METRICS.exists():
        return {}
    last = {}
    for line in METRICS.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            last = json.loads(line)
        except json.JSONDecodeError:
            continue
    return last


def _status() -> dict:
    if not STATUS.exists():
        return {}
    try:
        return json.loads(STATUS.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def _config() -> dict:
    p = EXPORT / "config.json"
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def write_license(dest: Path | None = None) -> Path:
    dest = dest or (EXPORT / "LICENSE")
    src = LICENSE_TEXT
    if LICENSE.exists():
        src = LICENSE.read_text(encoding="utf-8")
    else:
        LICENSE.write_text(LICENSE_TEXT, encoding="utf-8")
    dest.write_text(src, encoding="utf-8")
    return dest


def write_gitattributes(dest: Path | None = None) -> Path:
    dest = dest or (EXPORT / ".gitattributes")
    dest.write_text(
        "*.safetensors filter=lfs diff=lfs merge=lfs -text\n"
        "*.bin filter=lfs diff=lfs merge=lfs -text\n",
        encoding="utf-8",
    )
    return dest


def write_added_tokens() -> Path:
    cfg = EXPORT / "tokenizer_config.json"
    added: dict = {}
    if cfg.exists():
        data = json.loads(cfg.read_text(encoding="utf-8"))
        decoder = data.get("added_tokens_decoder") or {}
        for idx, meta in decoder.items():
            content = meta.get("content") if isinstance(meta, dict) else None
            if content and meta.get("special"):
                added[content] = int(idx)
    dest = EXPORT / "added_tokens.json"
    dest.write_text(json.dumps(added, indent=2), encoding="utf-8")
    return dest


def write_vocab_merges() -> None:
    src_vocab = TOKENIZER_DIR / "vocab.json"
    src_merges = TOKENIZER_DIR / "merges.txt"
    tok_json = EXPORT / "tokenizer.json"
    if src_vocab.exists():
        shutil.copy2(src_vocab, EXPORT / "vocab.json")
    if src_merges.exists():
        shutil.copy2(src_merges, EXPORT / "merges.txt")
    if (EXPORT / "vocab.json").exists() and (EXPORT / "merges.txt").exists():
        return
    if tok_json.exists():
        data = json.loads(tok_json.read_text(encoding="utf-8"))
        model = data.get("model") or {}
        (EXPORT / "vocab.json").write_text(json.dumps(model.get("vocab") or {}, ensure_ascii=False), encoding="utf-8")
        merges = model.get("merges") or []
        lines = ["#version: 0.2"]
        for m in merges:
            if isinstance(m, str):
                lines.append(m)
            elif isinstance(m, (list, tuple)):
                lines.append(" ".join(str(x) for x in m))
        (EXPORT / "merges.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_generation_config(tok=None) -> Path:
    pad = eos = bos = 50256
    if tok is not None:
        pad = tok.pad_token_id if tok.pad_token_id is not None else 50256
        eos = tok.eos_token_id if tok.eos_token_id is not None else 50256
        bos = tok.bos_token_id if tok.bos_token_id is not None else eos
    else:
        cfg = _config()
        pad = cfg.get("pad_token_id", 50256)
        eos = cfg.get("eos_token_id", 50256)
        bos = cfg.get("bos_token_id", 50256)
    gen = {
        "bos_token_id": bos,
        "eos_token_id": eos,
        "pad_token_id": pad,
        "max_new_tokens": 80,
        "do_sample": True,
        "temperature": 0.85,
        "top_p": 0.92,
        "repetition_penalty": 1.15,
        "transformers_version": "4.46.3",
    }
    dest = EXPORT / "generation_config.json"
    dest.write_text(json.dumps(gen, indent=2), encoding="utf-8")
    return dest


def write_model_card(dest: Path | None = None) -> Path:
    dest = dest or (EXPORT / "README.md")
    st = _status()
    met = _last_metrics()
    cfg = _config()
    body = MODEL_CARD.read_text(encoding="utf-8") if MODEL_CARD.exists() else "# Scansion-LM\n"
    if body.startswith("---"):
        rest = body.split("---", 2)
        body = rest[2].lstrip() if len(rest) >= 3 else body
    extra = [
        FRONTMATTER,
        body,
        "",
        "## Checkpoint",
        "",
        f"- architecture: `{cfg.get('architectures', ['GPT2LMHeadModel'])}`",
        f"- vocab_size: `{cfg.get('vocab_size', '—')}`",
        f"- n_positions: `{cfg.get('n_positions', MAX_LEN)}`",
        f"- n_layer / n_embd / n_head: `{cfg.get('n_layer', '—')} / {cfg.get('n_embd', '—')} / {cfg.get('n_head', '—')}`",
        f"- parameters: `{st.get('params', '—')}`",
        f"- steps: `{st.get('step', '—')}/{st.get('steps', '—')}`",
        f"- train loss (avg): `{st.get('loss', met.get('avg', '—'))}`",
        f"- examples: `{st.get('examples', '—')}`",
        "",
        "Load with vanilla Transformers — no custom `auto_map`:",
        "",
        "```python",
        "from transformers import AutoModelForCausalLM, AutoTokenizer",
        "tok = AutoTokenizer.from_pretrained(\"scansion-lm\")",
        "model = AutoModelForCausalLM.from_pretrained(\"scansion-lm\")",
        "prompt = \"\"\"Title: Heat Line",
        "Idea: A man scraping survival out of desert heat, stubborn will over panic.",
        "Verse:",
        "\"\"\"",
        "ids = tok(prompt, return_tensors=\"pt\")",
        "out = model.generate(**ids, max_new_tokens=80, do_sample=True, temperature=0.85,",
        "                    pad_token_id=tok.pad_token_id, eos_token_id=tok.eos_token_id)",
        "print(tok.decode(out[0], skip_special_tokens=False))",
        "```",
        "",
        "Upload:",
        "",
        "```bash",
        "huggingface-cli upload ./export scansion-lm --repo-type model",
        "```",
        "",
    ]
    dest.write_text("\n".join(extra), encoding="utf-8")
    return dest


def verify_hub_load() -> dict:
    if not (EXPORT / "config.json").exists():
        return {"ok": False, "error": "no config.json"}
    try:
        from transformers import AutoModelForCausalLM, AutoTokenizer

        tok = AutoTokenizer.from_pretrained(str(EXPORT))
        model = AutoModelForCausalLM.from_pretrained(str(EXPORT))
        if tok.pad_token_id is None:
            tok.pad_token = tok.eos_token
        prompt = (
            "Title: Heat Line\n"
            "Idea: A man scraping survival out of desert heat, stubborn will over panic.\n"
            "Verse:\n"
        )
        enc = tok(prompt, return_tensors="pt")
        out = model.generate(
            **enc,
            max_new_tokens=80,
            do_sample=True,
            temperature=0.8,
            top_p=0.92,
            pad_token_id=tok.pad_token_id,
            eos_token_id=tok.eos_token_id,
            repetition_penalty=1.12,
        )
        text = tok.decode(out[0], skip_special_tokens=False)
        new = tok.decode(out[0][enc["input_ids"].shape[1] :], skip_special_tokens=False)
        new = new.split("<|endoftext|>")[0]
        lines = [ln.strip() for ln in new.splitlines() if ln.strip() and not ln.strip().startswith("[")]
        english = [ln for ln in lines if re.search(r"[A-Za-z]{3,}", ln)]
        spam = bool(re.search(r"(\[Verse \d+\].*){3,}", text.replace("\n", " ")))
        ok = len(english) >= 2 and not spam
        auto_map = bool(getattr(model.config, "auto_map", None))
        return {
            "ok": bool(ok) and not auto_map,
            "arch": list(getattr(model.config, "architectures", []) or []),
            "vocab": len(tok),
            "params": int(sum(p.numel() for p in model.parameters())),
            "english_lines": english[:6],
            "preview": new[:500],
            "auto_map": auto_map,
        }
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


def finalize_export(tok=None) -> dict:
    EXPORT.mkdir(parents=True, exist_ok=True)
    write_generation_config(tok)
    write_added_tokens()
    write_vocab_merges()
    write_license()
    write_gitattributes()
    write_model_card()
    verify = verify_hub_load()
    (EXPORT / "hub_check.json").write_text(json.dumps(verify, indent=2), encoding="utf-8")
    files = sorted({p.name for p in EXPORT.iterdir()})
    required = [
        "config.json",
        "model.safetensors",
        "tokenizer.json",
        "tokenizer_config.json",
        "special_tokens_map.json",
        "vocab.json",
        "merges.txt",
        "generation_config.json",
        "README.md",
        "LICENSE",
        ".gitattributes",
    ]
    missing = [f for f in required if not (EXPORT / f).exists() and not (EXPORT / f.replace("model.safetensors", "pytorch_model.bin")).exists()]
    if "model.safetensors" in missing and (EXPORT / "pytorch_model.bin").exists():
        missing.remove("model.safetensors")
    return {
        "ok": not missing and bool(verify.get("ok")),
        "dir": str(EXPORT),
        "files": files,
        "missing": missing,
        "tokenizer": (EXPORT / "tokenizer.json").exists(),
        "status": {k: _status().get(k) for k in ("phase", "step", "steps", "loss", "params", "trained", "training")},
        "verify": verify,
    }


def export_ready() -> dict:
    if (EXPORT / "config.json").exists():
        return finalize_export()
    return {
        "ok": False,
        "dir": str(EXPORT),
        "files": sorted(p.name for p in EXPORT.iterdir()) if EXPORT.exists() else [],
        "tokenizer": False,
        "status": {k: _status().get(k) for k in ("phase", "step", "steps", "loss", "params", "trained", "training")},
        "error": "Train first — no checkpoint on disk.",
    }
