import copy
import json
import math
from fractions import Fraction

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st
from pydantic import ValidationError

from struct_ai.design.beam_models import BeamFlexureRun
from struct_ai.exceptions import InputOutOfRange, ScopeRefusal
from struct_ai.serialization import canonical_json
from struct_ai.services import engine_service as service
from tests.beam_reference import (
    assessment,
    beam_request,
    compression_reference,
    flange_input,
    limiting_ratio,
    quadrature_reference,
    rectangular_reference,
)


@pytest.mark.parametrize("fy,expected", [(415, 0.137784375), (500, 0.1327402097761799)])
def test_annex_g_coefficients_are_derived_and_not_confused_with_integrated_curve(fy, expected):
    request = beam_request()
    request["materials"]["steel_grade"] = f"Fe{fy}"
    result = service.design_beam_flexure(request).result
    r = limiting_ratio(fy)
    # Independent rational rectangular-equivalent formula, not a stored Mu coefficient.
    k = float(Fraction(9, 25)) * r * (1 - float(Fraction(21, 50)) * r)
    assert k == pytest.approx(expected, rel=1e-13)
    assert result.limits.xu_max_over_d == pytest.approx(r, rel=1e-13)
    assert result.limits.rectangular_annex_g_coefficient == pytest.approx(expected, rel=1e-13)
    integrated = 0.446 * (17 / 21) * r * (1 - (99 / 238) * r)
    assert result.limits.rectangular_integrated_curve_coefficient == pytest.approx(
        integrated, rel=1e-12
    )
    assert result.limits.rectangular_annex_g_coefficient != pytest.approx(integrated, rel=1e-3)
    assert not result.verified_code_compliance
    assert result.status == "DRAFT_SECTION_CHECKS_PASS"


@pytest.mark.parametrize("fy", [415, 500])
@pytest.mark.parametrize("x", [60.0, 120.0, 210.0])
def test_three_independent_rectangular_hand_states_for_each_grade(fy, x):
    request = beam_request()
    request["materials"]["steel_grade"] = f"Fe{fy}"
    force, moment = rectangular_reference(x, 300.0, 25.0, 500.0)
    tension = force / (fy / 1.15)
    result = service.assess_beam_flexure(assessment(request, top=0.0, bottom=tension)).result
    assert result.section.neutral_axis_mm == pytest.approx(x, rel=1e-11)
    assert result.section.concrete_centroid_mm == pytest.approx(x * 99 / 238, rel=1e-11)
    assert result.section.concrete_force_n == pytest.approx(force, rel=1e-11)
    assert result.section.moment_capacity_kn_m == pytest.approx(moment / 1_000_000, rel=1e-11)


@pytest.mark.parametrize("fy", [415, 500])
@pytest.mark.parametrize(
    "dp,x,opposite", [(25.0, 180.0, 800.0), (100.0, 200.0, 900.0), (50.0, 20.0, 30.0)]
)
def test_doubly_reinforced_strain_compatibility_and_displaced_concrete(fy, dp, x, opposite):
    request = beam_request()
    request["geometry"]["top_centroid_from_top_mm"] = dp
    request["materials"]["steel_grade"] = f"Fe{fy}"
    request["factored_moment_kn_m"] = 1.0
    force, moment = rectangular_reference(x, 300.0, 25.0, 500.0)
    strain = 0.0035 * (x - dp) / x
    stress = compression_reference(strain, fy)
    ratio = strain / 0.002
    displaced = 0 if strain <= 0 else 0.446 * 25 * (1 if ratio >= 1 else 1 - (1 - ratio) ** 2)
    net = opposite * (stress - displaced)
    tension = (force + net) / (fy / 1.15)
    result = service.assess_beam_flexure(assessment(request, top=opposite, bottom=tension)).result
    state = result.section
    assert state.neutral_axis_mm == pytest.approx(x, rel=1e-11)
    assert state.opposite_layer_strain == pytest.approx(strain, rel=1e-10)
    assert state.opposite_steel_stress_n_mm2 == pytest.approx(stress, rel=1e-10)
    assert state.displaced_concrete_stress_n_mm2 == pytest.approx(displaced, abs=1e-9)
    assert state.opposite_net_force_n == pytest.approx(net, rel=1e-10)
    assert state.moment_capacity_kn_m == pytest.approx((moment + net * (500 - dp)) / 1e6, rel=1e-10)
    if strain > 0:
        assert state.opposite_steel_stress_n_mm2 < fy / 1.15  # Not assumed yielded.
    else:
        assert state.opposite_net_force_n < 0  # Opposite layer really is in tension.
        check = next(c for c in result.checks if c.name == "Maximum tension steel (overall D)")
        assert check.demand == tension + opposite


