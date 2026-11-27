"""Repository launcher for the service-backed code audit. Units: per reported record."""

from __future__ import annotations

import sys
from pathlib import Path

# Support the explicitly requested `python tools/list_unverified.py` in a fresh checkout.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from struct_ai.codes.audit import main

if __name__ == "__main__":
    raise SystemExit(main())
