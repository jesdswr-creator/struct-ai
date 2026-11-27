import json
import subprocess
import sys
from pathlib import Path

import pytest

from struct_ai.services import engine_service


def test_service_selftest_repeats_real_solver_and_loads_resources():
    report = engine_service.run_packaging_selftest()
    assert report.kind == "M0B_DIAGNOSTIC_SELFTEST"
    assert report.status == "PASS"
    assert report.deterministic_repeat
    assert not report.frozen
    assert len(report.resources) == 10
    assert len(report.diagnostic.result.checks) == 5
    assert "BuildingInput" in report.not_tested[0]


def test_cli_selftest_writes_actual_evidence(tmp_path):
    output = tmp_path / "headless evidence.json"
    completed = subprocess.run(
        [sys.executable, "-m", "struct_ai", "--selftest", "--output", str(output)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
        timeout=30,
    )
    assert completed.returncode == 0, completed.stderr
    report = json.loads(output.read_text(encoding="utf-8"))
    assert report["status"] == "PASS"
    assert report["frozen"] is False
    # Same independently integrated 0.0054 m expectation as the solver tests.
    actual = report["diagnostic"]["result"]["observations"]["tip_displacement_m"]
    assert actual == pytest.approx(0.0054, rel=1e-12)


def test_cli_gui_selftest_uses_actual_spawned_worker(tmp_path):
    output = tmp_path / "GUI evidence.json"
    completed = subprocess.run(
        [sys.executable, "-m", "struct_ai", "--gui-selftest", "--output", str(output)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
        timeout=40,
    )
    assert completed.returncode == 0, completed.stderr
    report = json.loads(output.read_text(encoding="utf-8"))
    assert report["status"] == "PASS"
    assert report["frozen"] is False
    assert report["table_rows"] == 5
    assert all(check["ok"] for check in report["checks"])
    assert report["building_design_available"] is False


def test_source_tree_does_not_contain_fake_windows_executable():
    root = Path(__file__).resolve().parents[2]
    assert not list((root / "packaging").glob("*.exe"))