@pytest.mark.parametrize("shape", ["T", "L"])
@pytest.mark.parametrize(
    "x,case",
    [
        (60.0, "NA_IN_FLANGE"),
        (150.0, "NA_IN_WEB_FLANGE_PART_PARABOLIC"),
        (235.0, "NA_IN_WEB_FLANGE_PLATEAU"),
    ],
)
def test_flange_states_against_independent_piecewise_quadrature(shape, x, case):
    request = beam_request()
    request["geometry"]["flange"] = flange_input() | {"kind": shape}
    request["factored_moment_kn_m"] = 1.0
    # T formula 1900 capped to 1000; L formula 1100 also capped to 1000.
    force, moment = quadrature_reference(x, bw=300.0, bf=1000.0, thickness=100.0, fck=25.0, d=500.0)
    result = service.assess_beam_flexure(
        assessment(request, top=0.0, bottom=force / (415 / 1.15))
    ).result
    assert result.section.compression_case == case
    assert result.section.effective_flange_width_mm == 1000.0
    assert result.section.neutral_axis_mm == pytest.approx(x, rel=1e-11)
    assert result.section.concrete_force_n == pytest.approx(force, rel=1e-11)
    assert result.section.moment_capacity_kn_m == pytest.approx(moment / 1e6, rel=1e-11)
    assert result.section.flange_width_capped_by_actual


@pytest.mark.parametrize(
    "shape,rule,actual,expected",
    [
        ("T", "SLAB_BEAM", 3000.0, 1900.0),
        ("L", "SLAB_BEAM", 3000.0, 1100.0),
        ("T", "ISOLATED", 1000.0, 900.0),
        ("L", "ISOLATED", 1000.0, 600.0),
        ("T", "ISOLATED", 500.0, 500.0),
        ("L", "SLAB_BEAM", 500.0, 500.0),
    ],
)
def test_four_effective_width_rules_and_actual_width_cap(shape, rule, actual, expected):
    request = beam_request()
    request["geometry"]["flange"] = flange_input() | {
        "kind": shape,
        "width_rule": rule,
        "actual_width_mm": actual,
    }
    result = service.design_beam_flexure(request).result
    assert result.section.effective_flange_width_mm == expected
    assert any(c.name == "Flange transverse reinforcement" and c.ok for c in result.checks)


def test_flange_transition_is_continuous_not_a_rounded_block_jump():
    request = beam_request()
    request["geometry"]["flange"] = flange_input()
    states = []
    for x in (99.9999, 100.0, 100.0001):
        force, moment = quadrature_reference(
            x, bw=300.0, bf=1000.0, thickness=100.0, fck=25.0, d=500.0
        )
        result = service.assess_beam_flexure(
            assessment(request, top=0.0, bottom=force / (415 / 1.15))
        ).result
        states.append(result.section)
        assert result.section.moment_capacity_kn_m == pytest.approx(moment / 1e6, rel=1e-10)
    assert (
        states[0].moment_capacity_kn_m
        < states[1].moment_capacity_kn_m
        < states[2].moment_capacity_kn_m
    )
    assert states[2].moment_capacity_kn_m / states[0].moment_capacity_kn_m - 1 < 1e-5


def test_negative_bending_uses_web_and_the_other_explicit_centroid():
    request = beam_request()
    request["factored_moment_kn_m"] = -120.0
    request["geometry"]["top_centroid_from_top_mm"] = 70.0
    plain = service.design_beam_flexure(request).result
    request["geometry"]["flange"] = flange_input() | {"composite_action_confirmed": False}
    flanged = service.design_beam_flexure(request).result
    assert flanged.section.compression_face == "BOTTOM"
    assert flanged.section.tension_face == "TOP"
    assert flanged.section.effective_depth_mm == 480.0
    assert flanged.section.opposite_layer_depth_mm == 50.0
    assert flanged.section.compression_case == "FLANGE_IN_TENSION_IGNORED"
    assert flanged.reinforcement == plain.reinforcement
    assert flanged.section.moment_capacity_kn_m == plain.section.moment_capacity_kn_m
    assert not any("flange." in r.identifier for r in flanged.code_usage.constants)


