"""Run the same non-skipping gates locally and in CI. Units: none."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def main() -> int:
    """Run pytest and both lint/format checks, propagating failures. Units: none."""
    root = Path(__file__).resolve().parents[1]
    for arguments in (
        ["-m", "pytest"],
        ["-m", "ruff", "check", "."],
        ["-m", "ruff", "format", "--check", "."],
    ):
        completed = subprocess.run([sys.executable, *arguments], cwd=root, check=False)
        if completed.returncode:
            return completed.returncode
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
