import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from struct_ai.exceptions import CodeDataError, InputOutOfRange, MissingCodeValue, ScopeRefusal
from struct_ai.services import engine_service as service
from tests.component_reference import (
    cover_request,
    deflection_request,
    development_request,
    shear_request,
    torsion_request,
)

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def m2_data(tmp_path):
    root = tmp_path / "codes"
    shutil.copytree(
        ROOT / "struct_ai/codes", root, ignore=shutil.ignore_patterns("*.py", "__pycache__")
    )
    return root


def change_record(root, key, value=None, **changes):
    path = root / "is456_2000/data/beam_checks_draft.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    record = next(r for r in data["constants"] if r["key"] == "beam_checks." + key)
    record.update(value=value, **changes)
    if value is None:
        record["verification_note"] = "TODO_VERIFY: deliberately missing test fixture"
    path.write_text(json.dumps(data), encoding="utf-8")


@pytest.mark.parametrize(
    "factory,key",
    [
        (shear_request, "shear.table19.p04.m25"),
        (shear_request, "shear.table20.m25"),
        (shear_request, "shear.maximum_credited_fy"),
        (shear_request, "steel.design_stress_factor"),
        (shear_request, "shear.minimum_stress"),
        (shear_request, "shear.maximum_spacing"),
        (torsion_request, "torsion.equivalent_shear_factor"),
        (torsion_request, "torsion.equivalent_moment_divisor"),
        (torsion_request, "torsion.transverse_shear_divisor"),
        (torsion_request, "torsion.spacing_sum_divisor"),
        (torsion_request, "side_face.total_web_ratio"),
        (development_request, "bond.plain_tension.m25"),
        (development_request, "bond.deformed_multiplier"),
        (cover_request, "cover.moderate"),
        (cover_request, "spacing.horizontal_aggregate_addition"),
        (cover_request, "spacing.vertical_minimum"),
        (deflection_request, "deflection.final_span_divisor"),
        (deflection_request, "deflection.post_finish_span_divisor"),
        (deflection_request, "deflection.post_finish_absolute_limit"),
    ],
)
def test_missing_consumed_m2_value_refuses_without_fallback(m2_data, factory, key):
    change_record(m2_data, key)
    with pytest.raises(MissingCodeValue) as caught:
        service.assess_beam_checks(factory(), data_root=m2_data)
    assert caught.value.clause and caught.value.limit


@pytest.mark.parametrize(
    "key,value,units",
    [
        ("shear.table19.p04.m25", 0.64, "kN/m²"),
        ("shear.table19.p04.percent", 1.0, "1"),
        ("shear.maximum_spacing", 300.0, "m"),
    ],
)
def test_m2_units_are_rejected_before_use(m2_data, key, value, units):
    change_record(m2_data, key, value, units=units)
    with pytest.raises(CodeDataError, match="units"):
        service.assess_beam_checks(shear_request(), data_root=m2_data)


@pytest.mark.parametrize(
    "key,value",
    [
        ("shear.table19.p04.percent", 0.5),
        ("shear.table19.p04.m25", 0.2),
        ("shear.table20.m25", 0.1),
        ("shear.minimum_stress", 0.0),
    ],
)
def test_invalid_table_or_physical_coefficient_is_not_adjusted_to_pass(m2_data, key, value):
    change_record(m2_data, key, value)
    with pytest.raises(CodeDataError):
        service.assess_beam_checks(shear_request(), data_root=m2_data)


def test_other_grade_missing_values_do_not_block_unrelated_grade_or_usage(m2_data):
    change_record(m2_data, "shear.table19.p04.m40")
    run = service.assess_beam_checks(shear_request(), data_root=m2_data)
    assert not any(r.identifier.endswith(".m40") for r in run.result.code_usage.constants)


@pytest.mark.parametrize(
    "payload",
    [
        cover_request() | {"request_fire_check": True},
        cover_request() | {"request_maximum_crack_spacing_check": True},
        deflection_request() | {"method": "SPAN_DEPTH_CHARTS"},
    ],
)
def test_missing_unimplemented_code_routes_fail_closed(payload):
    with pytest.raises(MissingCodeValue):
        service.assess_beam_checks(payload)


def test_filling_one_scalar_cannot_enable_fire_workflow(m2_data):
    change_record(m2_data, "cover.fire_table16a", 20.0)
    with pytest.raises(NotImplementedError):
        service.assess_beam_checks(
            cover_request() | {"request_fire_check": True}, data_root=m2_data
        )


@pytest.mark.parametrize(
    "factory", [shear_request, development_request, cover_request, deflection_request]
)
def test_current_amended_code_requests_remain_blocked(factory):
    request = factory() | {"source_basis": "CURRENT_AMENDED_CODE"}
    if request["operation"] == "SHEAR_TORSION":
        request["flexure"]["source_basis"] = "CURRENT_AMENDED_CODE"
    with pytest.raises(MissingCodeValue, match="amendment"):
        service.assess_beam_checks(request)


@pytest.mark.parametrize(
    "change",
    [
        {"acknowledge_unverified": False},
        {"design_bar_stress_n_mm2": "300"},
        {"bar_diameter_mm": True},
        {"available_straight_length_mm": 0.0},
        {"extra": 1},
        {"equal_diameter_bundle_count": 2.0},
    ],
)
def test_strict_inputs_no_coercion_or_implicit_defaults(change):
    with pytest.raises(InputOutOfRange):
        service.assess_beam_checks(development_request() | change)