def test_mirroring_geometry_and_moment_mirrors_steel_not_capacity():
    request = beam_request()
    request["geometry"]["flange"] = flange_input()
    request["geometry"]["top_centroid_from_top_mm"] = 60.0
    positive = service.design_beam_flexure(request).result
    request["factored_moment_kn_m"] *= -1
    request["geometry"]["flange"]["face"] = "BOTTOM"
    request["geometry"]["top_centroid_from_top_mm"] = 50.0
    request["geometry"]["bottom_centroid_from_bottom_mm"] = 60.0
    negative = service.design_beam_flexure(request).result
    assert positive.section.moment_capacity_kn_m == negative.section.moment_capacity_kn_m
    assert positive.reinforcement.bottom_mm2 == negative.reinforcement.top_mm2


def test_zero_overhang_reduces_exactly_to_a_rectangle():
    request = beam_request()
    plain = service.design_beam_flexure(request).result
    request["geometry"]["flange"] = flange_input() | {"actual_width_mm": 300.0}
    flanged = service.design_beam_flexure(request).result
    assert plain.section == flanged.section
    assert plain.reinforcement == flanged.reinforcement
    assert plain.code_usage == flanged.code_usage


def test_minimum_provision_is_explicit_not_a_fake_round_trip():
    request = beam_request() | {"factored_moment_kn_m": 1.0}
    result = service.design_beam_flexure(request).result
    assert result.sizing.governing == "MINIMUM_TENSION_STEEL"
    assert result.reinforcement.bottom_mm2 == 0.85 * 300 * 500 / 415
    assert result.section.moment_capacity_kn_m > 1.0
    assert result.reinforcement.bottom_mm2 > result.sizing.tension_area_from_flexure_mm2


@pytest.mark.parametrize(
    "tension,opposite,expected_ok", [(6300.0, 5000.0, True), (6700.0, 5500.0, False)]
)
def test_maximum_steel_uses_overall_D_not_effective_d(tension, opposite, expected_ok):
    request = assessment(beam_request(), top=opposite, bottom=tension)
    result = service.assess_beam_flexure(request).result
    check = next(c for c in result.checks if c.name == "Maximum tension steel (overall D)")
    assert check.capacity == 0.04 * 300 * 550 == 6600.0
    assert tension > 0.04 * 300 * 500  # A wrong d-based limit would reject both.
    assert check.ok is expected_ok
    assert result.status == ("DRAFT_SECTION_CHECKS_PASS" if expected_ok else "REVISE_SECTION")


def test_insufficient_provided_capacity_is_a_failed_check_not_a_pass_or_resize():
    request = assessment(beam_request() | {"factored_moment_kn_m": 200.0}, top=0.0, bottom=800.0)
    result = service.assess_beam_flexure(request).result
    moment_check = next(c for c in result.checks if c.name == "Flexural moment")
    assert not moment_check.ok and moment_check.ratio > 1
    assert result.status == "REVISE_SECTION"
    assert result.reinforcement.bottom_mm2 == 800.0
    report = service.beam_flexure_report(
        BeamFlexureRun(result=result, result_hash=service.assess_beam_flexure(request).result_hash)
    )
    assert "**FAIL**" in report and "REVISE_SECTION" in report


def test_over_reinforced_section_is_refused_instead_of_clamped():
    with pytest.raises(InputOutOfRange, match="neutral axis beyond") as caught:
        service.assess_beam_flexure(assessment(beam_request(), top=0.0, bottom=4000.0))
    assert "38.1" in caught.value.clause
    assert caught.value.value["ok"] is False
    assert caught.value.limit


def test_single_policy_does_not_silently_add_compression_steel():
    with pytest.raises(InputOutOfRange, match="Singly reinforced limit"):
        service.design_beam_flexure(beam_request() | {"factored_moment_kn_m": 350.0})


