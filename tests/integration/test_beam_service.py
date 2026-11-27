import copy
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from struct_ai.codes.registry import CodeRegistry
from struct_ai.exceptions import CodeDataError, InputOutOfRange, MissingCodeValue, ScopeRefusal
from struct_ai.services import engine_service as service
from tests.beam_reference import assessment, beam_request, flange_input

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "struct_ai" / "codes"


@pytest.fixture
def draft_data_root(tmp_path):
    root = tmp_path / "codes"
    shutil.copytree(DATA, root, ignore=shutil.ignore_patterns("__pycache__", "*.py"))
    return root


def alter_value(root, key, *, value=None, **changes):
    path = root / "is456_2000/data/flexure_draft.json"
    document = json.loads(path.read_text(encoding="utf-8"))
    for record in document["constants"]:
        if record["key"] == key:
            record.update(value=value, **changes)
            if value is None:
                record["verification_note"] = (
                    "TODO_VERIFY: deliberately missing in this failure test"
                )
            break
    else:
        raise AssertionError(f"Test requested an unknown key: {key}")
    path.write_text(json.dumps(document, ensure_ascii=False), encoding="utf-8")


def test_current_amended_code_is_missing_and_cannot_be_selected():
    with pytest.raises(MissingCodeValue, match="amendment") as caught:
        service.design_beam_flexure(beam_request() | {"source_basis": "CURRENT_AMENDED_CODE"})
    assert caught.value.value is None and caught.value.clause and caught.value.limit


def test_editing_an_amendment_scalar_cannot_enable_code_compliance(draft_data_root):
    alter_value(draft_data_root, "applicability.current_amendment_review", value=1.0)
    with pytest.raises(NotImplementedError, match="compliance is not implemented"):
        service.design_beam_flexure(
            beam_request() | {"source_basis": "CURRENT_AMENDED_CODE"}, data_root=draft_data_root
        )


@pytest.mark.parametrize(
    "key",
    [
        "flexure.concrete.ultimate_strain",
        "flexure.concrete.plateau_strain",
        "flexure.concrete.peak_stress_factor",
        "flexure.steel.partial_factor",
        "flexure.steel.elastic_modulus",
        "flexure.steel.fe415.yield_strength",
        "flexure.steel.minimum_plastic_tension_strain",
        "flexure.reinforcement.minimum_tension_factor",
        "flexure.reinforcement.maximum_tension_ratio",
        "flexure.reinforcement.maximum_compression_ratio",
        "flexure.annex_g.resultant_factor",
        "flexure.annex_g.centroid_factor",
    ],
)
def test_every_required_rectangular_primitive_fails_closed_when_missing(draft_data_root, key):
    alter_value(draft_data_root, key)
    with pytest.raises(MissingCodeValue):
        service.design_beam_flexure(beam_request(), data_root=draft_data_root)


def test_code_units_are_checked_before_capture(draft_data_root):
    alter_value(draft_data_root, "flexure.steel.elastic_modulus", value=200000.0, units="kN/m²")
    with pytest.raises(CodeDataError, match="incompatible units") as caught:
        service.design_beam_flexure(beam_request(), data_root=draft_data_root)
    assert caught.value.value == "kN/m²" and caught.value.limit == "N/mm²"
    registry = CodeRegistry.load(draft_data_root)
    tracker = registry.new_tracker()
    with pytest.raises(CodeDataError):
        registry.require(
            "is456_2000.flexure.steel.elastic_modulus", tracker, expected_units="N/mm²"
        )
    assert tracker.snapshot().constants == ()


def test_missing_curve_only_blocks_paths_that_need_opposite_steel(draft_data_root):
    alter_value(draft_data_root, "flexure.steel.curve.p4.plastic_strain")
    result = service.design_beam_flexure(beam_request(), data_root=draft_data_root).result
    assert not any(".curve." in record.identifier for record in result.code_usage.constants)
    with pytest.raises(MissingCodeValue):
        service.design_beam_flexure(
            beam_request()
            | {
                "factored_moment_kn_m": 350.0,
                "reinforcement_policy": "ALLOW_COMPRESSION_STEEL",
            },
            data_root=draft_data_root,
        )


