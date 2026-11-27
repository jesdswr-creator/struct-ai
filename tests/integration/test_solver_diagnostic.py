import json

import pytest
from pydantic import ValidationError

from struct_ai.exceptions import InputOutOfRange
from struct_ai.serialization import canonical_json
from struct_ai.services import engine_service


def test_real_opensees_matches_independently_derived_example():
    # Synthetic beam, no IS values: EI = 25e6 * 0.0008 = 20,000 kN*m².
    # Integrating M=P*(L-y) twice: x_tip=12*27/(3*20,000)=0.0054 m.
    # Rotation_z=-12*9/(2*20,000)=-0.0027 rad.
    # Sum Fx=0 -> Rx=-12 kN; sum M_base=0 -> Mz=12*3=36 kN*m; Ry=0.
    run = engine_service.run_diagnostic(engine_service.diagnostic_example_input())
    observed = run.result.observations
    assert observed.tip_displacement_m == pytest.approx(0.0054, rel=1e-12)
    assert observed.tip_rotation_rad == pytest.approx(-0.0027, rel=1e-12)
    assert observed.support_fx_kn == pytest.approx(-12.0, rel=1e-12)
    assert observed.support_fy_kn == pytest.approx(0.0, abs=1e-12)
    assert observed.support_mz_kn_m == pytest.approx(36.0, rel=1e-12)
    assert len(run.result.checks) == 5
    assert all(check.ok for check in run.result.checks)
    assert run.result.code_usage.constants == ()
    assert not run.result.building_design_available


@pytest.mark.parametrize("force_kn", [-12.0, 6.0, 24.0])
def test_load_sign_and_proportional_response(force_kn):
    data = engine_service.diagnostic_example_input().model_dump() | {"force_kn": force_kn}
    result = engine_service.run_diagnostic(data).result.observations
    # Unit flexibility L³/(3EI)=27/60000=0.00045 m/kN independently.
    assert result.tip_displacement_m == pytest.approx(force_kn * 0.00045, rel=1e-12)
    assert result.support_fx_kn == pytest.approx(-force_kn, rel=1e-12)
    assert result.support_mz_kn_m == pytest.approx(3.0 * force_kn, rel=1e-12)


def test_inertia_change_has_independent_expected_deflection():
    data = engine_service.diagnostic_example_input().model_dump() | {"inertia_m4": 0.0016}
    # Twice EI: 12*3³/(3*25e6*0.0016)=0.0027 m.
    assert engine_service.run_diagnostic(
        data
    ).result.observations.tip_displacement_m == pytest.approx(0.0027, rel=1e-12)


def test_repeated_runs_are_byte_identical_even_after_a_different_model():
    inputs = engine_service.diagnostic_example_input()
    first = engine_service.run_diagnostic(inputs)
    engine_service.run_diagnostic(inputs.model_dump() | {"length_m": 2.0})
    reopened_inputs = json.loads(inputs.model_dump_json())
    second = engine_service.run_diagnostic(reopened_inputs)
    assert canonical_json(first) == canonical_json(second)
    assert first.result_hash == second.result_hash


def test_progress_has_fixed_stages():
    stages = []
    engine_service.run_diagnostic(engine_service.diagnostic_example_input(), progress=stages.append)
    assert stages == [
        "Validating synthetic inputs",
        "Building two-node model",
        "Solving linear static analysis",
        "Checking independent analytical solution",
    ]


@pytest.mark.parametrize(
    "change",
    [
        {"length_m": 0.0},
        {"length_m": -1.0},
        {"force_kn": 0.0},
        {"area_m2": 0.0},
        {"inertia_m4": -0.001},
        {"elastic_modulus_kn_m2": float("nan")},
        {"length_m": "3"},
        {"length_m": True},
        {"unknown": 1.0},
    ],
)
def test_invalid_inputs_fail_with_clause_value_limit(change):
    data = engine_service.diagnostic_example_input().model_dump() | change
    with pytest.raises(InputOutOfRange) as caught:
        engine_service.run_diagnostic(data)
    assert caught.value.clause
    assert caught.value.limit
    assert caught.value.value == data


@pytest.mark.parametrize("text", ["", " ", "abc", "NaN", "inf", "3,0"])
def test_invalid_form_text_is_not_defaulted(text):
    fields = {
        key: str(value)
        for key, value in engine_service.diagnostic_example_input().model_dump().items()
    }
    fields["length_m"] = text
    with pytest.raises(InputOutOfRange):
        engine_service.run_diagnostic_form(fields)


def test_hashed_payload_cannot_be_changed_without_detection():
    run = engine_service.run_diagnostic(engine_service.diagnostic_example_input())
    payload = run.model_dump(mode="json")
    payload["result"]["observations"]["support_fx_kn"] = 12.0
    with pytest.raises(ValidationError, match="content hash"):
        type(run).model_validate_json(json.dumps(payload))