@pytest.mark.parametrize("fy", [415, 500])
def test_double_sizing_forward_checks_and_unyielded_compression_steel(fy):
    request = beam_request() | {
        "factored_moment_kn_m": 350.0,
        "reinforcement_policy": "ALLOW_COMPRESSION_STEEL",
    }
    request["materials"]["steel_grade"] = f"Fe{fy}"
    result = service.design_beam_flexure(request).result
    assert result.sizing.governing == "DOUBLY_REINFORCED"
    assert result.reinforcement.top_mm2 > 0
    assert 0 < result.section.opposite_steel_stress_n_mm2 < fy / 1.15
    assert result.section.displaced_concrete_stress_n_mm2 > 0
    assert result.section.neutral_axis_mm < result.limits.xu_max_mm
    assert result.section.moment_capacity_kn_m == pytest.approx(350.0, rel=0.001)
    assert all(c.ok for c in result.checks)
    assert result.code_usage.unverified_count == 24


@pytest.mark.parametrize(
    "change",
    [
        {"acknowledge_unverified": False},
        {"acknowledge_unverified": 1},
        {"factored_moment_kn_m": 0.0},
        {"factored_moment_kn_m": math.inf},
        {"factored_moment_kn_m": "120"},
        {"factored_moment_kn_m": True},
        {"action_basis": "UNFACTORED"},
        {"unknown": 3},
    ],
)
def test_no_defaults_coercion_nonfinite_or_unknown_request_fields(change):
    with pytest.raises(InputOutOfRange) as caught:
        service.design_beam_flexure(beam_request() | change)
    assert caught.value.clause and caught.value.limit


@pytest.mark.parametrize("field", list(beam_request()))
def test_every_required_top_level_field_must_be_explicit(field):
    request = beam_request()
    del request[field]
    with pytest.raises(InputOutOfRange):
        service.design_beam_flexure(request)


@pytest.mark.parametrize(
    "materials",
    [
        {"fck_n_mm2": 100.0},
        {"steel_grade": "Fe550"},
        {"steel_curve": "TMT"},
    ],
)
def test_unsupported_material_domains_are_not_mapped_or_clamped(materials):
    request = beam_request()
    request["materials"].update(materials)
    with pytest.raises(InputOutOfRange):
        service.design_beam_flexure(request)


@pytest.mark.parametrize(
    "change",
    [
        {"top_centroid_from_top_mm": 500.0},
        {"overall_depth_mm": 40.0},
        {"web_width_mm": -1.0},
        {"flange": flange_input() | {"actual_width_mm": 100.0}},
        {"flange": flange_input() | {"thickness_mm": 550.0}},
    ],
)
def test_invalid_geometry_is_not_repaired(change):
    request = beam_request()
    request["geometry"].update(change)
    with pytest.raises(InputOutOfRange):
        service.design_beam_flexure(request)


@pytest.mark.parametrize(
    "change,exception",
    [
        ({"composite_action_confirmed": False}, ScopeRefusal),
        ({"main_steel_mm2_per_m": None}, InputOutOfRange),
        ({"transverse_steel_mm2_per_m": 479.0}, InputOutOfRange),
    ],
)
def test_inadequate_flange_coupling_does_not_get_flanged_capacity(change, exception):
    request = beam_request()
    request["geometry"]["flange"] = flange_input() | change
    with pytest.raises(exception) as caught:
        service.design_beam_flexure(request)
    assert "23.1.1" in caught.value.clause


def test_nonzero_axial_action_is_explicitly_refused():
    with pytest.raises(ScopeRefusal, match="axial action"):
        service.design_beam_flexure(beam_request() | {"axial_force_kn": 1.0})


def test_section_run_is_deterministic_and_hash_covers_data_checks_and_warning():
    request = beam_request()
    first, second = service.design_beam_flexure(request), service.design_beam_flexure(request)
    assert canonical_json(first) == canonical_json(second)
    assert first.result.code_usage.warning == "UNVERIFIED CODE CONSTANTS USED: 12"
    assert first.result.code_usage.warning in first.result.warnings
    altered = first.model_dump()
    altered["result"]["section"]["moment_capacity_kn_m"] += 10
    with pytest.raises(ValidationError, match="hash"):
        BeamFlexureRun.model_validate(altered)
    altered = first.model_dump()
    altered["result"]["warnings"] = ()
    with pytest.raises(ValidationError, match="warning"):
        BeamFlexureRun.model_validate(altered)


