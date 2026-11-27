import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def run_audit(*arguments):
    return subprocess.run(
        [sys.executable, str(ROOT / "tools/list_unverified.py"), *map(str, arguments)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
        cwd=ROOT,
        timeout=20,
    )


def test_empty_catalogue_is_not_advertised_as_verified():
    completed = run_audit()
    assert completed.returncode == 0
    assert "No engineering code constants implemented" in completed.stdout
    assert "NOT evidence" in completed.stdout


def test_cli_lists_every_unverified_including_null(catalogue_root, write_records, synthetic_record):
    write_records(
        [
            synthetic_record,
            synthetic_record
            | {"key": "missing", "value": None, "verification_note": "TODO_VERIFY"},
        ]
    )
    completed = run_audit("--data-root", catalogue_root)
    assert completed.returncode == 0, completed.stderr
    assert "UNVERIFIED CATALOGUE CONSTANTS: 2" in completed.stdout
    assert "is456_2000.missing" in completed.stdout
    assert "is456_2000.synthetic_scalar" in completed.stdout
    assert "null / TODO_VERIFY" in completed.stdout
    assert "NOT the number used" in completed.stdout


def test_json_inventory_is_reproducible():
    first, second = run_audit("--json"), run_audit("--json")
    assert first.returncode == second.returncode == 0
    assert first.stdout == second.stdout
    assert json.loads(first.stdout)["records"] == []


def test_cli_fails_with_structured_error_for_missing_catalogue(tmp_path):
    completed = run_audit("--data-root", tmp_path)
    assert completed.returncode == 2
    error = json.loads(completed.stderr)
    assert error["type"] == "CodeDataError"
    assert error["clause"]
    assert error["value"]
    assert error["limit"]