def test_constructed_model_is_revalidated_and_null_input_is_refused():
    model = service.validate_beam_checks(development_request())
    with pytest.raises(InputOutOfRange):
        service.assess_beam_checks(model.model_copy(update={"bar_diameter_mm": "bad"}))
    for invalid in (None, [], {}, {"operation": []}):
        with pytest.raises(InputOutOfRange):
            service.assess_beam_checks(invalid)


@pytest.mark.parametrize(
    "text",
    [
        '{"operation":"COVER_SPACING","operation":"DEFLECTION_LIMITS"}',
        '{"operation":"DEVELOPMENT_LENGTH","bar_diameter_mm":NaN}',
        "[]",
        '"abc"',
        "[" * 2000 + "0" + "]" * 2000,
        "é" * 500001,
    ],
    # pytest exports node IDs in PYTEST_CURRENT_TEST; Windows env values have a size cap.
    # Keep the same oversized/deep test INPUTS, but give cases bounded diagnostic names.
    ids=["duplicate", "nonfinite", "array", "string", "deep", "oversize-utf8"],
)
def test_json_transport_is_bounded_finite_and_unambiguous(text):
    with pytest.raises(InputOutOfRange):
        service.run_beam_checks_json(text)


def test_unsupported_concrete_grade_axial_and_zero_bending_are_not_guessed():
    request = shear_request()
    request["flexure"]["materials"]["fck_n_mm2"] = 27.0
    with pytest.raises(InputOutOfRange, match="discrete"):
        service.assess_beam_checks(request)
    request = shear_request()
    request["flexure"]["axial_force_kn"] = 1.0
    with pytest.raises(ScopeRefusal, match="Axial"):
        service.assess_beam_checks(request)
    request = torsion_request()
    request["flexure"]["factored_moment_kn_m"] = 0.0
    with pytest.raises(InputOutOfRange):
        service.assess_beam_checks(request)


def test_report_preserves_failed_checks_trace_and_hash_not_recalculated():
    request = torsion_request()
    request["stirrups"]["spacing_mm"] = 500.0
    run = service.assess_beam_checks(request)
    report = service.beam_checks_report(run)
    assert "REVISE_SECTION" in report and "FAIL" in report
    assert run.result_hash in report and run.result.code_usage.warning in report
    assert all(c.name in report for c in run.result.checks)
    assert all(r.identifier in report for r in run.result.code_usage.constants)
    with pytest.raises(InputOutOfRange, match="integrity"):
        service.beam_checks_report(run.model_copy(update={"result_hash": "0" * 64}))


@pytest.mark.parametrize(
    "factory",
    [shear_request, torsion_request, development_request, cover_request, deflection_request],
)
def test_real_source_entrypoint_writes_json_trace_and_no_false_failure(factory, tmp_path):
    source, output, trace, failure = (
        tmp_path / p for p in ("input.json", "result.json", "trace.md", "failure.json")
    )
    request = factory()
    source.write_text(json.dumps(request), encoding="utf-8")
    expected = service.assess_beam_checks(request)
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "struct_ai",
            "--beam-checks",
            str(source),
            "--output",
            str(output),
            "--report",
            str(trace),
            "--error-output",
            str(failure),
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=20,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert json.loads(output.read_text())["result_hash"] == expected.result_hash
    assert expected.result_hash in trace.read_text(encoding="utf-8")
    assert not failure.exists()


def test_real_cli_failure_and_overwrite_protection(tmp_path):
    source, output, failure = (tmp_path / p for p in ("input.json", "result.json", "failure.json"))
    source.write_text(json.dumps(cover_request() | {"request_fire_check": True}))
    command = [
        sys.executable,
        "-m",
        "struct_ai.cli.beam_checks",
        str(source),
        "--output",
        str(output),
        "--error-output",
        str(failure),
    ]
    result = subprocess.run(command, capture_output=True, text=True, timeout=20, check=False)
    assert result.returncode == 2
    assert json.loads(failure.read_text())["error"]["type"] == "MissingCodeValue"
    assert not output.exists()
    original = failure.read_bytes()
    result = subprocess.run(command, capture_output=True, text=True, timeout=20, check=False)
    assert result.returncode == 2 and failure.read_bytes() == original


def test_fresh_component_process_no_qt_solver_llm_import_and_deterministic_hash():
    script = """
import sys
from struct_ai.services import engine_service
run = engine_service.run_beam_checks_json(sys.argv[1])
heavy = ('PySide6', 'openseespy', 'ollama', 'numpy', 'torch')
assert not any(n.startswith(heavy) for n in sys.modules)
print(run.result_hash)
"""
    request = torsion_request()
    expected = service.assess_beam_checks(request).result_hash
    for _ in range(2):
        result = subprocess.run(
            [sys.executable, "-c", script, json.dumps(request)],
            capture_output=True,
            text=True,
            env=os.environ.copy(),
            timeout=20,
            check=False,
        )
        assert result.returncode == 0, result.stderr
        assert result.stdout.strip() == expected