def test_json_duplicate_and_nonfinite_fields_fail_before_calculation():
    original = json.dumps(beam_request())
    for invalid in (
        original.replace('"operation": "DESIGN"', '"operation":"DESIGN","operation":"ASSESS"'),
        original.replace("120.0", "NaN"),
        "[]",
        "null",
        " " * 1_000_001,
    ):
        with pytest.raises(InputOutOfRange):
            service.run_beam_flexure_json(invalid)


def test_float_units_conversion_regression_and_actual_input_unchanged():
    request = beam_request()
    preserved = copy.deepcopy(request)
    run = service.design_beam_flexure(request)
    assert request == preserved
    state = run.result.section
    # Independent N*mm -> kN*m: 1000 force and 1000 length, not only one factor.
    moment_n_mm = state.concrete_force_n * (500 - state.concrete_centroid_mm)
    assert state.moment_capacity_kn_m == pytest.approx(moment_n_mm / 1_000_000, rel=1e-13)
    assert state.moment_capacity_kn_m == pytest.approx(120.0, rel=0.001)


@settings(max_examples=50, derandomize=True, deadline=None, database=None)
@given(
    fy=st.sampled_from([415, 500]),
    fck=st.integers(20, 40),
    width=st.integers(200, 600),
    d=st.integers(350, 850),
    fraction=st.floats(min_value=0.4, max_value=1.8),
)
def test_property_inverse_forward_round_trip_within_one_tenth_percent(fy, fck, width, d, fraction):
    request = beam_request()
    request["geometry"].update(web_width_mm=float(width), overall_depth_mm=float(d + 50))
    request["materials"].update(steel_grade=f"Fe{fy}", fck_n_mm2=float(fck))
    _, limit_moment = rectangular_reference(limiting_ratio(fy) * d, width, fck, d)
    demand = fraction * limit_moment / 1e6
    request.update(factored_moment_kn_m=demand, reinforcement_policy="ALLOW_COMPRESSION_STEEL")
    designed = service.design_beam_flexure(request).result
    assert designed.sizing.governing != "MINIMUM_TENSION_STEEL"
    checked = service.assess_beam_flexure(
        assessment(
            request, top=designed.reinforcement.top_mm2, bottom=designed.reinforcement.bottom_mm2
        )
    ).result
    assert checked.section.moment_capacity_kn_m == pytest.approx(demand, rel=0.001)
    assert all(c.ok for c in checked.checks)
    assert checked.section == designed.section


@settings(max_examples=40, derandomize=True, deadline=None, database=None)
@given(
    low=st.floats(min_value=0.2, max_value=0.65), increment=st.floats(min_value=0.05, max_value=0.3)
)
def test_property_capacity_is_monotone_in_tension_steel_within_ductile_domain(low, increment):
    request = beam_request() | {"factored_moment_kn_m": 1.0}
    force, _ = rectangular_reference(limiting_ratio(415) * 500, 300, 25, 500)
    limit_area = force / (415 / 1.15)
    first = service.assess_beam_flexure(
        assessment(request, top=0.0, bottom=low * limit_area)
    ).result
    second = service.assess_beam_flexure(
        assessment(request, top=0.0, bottom=(low + increment) * limit_area)
    ).result
    assert second.section.moment_capacity_kn_m > first.section.moment_capacity_kn_m
    assert second.section.neutral_axis_mm > first.section.neutral_axis_mm


@settings(max_examples=30, derandomize=True, deadline=None, database=None)
@given(
    width=st.floats(min_value=400.0, max_value=1200.0),
    extra=st.floats(min_value=1.0, max_value=600.0),
)
def test_property_capacity_does_not_fall_when_an_admissible_flange_widens(width, extra):
    request = beam_request() | {"factored_moment_kn_m": 1.0}
    request["geometry"]["flange"] = flange_input() | {
        "actual_width_mm": width,
        "zero_moment_distance_mm": 30000.0,
    }
    first = service.assess_beam_flexure(assessment(request, top=0.0, bottom=1000.0)).result
    request["geometry"]["flange"]["actual_width_mm"] += extra
    second = service.assess_beam_flexure(assessment(request, top=0.0, bottom=1000.0)).result
    assert second.section.moment_capacity_kn_m > first.section.moment_capacity_kn_m


