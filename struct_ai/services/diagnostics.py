"""Local operational diagnostics, kept outside deterministic result hashes. Units: none."""

from __future__ import annotations

import json
import logging
import os
import platform
import sys
from importlib.metadata import PackageNotFoundError, version
from logging.handlers import RotatingFileHandler
from pathlib import Path

from struct_ai import __version__


def log_directory() -> Path:
    """Locate APPDATA/struct_ai/logs on Windows; XDG state on Linux. Units: none."""
    if sys.platform == "win32":
        appdata = os.environ.get("APPDATA")
        if not appdata:
            raise RuntimeError("APPDATA is missing; cannot choose a Windows log directory silently")
        return Path(appdata) / "struct_ai" / "logs"
    state = Path(os.environ.get("XDG_STATE_HOME", str(Path.home() / ".local/state")))
    return state / "struct_ai" / "logs"


def configure_logging() -> Path:
    """Set up a bounded UTF-8 operational log; file failures propagate. Units: bytes for size."""
    folder = log_directory()
    folder.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger("struct_ai")
    if not logger.handlers:
        handler = RotatingFileHandler(
            folder / "struct_ai.log", maxBytes=1_000_000, backupCount=3, encoding="utf-8"
        )
        handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        logger.propagate = False
    return folder


def diagnostics_text() -> str:
    """Return versions/capabilities, never secrets or project data. Units: none."""
    packages: dict[str, str] = {}
    for package in ("pydantic", "openseespy", "PySide6-Essentials", "pyinstaller"):
        try:
            packages[package] = version(package)
        except PackageNotFoundError:
            packages[package] = "not installed / metadata absent"
    return json.dumps(
        {
            "engine_version": __version__,
            "capability": "M0b solver diagnostic only; building design NOT implemented",
            "python": platform.python_version(),
            "platform": platform.platform(),
            "architecture": platform.machine(),
            "frozen": bool(getattr(sys, "frozen", False)),
            "packages": packages,
            "log_folder": str(log_directory()),
            "llm": "not implemented / not loaded by struct_ai",
            "license_notice": "OpenSeesPy commercial redistribution requires a separate licence",
        },
        indent=2,
        ensure_ascii=False,
    )
