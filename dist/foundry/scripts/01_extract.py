#!/usr/bin/env python3
"""Step 1 — extract meter/rhyme DNA and build the original-sheet corpus."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scansion_lm.corpus import build_all  # noqa: E402

if __name__ == "__main__":
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 480
    print(json.dumps(build_all(n), indent=2))
