#!/usr/bin/env python3
"""Step 2 — train the Hugging Face BPE tokenizer on the corpus."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scansion_lm.tokenize import train_tokenizer  # noqa: E402

if __name__ == "__main__":
    print(train_tokenizer())
