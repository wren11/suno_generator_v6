#!/usr/bin/env python3
"""Step 6 — serve the loopback inference sidecar."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scansion_lm.server import serve  # noqa: E402

if __name__ == "__main__":
    serve()
