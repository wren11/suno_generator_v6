#!/usr/bin/env python3
"""Step 3 — fine-tune distilgpt2 on original lyric verses (CPU, safetensors)."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scansion_lm.train import train  # noqa: E402

if __name__ == "__main__":
    steps = int(sys.argv[1]) if len(sys.argv) > 1 else 300
    corpus_n = int(sys.argv[2]) if len(sys.argv) > 2 else 640
    print(json.dumps(train(steps=steps, corpus_n=corpus_n), indent=2))
