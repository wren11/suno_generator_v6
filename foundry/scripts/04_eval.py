#!/usr/bin/env python3
"""Step 4 — score gold sheets and the trained model against the Suno guide."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scansion_lm.eval_guide import eval_model, gold_sheet_score  # noqa: E402

if __name__ == "__main__":
    print(json.dumps({"gold": gold_sheet_score(), "model": eval_model()}, indent=2))