@pytest.mark.parametrize("opposite,expected_ok", [(6400.0, True), (6700.0, False)])
def test_compression_area_maximum_also_uses_overall_depth(opposite, expected_ok):
    result = service.assess_beam_flexure(
        assessment(beam_request(), top=opposite, bottom=6000.0)
    ).result
    check = next(c for c in result.checks if c.name == "Maximum opposite-layer steel (overall D)")
    assert result.section.opposite_layer_strain > 0
    assert check.capacity == 0.04 * 300 * 550
    assert check.demand > 0.04 * 300 * 500
    assert check.ok is expected_ok


@pytest.mark.parametrize("shape", ["T", "L"])
@pytest.mark.parametrize("fy", [415, 500])
def test_doubly_reinforced_flange_hand_state_uses_independent_quadrature(shape, fy):
    request = beam_request() | {"factored_moment_kn_m": 1.0}
    request["geometry"]["flange"] = flange_input() | {"kind": shape}
    request["geometry"]["top_centroid_from_top_mm"] = 75.0
    request["materials"]["steel_grade"] = f"Fe{fy}"
    x, opposite, dp = 170.0, 800.0, 75.0
    force, concrete_moment = quadrature_reference(
        x, bw=300.0, bf=1000.0, thickness=100.0, fck=25.0, d=500.0
    )
    strain = 0.0035 * (1 - dp / x)
    stress = compression_reference(strain, fy)
    displaced = 0.446 * 25 * (1 - (1 - strain / 0.002) ** 2)
    net = opposite * (stress - displaced)
    tension = (force + net) / (fy / 1.15)
    result = service.assess_beam_flexure(assessment(request, top=opposite, bottom=tension)).result
    assert result.section.neutral_axis_mm == pytest.approx(x, rel=1e-11)
    assert result.section.moment_capacity_kn_m == pytest.approx(
        (concrete_moment + net * (500 - dp)) / 1e6, rel=1e-10
    )
    assert result.section.opposite_steel_stress_n_mm2 == pytest.approx(stress, rel=1e-11)
    assert all(check.ok for check in result.checks)


@pytest.mark.parametrize("shape", ["T", "L"])
@pytest.mark.parametrize("fy", [415, 500])
def test_double_flanged_inverse_forward_roundtrip(shape, fy):
    request = beam_request() | {"reinforcement_policy": "ALLOW_COMPRESSION_STEEL"}
    request["geometry"]["flange"] = flange_input() | {"kind": shape}
    request["materials"]["steel_grade"] = f"Fe{fy}"
    _, limit_moment = quadrature_reference(
        limiting_ratio(fy) * 500, bw=300.0, bf=1000.0, thickness=100.0, fck=25.0, d=500.0
    )
    request["factored_moment_kn_m"] = 1.3 * limit_moment / 1e6
    result = service.design_beam_flexure(request).result
    assert result.sizing.governing == "DOUBLY_REINFORCED"
    assert result.section.moment_capacity_kn_m == pytest.approx(
        request["factored_moment_kn_m"], rel=0.001
    )
    assert result.code_usage.unverified_count == 27
    assert all(check.ok for check in result.checks)


def test_public_unit_limiting_moment_equality_is_not_a_false_overlimit_refusal():
    # Found by a seeded boundary probe. N mm -> kN m -> N mm is not always bit-exact.
    request = beam_request() | {"factored_moment_kn_m": 1.0}
    request["geometry"].update(web_width_mm=588.7578458302612, overall_depth_mm=732.9649993950547)
    request["materials"].update(fck_n_mm2=28.162040365494743, steel_grade="Fe500")
    limit = service.design_beam_flexure(request).result.limits.concrete_only_limiting_moment_kn_m
    result = service.design_beam_flexure(request | {"factored_moment_kn_m": limit}).result
    assert result.status == "DRAFT_SECTION_CHECKS_PASS"
    assert result.section.moment_capacity_kn_m == limit
    assert result.sizing.numerical_moment_reserve_kn_m == 0.0
    # No positive passing tolerance is introduced by handling an exact public-unit endpoint.
    with pytest.raises(InputOutOfRange, match="Singly reinforced limit"):
        service.design_beam_flexure(
            request | {"factored_moment_kn_m": math.nextafter(limit, math.inf)}
        )
