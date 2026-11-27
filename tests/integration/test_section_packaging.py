import json

import pytest

from struct_ai.cli import beam_checks
from struct_ai.serialization import content_hash
from struct_ai.services import engine_service
from tests.component_reference import cover_request, development_request
from tools.package_manifest import write_manifest
from tools.smoke_sections import run_smoke, validate_payload


def test_real_source_smoke_exercises_all_15_paths_from_unrelated_working_directory(tmp_path):
    summary = run_smoke(tmp_path / "source", None, None)
    assert summary["status"] == "PASS" and summary["case_count"] == 15
    assert summary["mode"] == "SOURCE_PYTHON"
    assert not summary["clean_windows_no_python_accepted"]
    assert [c["exit_code"] for c in summary["cases"]].count(0) == 9
    assert [c["exit_code"] for c in summary["cases"]].count(1) == 2
    assert [c["exit_code"] for c in summary["cases"]].count(2) == 4
    with pytest.raises(FileExistsError):
        run_smoke(tmp_path / "source", None, None)


@pytest.mark.parametrize("defect", ["hash", "warning", "false_ok", "empty_checks"])
def test_smoke_verifier_does_not_accept_tampered_result(defect):
    run = engine_service.assess_beam_checks(development_request())
    payload = json.loads(run.model_dump_json())
    report = engine_service.beam_checks_report(run)
    if defect == "hash":
        payload["result_hash"] = "0" * 64
    if defect == "warning":
        payload["result"]["warnings"] = []
    if defect == "false_ok":
        payload["result"]["checks"][0]["ok"] = False
    if defect == "empty_checks":
        payload["result"]["checks"] = []
    if defect != "hash":
        new_hash = content_hash(payload["result"])
        report = report.replace(payload["result_hash"], new_hash)
        payload["result_hash"] = new_hash
    with pytest.raises(RuntimeError):
        validate_payload(payload, 0, report)


def test_windowed_no_console_saves_failure_json_without_fabricated_result(tmp_path, monkeypatch):
    source, failure, output = (tmp_path / n for n in ("input.json", "failure.json", "result.json"))
    source.write_text(json.dumps(cover_request() | {"request_fire_check": True}))
    monkeypatch.setattr("sys.stdout", None)
    monkeypatch.setattr("sys.stderr", None)
    assert (
        beam_checks.main([str(source), "--output", str(output), "--error-output", str(failure)])
        == 2
    )
    assert not output.exists()
    assert json.loads(failure.read_text())["error"]["type"] == "MissingCodeValue"


def test_windowed_no_console_requires_explicit_result_path(tmp_path, monkeypatch):
    source, failure = tmp_path / "input.json", tmp_path / "failure.json"
    source.write_text(json.dumps(development_request()))
    monkeypatch.setattr("sys.stdout", None)
    monkeypatch.setattr("sys.stderr", None)
    assert beam_checks.main([str(source), "--error-output", str(failure)]) == 2
    assert json.loads(failure.read_text())["error"]["type"] == "FileContractError"


def test_windowed_real_calculation_retains_warnings_in_saved_result_and_report(
    tmp_path, monkeypatch
):
    source, output, trace = (tmp_path / n for n in ("input.json", "result.json", "trace.md"))
    source.write_text(json.dumps(development_request()))
    monkeypatch.setattr("sys.stdout", None)
    monkeypatch.setattr("sys.stderr", None)
    assert beam_checks.main([str(source), "--output", str(output), "--report", str(trace)]) == 0
    payload = json.loads(output.read_text())
    assert payload["result"]["warnings"][0] in trace.read_text(encoding="utf-8")


def test_final_bundle_manifest_includes_evidence_and_refuses_overwrite(tmp_path):
    (tmp_path / "README.md").write_text("DRAFT")
    (tmp_path / "ci-evidence").mkdir()
    (tmp_path / "ci-evidence/summary.json").write_text('{"status":"PASS"}')
    manifest = write_manifest(tmp_path, "f" * 40)
    assert {r["path"] for r in manifest["files"]} == {"README.md", "ci-evidence/summary.json"}
    assert not manifest["building_design_available"] and not manifest["verified_code_compliance"]
    assert not manifest["digitally_signed"] and not manifest["installer"]
    before = (tmp_path / "DRAFT-BUNDLE-MANIFEST.json").read_bytes()
    with pytest.raises(FileExistsError):
        write_manifest(tmp_path, "f" * 40)
    assert (tmp_path / "DRAFT-BUNDLE-MANIFEST.json").read_bytes() == before
    with pytest.raises(ValueError):
        write_manifest(tmp_path, "latest")
