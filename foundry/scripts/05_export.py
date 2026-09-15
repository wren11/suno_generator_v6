#!/usr/bin/env python3
"""Step 5 — write the Hugging Face export (card, LFS attrs, vocab, LICENSE)."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scansion_lm.export_bundle import export_ready  # noqa: E402

if __name__ == "__main__":
    info = export_ready()
    print(json.dumps(info, indent=2))
    if not info.get("ok"):
        sys.exit(1)
