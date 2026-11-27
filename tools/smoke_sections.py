"""Run real source/frozen section commands and refusals, not mocks. Units: field suffixes."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import platform
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

# Allow both direct script execution and import in tests; no engineering imports here.
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.smoke_frozen import file_sha256, isolated_environment  # noqa: E402

SAMPLES = (
    ("rectangular", "beam-flexure"),
    ("doubly_reinforced", "beam-flexure"),
    ("T", "beam-flexure"),
    ("L", "beam-flexure"),
    ("shear", "beam-checks"),
    ("torsion", "beam-checks"),
    ("development_length", "beam-checks"),
    ("cover_spacing", "beam-checks"),
    ("deflection_limits", "beam-checks"),
)


def validate_payload(payload: dict[str, Any], expected_exit: int, report: str) -> None:
    """Check evidence integrity/consistency; no engineering recalculation. Units: unchanged."""
    result = payload["result"]
    canonical = json.dumps(
        result, sort_keys=True, ensure_ascii=False, allow_nan=False, separators=(",", ":")
    )
    expected_hash = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    if payload["result_hash"] != expected_hash or expected_hash not in report:
        raise RuntimeError("Section result/report hash mismatch")
    if result["building_design_available"] or result["verified_code_compliance"]:
        raise RuntimeError("Section command incorrectly claims building/code verification")
    if result["kind"] not in ("DRAFT_BEAM_FLEXURE", "DRAFT_BEAM_COMPONENT_CHECKS"):
        raise RuntimeError("Wrong section result type")
    if not result["checks"]:
        raise RuntimeError("Empty check set cannot pass")
    for check in result["checks"]:
        if check["capacity"] <= 0 or check["demand"] < 0:
            raise RuntimeError("Invalid check demand/capacity")
        if check["ok"] != (check["demand"] <= check["capacity"]):
            raise RuntimeError("Contradictory pass/fail result")
    passed = all(c["ok"] for c in result["checks"])
    if passed != (expected_exit == 0) or (result["status"] == "REVISE_SECTION") == passed:
        raise RuntimeError("Wrong exit/status for actual returned checks")
    count = sum(not r["data"]["verified"] for r in result["code_usage"]["constants"])
    warning = f"UNVERIFIED CODE CONSTANTS USED: {count}"
    if count == 0 or warning not in result["warnings"] or warning not in report:
        raise RuntimeError("Missing actual-use unverified warning")


def run_smoke(
    output: Path, executable: Path | None, source_evidence: Path | None
) -> dict[str, Any]:
    """Run nine samples, failed checks and refusal/overwrite paths. Units: seconds/bytes."""
    output = output.resolve()
    # New directory prevents stale outputs from satisfying a failed test.
    output.mkdir(parents=True, exist_ok=False)
    command_prefix = (
        [str(executable.resolve(strict=True))]
        if executable
        else [sys.executable, "-m", "struct_ai"]
    )
    environment = isolated_environment(os.environ, windows=os.name == "nt")
    cases: list[dict[str, Any]] = []
    with tempfile.TemporaryDirectory(prefix="struct ai section smoke ") as temporary:
        environment["APPDATA"] = str(Path(temporary) / "state")
        environment["XDG_STATE_HOME"] = str(Path(temporary) / "state")

        def execute(
            name: str, mode: str, text: str, exit_code: int, error_type: str | None = None
        ) -> None:
            """Exercise actual CLI/file IO; no dependency substitution. Units: 60 s timeout."""
            folder = output / name
            folder.mkdir()
            source, result, trace, failure = (
                folder / n for n in ("input.json", "result.json", "trace.md", "error.json")
            )
            source.write_text(text, encoding="utf-8")
            command = [
                *command_prefix,
                "--" + mode,
                str(source),
                "--output",
                str(result),
                "--report",
                str(trace),
                "--error-output",
                str(failure),
            ]
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
                (folder / "console.log").write_bytes(
                    (error.stdout or b"") + b"\n" + (error.stderr or b"")
                )
                raise RuntimeError(f"Section command {name} timed out") from error
            (folder / "console.log").write_text(
                completed.stdout + "\n" + completed.stderr, encoding="utf-8"
            )
            if completed.returncode != exit_code:
                for app_log in Path(temporary).rglob("*.log"):
                    print(app_log.read_text(encoding="utf-8", errors="replace")[-8000:])
                raise RuntimeError(
                    f"{name}: expected exit {exit_code}, got {completed.returncode}; "
                    f"{completed.stderr}"
                )
            record: dict[str, Any] = {"name": name, "mode": mode, "exit_code": exit_code}
            if exit_code in (0, 1):
                document = json.loads(result.read_text(encoding="utf-8"))
                validate_payload(document, exit_code, trace.read_text(encoding="utf-8"))
                if failure.exists():
                    raise RuntimeError(f"{name}: successful assessment also emitted failure file")
                record.update(
                    result_hash=document["result_hash"],
                    result_sha256=file_sha256(result),
                    report_sha256=file_sha256(trace),
                    checks=len(document["result"]["checks"]),
                )
                if source_evidence is not None:
                    baseline = json.loads(
                        (source_evidence / name / "result.json").read_text(encoding="utf-8")
                    )
                    if (
                        document != baseline
                        or trace.read_bytes() != (source_evidence / name / "trace.md").read_bytes()
                    ):
                        raise RuntimeError(f"Source/frozen section payload/trace differ: {name}")
            else:
                error = json.loads(failure.read_text(encoding="utf-8"))
                if (
                    result.exists()
                    or trace.exists()
                    or error.get("status") != "FAIL"
                    or error["error"]["type"] != error_type
                ):
                    raise RuntimeError(f"{name}: refusal evidence mismatch")
                record["error_type"] = error_type
            cases.append(record)

        for name, mode in SAMPLES:
            execute(
                "SAMPLE_" + name,
                mode,
                (ROOT / f"examples/SAMPLE_beam_{name}.json").read_text(encoding="utf-8"),
                0,
            )
        failed_flexure = json.loads(
            (ROOT / "examples/SAMPLE_beam_rectangular.json").read_text(encoding="utf-8")
        )
        failed_flexure.update(
            operation="ASSESS",
            reinforcement={"top_mm2": 0.0, "bottom_mm2": 800.0},
            factored_moment_kn_m=200.0,
        )
        del failed_flexure["reinforcement_policy"]
        execute("flexure_revise", "beam-flexure", json.dumps(failed_flexure), 1)
        failed_shear = json.loads(
            (ROOT / "examples/SAMPLE_beam_shear.json").read_text(encoding="utf-8")
        )
        failed_shear["factored_shear_kn"] = 600.0
        execute("shear_revise", "beam-checks", json.dumps(failed_shear), 1)
        missing = json.loads(
            (ROOT / "examples/SAMPLE_beam_cover_spacing.json").read_text(encoding="utf-8")
        )
        missing["request_fire_check"] = True
        execute("missing_fire_data", "beam-checks", json.dumps(missing), 2, "MissingCodeValue")
        execute(
            "duplicate_json",
            "beam-checks",
            '{"operation":"COVER_SPACING","operation":"SHEAR_TORSION"}',
            2,
            "InputOutOfRange",
        )
        invalid = copy.deepcopy(failed_shear)
        invalid["stirrups"]["spacing_mm"] = "100"
        execute("strict_type_refusal", "beam-checks", json.dumps(invalid), 2, "InputOutOfRange")
        old = output / "SAMPLE_rectangular"
        protected = {
            name: (old / name).read_bytes() for name in ("input.json", "result.json", "trace.md")
        }
        repeated = subprocess.run(
            [
                *command_prefix,
                "--beam-flexure",
                str(old / "input.json"),
                "--output",
                str(old / "result.json"),
                "--report",
                str(old / "trace.md"),
            ],
            cwd=temporary,
            env=environment,
            capture_output=True,
            text=True,
            timeout=60,
            check=False,
        )
        if repeated.returncode != 2 or any(
            (old / name).read_bytes() != data for name, data in protected.items()
        ):
            raise RuntimeError("Existing inputs/evidence were overwritten or not refused")
        cases.append(
            {"name": "overwrite_refusal", "exit_code": 2, "protected_files": tuple(protected)}
        )
    summary = {
        "kind": "DRAFT_SECTION_COMMAND_SMOKE",
        "status": "PASS",
        "platform": platform.platform(),
        "mode": "FROZEN_EXECUTABLE" if executable else "SOURCE_PYTHON",
        "executable_sha256": file_sha256(executable) if executable else None,
        "source_payloads_and_reports_compared": source_evidence is not None,
        "case_count": len(cases),
        "cases": cases,
        "building_design_available": False,
        "verified_code_compliance": False,
        "clean_windows_no_python_accepted": False,
    }
    (output / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, sort_keys=True))
    return summary


def main() -> int:
    """Run explicit smoke; the app never auto-runs samples. Units: field suffixes."""
    parser = argparse.ArgumentParser(
        description="Actual draft section CLI smoke; not a building test"
    )
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--executable", type=Path)
    parser.add_argument("--source-evidence", type=Path)
    args = parser.parse_args()
    if args.source_evidence is not None and args.executable is None:
        parser.error("--source-evidence is for a frozen comparison")
    run_smoke(args.output, args.executable, args.source_evidence)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