def test_missing_flange_value_does_not_block_rectangles_or_flange_in_tension(draft_data_root):
    alter_value(draft_data_root, "flexure.flange.t_span_divisor")
    service.design_beam_flexure(beam_request(), data_root=draft_data_root)
    request = beam_request()
    request["geometry"]["flange"] = flange_input()
    with pytest.raises(MissingCodeValue):
        service.design_beam_flexure(request, data_root=draft_data_root)
    negative = service.design_beam_flexure(
        request | {"factored_moment_kn_m": -120.0}, data_root=draft_data_root
    ).result
    assert negative.section.compression_case == "FLANGE_IN_TENSION_IGNORED"


def test_malformed_curve_is_not_interpolated(draft_data_root):
    alter_value(draft_data_root, "flexure.steel.curve.p4.stress_ratio", value=0.50)
    with pytest.raises(CodeDataError, match="ordered"):
        service.assess_beam_flexure(
            assessment(beam_request(), top=200.0, bottom=1000.0), data_root=draft_data_root
        )


def test_missing_catalogue_directory_has_no_packaged_data_fallback(tmp_path):
    with pytest.raises(CodeDataError, match="missing"):
        service.design_beam_flexure(beam_request(), data_root=tmp_path)


def test_stale_model_construct_does_not_bypass_service_input_validation():
    request = service.validate_beam_flexure_design(beam_request())
    bypassed = request.model_copy(update={"factored_moment_kn_m": "123", "axial_force_kn": 0.0})
    with pytest.raises(InputOutOfRange):
        service.design_beam_flexure(bypassed)
    with pytest.raises(InputOutOfRange):
        service.design_beam_flexure(None)


def test_report_does_not_recalculate_or_hide_warnings_and_failed_checks():
    run = service.design_beam_flexure(beam_request())
    report = service.beam_flexure_report(run)
    assert run.result.code_usage.warning in report
    assert run.result_hash in report
    assert run.result.code_usage.data_digest in report
    assert "NOT code-compliance approval" in report
    assert "Overall D" in report and "NOT selected bars" in report
    assert all(c.name in report for c in run.result.checks)
    assert all(r.identifier in report for r in run.result.code_usage.constants)
    changed = run.model_copy(update={"result_hash": "0" * 64})
    with pytest.raises(InputOutOfRange, match="integrity"):
        service.beam_flexure_report(changed)


def test_current_model_parameters_not_report_literals(draft_data_root):
    # Deliberately altered unverified test data tests provenance, NOT a new design basis.
    alter_value(draft_data_root, "flexure.concrete.peak_stress_factor", value=0.440)
    run = service.design_beam_flexure(beam_request(), data_root=draft_data_root)
    assert run.result.parameters.concrete_peak_factor == 0.440
    report = service.beam_flexure_report(run)
    assert "0.44 fck" in report
    assert run.result_hash != service.design_beam_flexure(beam_request()).result_hash


def test_oversize_or_deep_json_fails_with_typed_input_error():
    with pytest.raises(InputOutOfRange):
        service.run_beam_flexure_json("[" * 2000 + "0" + "]" * 2000)
    with pytest.raises(InputOutOfRange):
        service.run_beam_flexure_json("é" * 500_001)


def test_no_capacity_when_opposite_layer_prevents_positive_ductile_equilibrium():
    request = beam_request()
    request["geometry"]["top_centroid_from_top_mm"] = 400.0
    with pytest.raises(InputOutOfRange, match="cannot balance"):
        service.assess_beam_flexure(assessment(request, top=5000.0, bottom=1000.0))


def test_no_compression_steel_sizing_when_layer_is_outside_compression_zone():
    request = beam_request() | {
        "factored_moment_kn_m": 350.0,
        "reinforcement_policy": "ALLOW_COMPRESSION_STEEL",
    }
    request["geometry"]["top_centroid_from_top_mm"] = 300.0
    with pytest.raises(InputOutOfRange, match="cannot act as compression steel"):
        service.design_beam_flexure(request)


def test_deep_opposite_flange_is_not_silently_treated_as_ordinary_tension_slab():
    request = beam_request() | {"factored_moment_kn_m": -120.0}
    request["geometry"]["flange"] = flange_input() | {"thickness_mm": 400.0}
    with pytest.raises(ScopeRefusal, match="deep opposite-face flange"):
        service.design_beam_flexure(request)


