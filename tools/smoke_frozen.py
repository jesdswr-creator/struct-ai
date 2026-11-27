"""Exercise a real onedir executable outside the source tree. Units: seconds, evidence JSON."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import tempfile
from pathlib import Path


def main() -> int:
    """Test solver and GUI with external Python/library paths removed. Units: 60 s per command."""
    parser = argparse.ArgumentParser(description="Smoke test a real M0b frozen executable")
    parser.add_argument("executable", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    executable = args.executable.resolve(strict=True)
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    environment = os.environ.copy()
    for name in (
        "PYTHONPATH",
        "PYTHONHOME",
        "LD_LIBRARY_PATH",
        "LD_PRELOAD",
        "QT_PLUGIN_PATH",
        "QT_QPA_PLATFORM_PLUGIN_PATH",
    ):
        environment.pop(name, None)
    if os.name == "nt":
        system_root = Path(environment["SystemRoot"])
        environment["PATH"] = os.pathsep.join((str(system_root / "System32"), str(system_root)))
        # Exercise the actual Windows platform plugin, not only the offscreen plugin.
        environment.pop("QT_QPA_PLATFORM", None)
    else:
        environment["QT_QPA_PLATFORM"] = "offscreen"
    environment["PYTHONUTF8"] = "1"
    reports = []
    with tempfile.TemporaryDirectory(prefix="struct ai smoke ") as temporary:
        for mode in ("selftest", "gui-selftest"):
            path = output / f"{mode}.json"
            log = output / f"{mode}.log"
            # Stale files cannot satisfy or obscure a failed subsequent execution.
            path.unlink(missing_ok=True)
            log.unlink(missing_ok=True)
            command = [str(executable), f"--{mode}", "--output", str(path)]
            try:
                completed = subprocess.run(
                    command,
                    cwd=temporary,
                    env=environment,
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    timeout=60,
                    check=False,
                )
            except subprocess.TimeoutExpired as error:
                # TimeoutExpired retains raw bytes even when text mode was requested.
                log.write_bytes((error.stdout or b"") + b"\n" + (error.stderr or b""))
                raise RuntimeError(f"Frozen {mode} exceeded 60 seconds; inspect {log}") from error
            log.write_text(completed.stdout + "\n" + completed.stderr, encoding="utf-8")
            if completed.returncode != 0:
                raise RuntimeError(
                    f"Frozen {mode} exited {completed.returncode}; inspect logs in {output}"
                )
            report = json.loads(path.read_text(encoding="utf-8"))
            if report.get("status") != "PASS" or report.get("frozen") is not True:
                raise RuntimeError(f"{mode} did not prove successful frozen execution")
            reports.append(report)
    if reports[0].get("kind") != "M0B_DIAGNOSTIC_SELFTEST":
        raise RuntimeError("Wrong headless selftest type; expected the real diagnostic")
    if reports[1].get("kind") != "M0B_GUI_SELFTEST":
        raise RuntimeError("Wrong GUI selftest type; expected the real window and worker")
    expected_platform = "windows" if os.name == "nt" else "offscreen"
    if reports[1].get("qt_platform") != expected_platform:
        raise RuntimeError(f"Frozen GUI did not exercise the required {expected_platform} plugin")
    if reports[0]["diagnostic"]["result_hash"] != reports[1]["result_hash"]:
        raise RuntimeError("Frozen headless and GUI worker results differ")
    print("Frozen headless and GUI selftests passed from an unrelated working directory.")
    print("This is NOT evidence of running on a clean Windows machine without Python.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
