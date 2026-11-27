"""Exercise a real onedir executable outside the source tree. Units: seconds, evidence JSON."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import shutil
import subprocess
import tempfile
from collections.abc import Mapping
from pathlib import Path, PureWindowsPath
from typing import Any


def file_sha256(path: Path) -> str:
    """Hash actual file bytes without loading a whole native library into memory. Units: none."""
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def bundle_inventory(root: Path) -> list[dict[str, Any]]:
    """Inventory runtime files and internal symlinks, refusing external links. Units: bytes."""
    root = root.resolve(strict=True)
    entries = []
    for path in sorted(root.rglob("*")):
        name = path.relative_to(root).as_posix()
        if path.is_symlink():
            if not path.resolve(strict=True).is_relative_to(root):
                raise RuntimeError(f"Bundle symlink escapes the runtime directory: {name}")
            entries.append({"path": name, "symlink": os.readlink(path)})
        elif path.is_file():
            entries.append(
                {"path": name, "bytes": path.stat().st_size, "sha256": file_sha256(path)}
            )
    return entries


def isolated_environment(inherited: Mapping[str, str], *, windows: bool) -> dict[str, str]:
    """Remove developer paths and use Windows case-insensitive key semantics. Units: none."""
    environment = (
        {key.upper(): value for key, value in inherited.items()} if windows else dict(inherited)
    )
    for name in (
        "PYTHONPATH",
        "PYTHONHOME",
        "PYTHONEXECUTABLE",
        "PYTHONUSERBASE",
        "VIRTUAL_ENV",
        "CONDA_PREFIX",
        "LD_LIBRARY_PATH",
        "LD_PRELOAD",
        "QT_PLUGIN_PATH",
        "QT_QPA_PLATFORM_PLUGIN_PATH",
    ):
        environment.pop(name, None)
    if windows:
        root = PureWindowsPath(environment.get("SYSTEMROOT", ""))
        if not root.is_absolute():
            raise RuntimeError("Windows SYSTEMROOT must be present and absolute; no fallback used")
        environment["PATH"] = ";".join((str(root / "System32"), str(root)))
        # Exercise the actual Windows platform plugin, not only the offscreen plugin.
        environment.pop("QT_QPA_PLATFORM", None)
    else:
        environment["QT_QPA_PLATFORM"] = "offscreen"
    environment["PYTHONUTF8"] = "1"
    return environment


def main() -> int:
    """Test solver and GUI with external Python/library paths removed. Units: 60 s per command."""
    parser = argparse.ArgumentParser(description="Smoke test a real M0b frozen executable")
    parser.add_argument("executable", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--source-report", type=Path)
    args = parser.parse_args()
    executable = args.executable.resolve(strict=True)
    output = args.output.resolve()
    if output.is_relative_to(executable.parent):
        parser.error("--output must be outside the runtime bundle being inventoried")
    output.mkdir(parents=True, exist_ok=True)
    for name in ("summary.json", "bundle-manifest.json"):
        (output / name).unlink(missing_ok=True)
    environment = isolated_environment(os.environ, windows=os.name == "nt")
    reports = []
    with tempfile.TemporaryDirectory(prefix="struct ai smoke ") as temporary:
        for mode in ("selftest", "gui-selftest"):
            path = output / f"{mode}.json"
            log = output / f"{mode}.log"
            # Isolate application logs and preferences from the build host's user profile.
            state_root = Path(temporary) / mode
            environment["APPDATA"] = str(state_root)
            environment["XDG_STATE_HOME"] = str(state_root)
            # Stale files cannot satisfy or obscure a failed subsequent execution.
            path.unlink(missing_ok=True)
            log.unlink(missing_ok=True)
            for previous in output.glob(f"{mode}-app-*.log"):
                previous.unlink()
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
            finally:
                # Windowed executables have no console: preserve their actual native/app
                # logs, including failed startup traces, before deleting the temp profile.
                for app_log in sorted(state_root.rglob("*.log")):
                    saved = output / f"{mode}-app-{app_log.name}"
                    shutil.copyfile(app_log, saved)
                    text = saved.read_text(encoding="utf-8", errors="replace")
                    print(f"Application log {saved}:\n{text[-12000:]}")
            log.write_text(completed.stdout + "\n" + completed.stderr, encoding="utf-8")
            if completed.returncode != 0:
                print(log.read_text(encoding="utf-8")[-12000:])
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
    result_hash = reports[0]["diagnostic"]["result_hash"]
    if result_hash != reports[1]["result_hash"]:
        raise RuntimeError("Frozen headless and GUI worker results differ")
    checks = reports[0]["diagnostic"]["result"]["checks"]
    if reports[1].get("checks") != checks or reports[1].get("table_rows") != len(checks):
        raise RuntimeError("Frozen GUI checks/table rows do not match the headless result")
    if args.source_report is not None:
        source = json.loads(args.source_report.read_text(encoding="utf-8"))
        if (
            source.get("kind") != "M0B_DIAGNOSTIC_SELFTEST"
            or source.get("status") != "PASS"
            or source.get("frozen") is not False
            or source.get("platform") != reports[0]["platform"]
            or source["diagnostic"]["result_hash"] != result_hash
        ):
            raise RuntimeError("Source and frozen results do not match on this build host")
    inventory = bundle_inventory(executable.parent)
    manifest = output / "bundle-manifest.json"
    manifest.write_text(json.dumps(inventory, indent=2) + "\n", encoding="utf-8")
    summary = {
        "kind": "M0B_FROZEN_SMOKE",
        "status": "PASS",
        "platform": platform.platform(),
        "python_version": reports[0]["python_version"],
        "qt_platform": reports[1]["qt_platform"],
        "result_hash": result_hash,
        "checks": len(checks),
        "resources": len(reports[0]["resources"]),
        "source_result_compared": args.source_report is not None,
        "executable_sha256": file_sha256(executable),
        "bundle_manifest_sha256": file_sha256(manifest),
        "bundle_regular_files": sum("sha256" in entry for entry in inventory),
        "bundle_symlinks": sum("symlink" in entry for entry in inventory),
        "bundle_regular_file_bytes": sum(entry.get("bytes", 0) for entry in inventory),
        "report_sha256": {
            name: file_sha256(output / f"{name}.json") for name in ("selftest", "gui-selftest")
        },
        "clean_windows_no_python_accepted": False,
    }
    (output / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print("Frozen headless and GUI selftests passed from an unrelated working directory.")
    print("This is NOT evidence of running on a clean Windows machine without Python.")
    print(json.dumps(summary, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