def test_exact_coupling_threshold_passes_without_tolerance():
    request = beam_request()
    request["geometry"]["flange"] = flange_input() | {"transverse_steel_mm2_per_m": 480.0}
    result = service.design_beam_flexure(request).result
    check = next(c for c in result.checks if c.name == "Flange transverse reinforcement")
    assert check.ratio == 1 and check.ok
    request["geometry"]["flange"]["transverse_steel_mm2_per_m"] = 479.9999999
    with pytest.raises(InputOutOfRange):
        service.design_beam_flexure(request)


@pytest.mark.parametrize(
    "name",
    [
        "SAMPLE_beam_rectangular.json",
        "SAMPLE_beam_doubly_reinforced.json",
        "SAMPLE_beam_T.json",
        "SAMPLE_beam_L.json",
    ],
)
def test_actual_cli_samples_create_traceable_json_and_markdown(name, tmp_path):
    output, report = tmp_path / "result.json", tmp_path / "trace.md"
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "struct_ai.cli.beam_flexure",
            str(ROOT / "examples" / name),
            "--output",
            str(output),
            "--report",
            str(report),
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
        timeout=20,
    )
    assert completed.returncode == 0, completed.stderr
    document = json.loads(output.read_text(encoding="utf-8"))
    assert document["result"]["status"] == "DRAFT_SECTION_CHECKS_PASS"
    assert "SAMPLE" in document["result"]["inputs"]["calculation_label"]
    assert "UNVERIFIED CODE CONSTANTS USED:" in completed.stderr
    assert document["result_hash"] in report.read_text(encoding="utf-8")


def test_cli_refuses_to_overwrite_inputs_or_old_evidence(tmp_path):
    path = tmp_path / "input.json"
    original = json.dumps(beam_request())
    path.write_text(original)
    completed = subprocess.run(
        [sys.executable, "-m", "struct_ai.cli.beam_flexure", str(path), "--output", str(path)],
        capture_output=True,
        text=True,
        check=False,
        timeout=20,
    )
    assert completed.returncode == 2
    assert path.read_text() == original
    destination = tmp_path / "old-result.json"
    destination.write_text("old evidence")
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "struct_ai.cli.beam_flexure",
            str(path),
            "--output",
            str(destination),
        ],
        capture_output=True,
        text=True,
        check=False,
        timeout=20,
    )
    assert completed.returncode == 2
    assert destination.read_text() == "old evidence"


def test_cli_failed_check_returns_nonzero_and_preserves_failed_result(tmp_path):
    path = tmp_path / "input.json"
    request = assessment(beam_request() | {"factored_moment_kn_m": 200.0}, top=0.0, bottom=800.0)
    path.write_text(json.dumps(request))
    completed = subprocess.run(
        [sys.executable, "-m", "struct_ai.cli.beam_flexure", str(path)],
        capture_output=True,
        text=True,
        check=False,
        timeout=20,
    )
    assert completed.returncode == 1
    assert json.loads(completed.stdout)["result"]["status"] == "REVISE_SECTION"


def test_cli_missing_value_is_structured_error_and_writes_no_result(tmp_path):
    path, output = tmp_path / "input.json", tmp_path / "result.json"
    path.write_text(json.dumps(beam_request() | {"source_basis": "CURRENT_AMENDED_CODE"}))
    completed = subprocess.run(
        [sys.executable, "-m", "struct_ai.cli.beam_flexure", str(path), "--output", str(output)],
        capture_output=True,
        text=True,
        check=False,
        timeout=20,
    )
    assert completed.returncode == 2
    assert json.loads(completed.stderr)["type"] == "MissingCodeValue"
    assert not output.exists()


def test_section_run_does_not_import_qt_opensees_or_llm_even_when_called_in_a_fresh_process():
    script = """
import json, sys
from struct_ai.services import engine_service
request=json.loads(sys.argv[1])
run=engine_service.design_beam_flexure(request)
heavy=('openseespy', 'PySide6', 'ollama', 'torch', 'numpy')
assert not any(n.startswith(heavy) for n in sys.modules)
assert run.result.verified_code_compliance is False
print(run.result_hash)
"""
    request = beam_request()
    expected = service.design_beam_flexure(request).result_hash
    for _ in range(2):
        completed = subprocess.run(
            [sys.executable, "-c", script, json.dumps(request)],
            env=os.environ.copy(),
            capture_output=True,
            text=True,
            check=False,
            timeout=20,
        )
        assert completed.returncode == 0, completed.stderr
        assert completed.stdout.strip() == expected
    assert request == copy.deepcopy(request)
