"""GPT-2 tokenizer (Hugging Face AutoTokenizer) for Scansion-LM."""

from __future__ import annotations

from pathlib import Path

from transformers import AutoTokenizer

from .paths import MAX_LEN, TOKENIZER_DIR

BASE_TOKENIZER = "distilgpt2"


def train_tokenizer(vocab_size: int | None = None) -> Path:
    """Save the GPT-2 BPE tokenizer with pad = eos. Vocab stays 50257 — no custom tokens."""
    tok = AutoTokenizer.from_pretrained(BASE_TOKENIZER)
    if tok.pad_token is None:
        tok.pad_token = tok.eos_token
        tok.pad_token_id = tok.eos_token_id
    tok.model_max_length = MAX_LEN
    tok.padding_side = "right"
    tok.truncation_side = "right"
    TOKENIZER_DIR.mkdir(parents=True, exist_ok=True)
    tok.save_pretrained(str(TOKENIZER_DIR))
    return TOKENIZER_DIR


def load_tokenizer(path: Path | None = None):
    p = path or TOKENIZER_DIR
    tok = AutoTokenizer.from_pretrained(str(p))
    if tok.pad_token is None:
        tok.pad_token = tok.eos_token or "<|endoftext|>"
    tok.model_max_length = MAX_LEN
    tok.padding_side = "right"
    return tok
