"""Frozen runtime prerequisites; native directories and windowed log streams. Units: none."""

from __future__ import annotations

import os
import sys
from pathlib import Path

bundle = Path(sys._MEIPASS)
_dll_handles = []
if sys.platform == "win32":
    native = bundle / "openseespywin"
    if not native.is_dir():
        raise RuntimeError("Bundled OpenSeesPy Windows directory is missing")
    # Hold the handles for the lifetime of the process; do not immediately close them.
    _dll_handles.append(os.add_dll_directory(str(bundle)))
    _dll_handles.append(os.add_dll_directory(str(native)))

if sys.stdout is None or sys.stderr is None:
    if sys.platform == "win32":
        appdata = os.environ.get("APPDATA")
        if not appdata:
            raise RuntimeError("APPDATA is missing; cannot initialise windowed diagnostic logs")
        log_root = Path(appdata) / "struct_ai" / "logs"
    else:
        log_root = (
            Path(os.environ.get("XDG_STATE_HOME", str(Path.home() / ".local/state")))
            / "struct_ai/logs"
        )
    log_root.mkdir(parents=True, exist_ok=True)
    console_log = log_root / "native-console.log"
    if console_log.exists() and console_log.stat().st_size > 1_000_000:
        console_log.replace(log_root / "native-console.previous.log")
    _console_stream = console_log.open("a", encoding="utf-8", buffering=1)
    if sys.stdout is None:
        sys.stdout = _console_stream
    if sys.stderr is None:
        sys.stderr = _console_stream
