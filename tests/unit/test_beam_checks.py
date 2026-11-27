import copy
import math
from fractions import Fraction as F

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from struct_ai.codes.registry import CodeRegistry
from struct_ai.design.beam_checks import BeamCheckData
from struct_ai.exceptions import InputOutOfRange, ScopeRefusal
from struct_ai.services import engine_service as service
from tests.beam_reference import flange_input
from tests.component_reference import (
    checks,
    cover_request,
    deflection_request,
    development_request,
    quantities,
    shear_request,
    torsion_request,
)


@pytest.mark.parametrize(
    "factory",
    [shear_request, torsion_request, development_request, cover_request, deflection_request],
)
def test_explicit_sample_subchecks_are_deterministic_without_mutating_input(factory):
    request = factory()
    original = copy.deepcopy(request)
    first, second = service.assess_beam_checks(request), service.assess_beam_checks(request)
    assert first == second and request == original
    assert first.result.status == "DRAFT_COMPONENT_CHECKS_PASS"
    assert not first.result.verified_code_compliance
    assert not first.result.complete_member_design_available
    assert all(c.ok for c in first.result.checks)
    assert first.result.code_usage.warning in first.result.warnings


@pytest.mark.parametrize(
    "p,expected",
    [
        (0.0, 0.29),
        (0.1, 0.29),
        (0.15, 0.29),
        (0.2, 0.325),
        (0.25, 0.36),
        (0.375, 0.425),
        (1.0, 0.64),
        (1.125, 0.67),
        (2.9, 0.912),
        (3.0, 0.92),
        (4.0, 0.92),
    ],
)
def test_independent_table19_interpolation_and_explicit_end_rows(p, expected):
    registry = CodeRegistry.load()
    actual, low, high = BeamCheckData(registry, registry.new_tracker()).shear_strength("m25", p)
    assert actual == pytest.approx(expected, rel=1e-14)
    assert low <= high


def test_shear_stress_area_minimum_and_spacing_use_independent_arithmetic():
    run = service.assess_beam_checks(shear_request())
    q, c = quantities(run), checks(run)
    assert q["tensile_steel_percentage"] == 1.0
    assert q["concrete_shear_strength"] == 0.64
    assert q["stirrup_area"] == pytest.approx(50 * math.pi)
    assert q["stirrup_design_stress"] == pytest.approx(361.05)
    assert c["Maximum equivalent shear stress"].demand == 0.8
    assert c["Maximum equivalent shear stress"].capacity == 3.1
    assert c["Minimum vertical stirrup rate"].demand == pytest.approx(
        float(F(120, 1) / F("361.05"))
    )
    assert c["Equivalent shear stirrup rate"].demand == pytest.approx(float(F(48, 1) / F("361.05")))
    assert c["Vertical stirrup spacing"].capacity == 300.0
    assert q["primary_equivalent_moment"] == 80.0


def test_torsion_independent_equivalent_actions_cage_and_sideface_arithmetic():
    run = service.assess_beam_checks(torsion_request())
    q, c = quantities(run), checks(run)
    # N, mm: 120000 + (8/5)*30000000/300 = 280000; Mt=30*(17/6)/(17/10)=50.
    assert q["equivalent_shear"] == pytest.approx(280.0)
    assert q["torsion_equivalent_moment"] == pytest.approx(50.0)
    assert q["primary_equivalent_moment"] == pytest.approx(130.0)
    assert q["corner_bar_depth"] == 450.0
    required_rate = (F(30_000_000, 200 * 450) + F(120_000, 1) / (F(5, 2) * 450)) / F("361.05")
    assert c["Combined torsion/shear stirrup rate"].demand == pytest.approx(float(required_rate))
    assert c["Closed torsion stirrup spacing"].capacity == 177.5
    assert c["Left side-face reinforcement"].demand == 82.5  # .001*300*550/2, not d.
    assert c["Right side-face reinforcement"].demand == 82.5
    assert len(run.result.flexure_evaluations) == 1


@pytest.mark.parametrize("moment_sign", [-1.0, 1.0])
@pytest.mark.parametrize(
    "shear_sign,torsion_sign", [(-1.0, -1.0), (-1.0, 1.0), (1.0, -1.0), (1.0, 1.0)]
)
def test_torsion_magnitudes_and_opposite_physical_face_demands(
    moment_sign, shear_sign, torsion_sign
):
    request = torsion_request()
    request["flexure"]["factored_moment_kn_m"] = 10.0 * moment_sign
    request["flexure"]["reinforcement"] = {"top_mm2": 1500.0, "bottom_mm2": 1500.0}
    request["factored_shear_kn"] *= shear_sign
    request["factored_torsion_kn_m"] *= torsion_sign
    run = service.assess_beam_checks(request)
    q = quantities(run)
    assert q["primary_equivalent_moment"] == pytest.approx(60.0 * moment_sign)
    assert q["opposite_equivalent_moment"] == pytest.approx(-40.0 * moment_sign)
    assert len(run.result.flexure_evaluations) == 2
    first, second = run.result.flexure_evaluations
    assert first.result.section.tension_face != second.result.section.tension_face
    assert all(c.ok for c in run.result.checks)


def test_asymmetric_negative_depth_uses_other_physical_layer_not_positive_d():
    request = shear_request()
    request["flexure"]["geometry"]["top_centroid_from_top_mm"] = 75.0
    request["flexure"]["factored_moment_kn_m"] = -80.0
    request["flexure"]["reinforcement"] = {"top_mm2": 1425.0, "bottom_mm2": 300.0}
    q = quantities(service.assess_beam_checks(request))
    assert q["effective_depth"] == 475.0
    assert q["tensile_steel_percentage"] == 1.0


def test_flanged_shear_uses_web_not_effective_flange_width():
    request = shear_request()
    request["flexure"]["geometry"]["flange"] = flange_input()
    q = quantities(service.assess_beam_checks(request))
    assert q["tensile_steel_percentage"] == 1.0
    assert q["concrete_shear_strength"] == 0.64
    request = torsion_request()
    request["flexure"]["geometry"]["flange"] = flange_input()
    with pytest.raises(ScopeRefusal, match="Flanged torsion"):
        service.assess_beam_checks(request)


def test_explicit_fy_ceiling_not_silent_stirrup_grade_substitution():
    request = shear_request()
    first = service.assess_beam_checks(request)
    request["stirrups"]["steel_grade"] = "Fe500"
    second = service.assess_beam_checks(request)
    q = quantities(second)
    assert q["stirrup_input_yield"] == 500.0
    assert q["stirrup_credited_yield"] == 415.0
    assert q["stirrup_design_stress"] == quantities(first)["stirrup_design_stress"]
    assert first.result_hash != second.result_hash
    request["stirrups"]["steel_grade"] = "Fe250"
    assert quantities(service.assess_beam_checks(request))["stirrup_design_stress"] == 217.5


@pytest.mark.parametrize("shear,ok", [(465.0, True), (465.000001, False)])
def test_maximum_shear_does_not_clamp_to_pass(shear, ok):
    request = shear_request() | {"factored_shear_kn": shear}
    request["stirrups"]["spacing_mm"] = 10.0
    run = service.assess_beam_checks(request)
    assert checks(run)["Maximum equivalent shear stress"].ok is ok
    assert (run.result.status == "DRAFT_COMPONENT_CHECKS_PASS") is ok
    assert run.result.inputs.factored_shear_kn == shear


@pytest.mark.parametrize(
    "field",
    ["critical_section_actions_confirmed", "longitudinal_anchorage_and_continuity_confirmed"],
)
def test_unconfirmed_prerequisites_are_not_silently_assumed(field):
    with pytest.raises(ScopeRefusal):
        service.assess_beam_checks(shear_request() | {field: False})


@pytest.mark.parametrize("change", ["missing", "open", "four_legs", "outside_cage"])
def test_torsion_geometry_failures_are_explicit(change):
    request = torsion_request()
    if change == "missing":
        request["torsion_geometry"] = None
    if change == "open":
        request["torsion_geometry"]["closed_rectangular_stirrups_and_corner_bars_confirmed"] = False
    if change == "four_legs":
        request["stirrups"]["effective_legs"] = 4
    if change == "outside_cage":
        request["torsion_geometry"]["corner_bar_width_mm"] = 300.0
    with pytest.raises((InputOutOfRange, ScopeRefusal)):
        service.assess_beam_checks(request)


def test_sideface_failures_and_missing_values_are_not_hidden():
    request = torsion_request()
    request["side_faces"]["left_area_mm2"] = 80.0
    run = service.assess_beam_checks(request)
    assert not checks(run)["Left side-face reinforcement"].ok
    assert run.result.status == "REVISE_SECTION"
    request["side_faces"] = None
    with pytest.raises(InputOutOfRange, match="side-face"):
        service.assess_beam_checks(request)


@pytest.mark.parametrize(
    "grade,bond", [("M20", 1.2), ("M25", 1.4), ("M30", 1.5), ("M35", 1.7), ("M40", 1.9)]
)
@pytest.mark.parametrize("state,multiplier", [("TENSION", 1.0), ("COMPRESSION", 1.25)])
@pytest.mark.parametrize("bundle,factor", [(1, 1.0), (2, 1.1), (3, 1.2), (4, 1.33)])
def test_development_equilibrium_not_incorrect_percentage_length_reduction(
    grade, bond, state, multiplier, bundle, factor
):
    request = development_request() | {
        "concrete_grade": grade,
        "stress_state": state,
        "equal_diameter_bundle_count": bundle,
        "available_straight_length_mm": 2000.0,
    }
    run = service.assess_beam_checks(request)
    q = quantities(run)
    assert q["design_bond_stress"] == pytest.approx(bond * 1.6 * multiplier)
    independent = 20 * 300 / (4 * bond * 1.6 * multiplier) * factor
    assert q["required_straight_development_length"] == pytest.approx(independent, rel=1e-14)


def test_development_stress_is_required_not_assumed_yield_and_over_yield_refused():
    request = development_request() | {"design_bar_stress_n_mm2": 150.0}
    assert quantities(service.assess_beam_checks(request))[
        "required_straight_development_length"
    ] == pytest.approx(334.8214285714286)
    with pytest.raises(InputOutOfRange, match="Bar stress"):
        service.assess_beam_checks(development_request() | {"design_bar_stress_n_mm2": 400.0})
    failed = service.assess_beam_checks(
        development_request() | {"available_straight_length_mm": 100.0}
    )
    assert failed.result.status == "REVISE_SECTION"


@pytest.mark.parametrize(
    "exposure,cover",
    [
        ("MILD", 20.0),
        ("MODERATE", 30.0),
        ("SEVERE", 45.0),
        ("VERY_SEVERE", 50.0),
        ("EXTREME", 75.0),
    ],
)
def test_cover_bases_exact_equality_and_next_value_below(exposure, cover):
    request = cover_request() | {"exposure": exposure, "nominal_cover_to_outermost_steel_mm": cover}
    assert checks(service.assess_beam_checks(request))["Base durability and bar-diameter cover"].ok
    request["nominal_cover_to_outermost_steel_mm"] = math.nextafter(cover, 0.0)
    assert not checks(service.assess_beam_checks(request))[
        "Base durability and bar-diameter cover"
    ].ok


def test_bar_diameter_and_horizontal_vertical_spacing_have_distinct_limits():
    request = cover_request() | {
        "exposure": "MILD",
        "largest_bar_diameter_mm": 32.0,
        "nominal_maximum_aggregate_mm": 60.0,
    }
    c = checks(service.assess_beam_checks(request))
    assert c["Base durability and bar-diameter cover"].demand == 32.0
    assert c["Minimum horizontal clear spacing"].demand == 65.0
    assert c["Minimum vertical clear spacing"].demand == 40.0
    assert not c["Minimum horizontal clear spacing"].ok
    assert not c["Minimum vertical clear spacing"].ok


def test_no_vertical_spacing_in_single_row_and_no_unaligned_multirow_pass():
    request = cover_request() | {"number_of_rows": 1, "minimum_vertical_clear_mm": None}
    assert len(service.assess_beam_checks(request).result.checks) == 2
    with pytest.raises(ScopeRefusal, match="aligned"):
        service.assess_beam_checks(cover_request() | {"rows_vertically_aligned": False})


@pytest.mark.parametrize(
    "span,final,post", [(6000.0, 24.0, 120.0 / 7), (7000.0, 28.0, 20.0), (8000.0, 32.0, 20.0)]
)
def test_deflection_limits_are_independent_and_use_lesser_post_limit(span, final, post):
    c = checks(service.assess_beam_checks(deflection_request() | {"effective_span_mm": span}))
    assert c["Final all-effects deflection"].capacity == final
    assert c["After partitions/finishes deflection"].capacity == pytest.approx(post)


@pytest.mark.parametrize(
    "field,bound",
    [
        ("final_all_effects_deflection_mm", 24.0),
        ("after_partitions_finishes_deflection_mm", 6000.0 / 350),
    ],
)
def test_deflection_exact_boundary_then_next_representable_failure(field, bound):
    request = deflection_request() | {field: bound}
    assert service.assess_beam_checks(request).result.status == "DRAFT_COMPONENT_CHECKS_PASS"
    assert (
        service.assess_beam_checks(request | {field: math.nextafter(bound, math.inf)}).result.status
        == "REVISE_SECTION"
    )


def test_immediate_deflection_is_not_used_as_final_deflection():
    with pytest.raises(ScopeRefusal, match="Immediate"):
        service.assess_beam_checks(
            deflection_request() | {"includes_creep_shrinkage_temperature": False}
        )


@settings(max_examples=30, deadline=None)
@given(st.floats(min_value=30.0, max_value=250.0, allow_nan=False, allow_infinity=False))
def test_more_stirrup_provision_never_increases_utilisation(spacing):
    request = shear_request()
    request["stirrups"]["spacing_mm"] = spacing
    before = checks(service.assess_beam_checks(request))
    request["stirrups"]["spacing_mm"] = spacing / 2
    after = checks(service.assess_beam_checks(request))
    for key in (
        "Minimum vertical stirrup rate",
        "Equivalent shear stirrup rate",
        "Vertical stirrup spacing",
    ):
        assert after[key].ratio <= before[key].ratio


@settings(max_examples=30, deadline=None)
@given(st.floats(min_value=50.0, max_value=350.0, allow_nan=False, allow_infinity=False))
def test_development_length_scales_linearly_with_required_stress(stress):
    one = service.assess_beam_checks(development_request() | {"design_bar_stress_n_mm2": stress})
    two = service.assess_beam_checks(
        development_request() | {"design_bar_stress_n_mm2": stress / 2}
    )
    assert quantities(two)["required_straight_development_length"] == pytest.approx(
        quantities(one)["required_straight_development_length"] / 2, rel=1e-14
    )


def test_public_shear_endpoint_next_representable_overload_is_not_lost_in_stress_units():
    # Seeded probe found kN -> N -> stress rounding a real public-unit overload to equality.
    request = shear_request()
    b, overall = 244.01569998471433, 509.28391371365325
    request["flexure"]["geometry"].update(web_width_mm=b, overall_depth_mm=overall)
    request["flexure"]["reinforcement"] = {
        "top_mm2": 0.0,
        "bottom_mm2": 0.005 * b * (overall - 50.0),
    }
    request["flexure"]["factored_moment_kn_m"] = 1.0
    request["stirrups"]["spacing_mm"] = 5.0
    # Independent Table 20 M25 force limit: tau_cmax * bw * d / 1000.
    limit_kn = 3.1 * b * (overall - 50.0) / 1000.0
    request["factored_shear_kn"] = limit_kn
    assert service.assess_beam_checks(request).result.status == "DRAFT_COMPONENT_CHECKS_PASS"
    request["factored_shear_kn"] = math.nextafter(limit_kn, math.inf)
    assert service.assess_beam_checks(request).result.status == "REVISE_SECTION"


@settings(max_examples=35, deadline=None)
@given(
    b=st.floats(min_value=200.0, max_value=600.0, allow_nan=False, allow_infinity=False),
    overall=st.floats(min_value=300.0, max_value=700.0, allow_nan=False, allow_infinity=False),
)
def test_published_shear_endpoint_equality_and_nextafter_property(b, overall):
    request = shear_request()
    request["flexure"]["geometry"].update(web_width_mm=b, overall_depth_mm=overall)
    request["flexure"]["reinforcement"] = {
        "top_mm2": 0.0,
        "bottom_mm2": 0.005 * b * (overall - 50.0),
    }
    request["flexure"]["factored_moment_kn_m"] = 1.0
    request["factored_shear_kn"] = 1.0
    request["stirrups"]["spacing_mm"] = 5.0
    cap = checks(service.assess_beam_checks(request))[
        "Maximum equivalent shear force (public units)"
    ].capacity
    request["factored_shear_kn"] = cap
    assert service.assess_beam_checks(request).result.status == "DRAFT_COMPONENT_CHECKS_PASS"
    request["factored_shear_kn"] = math.nextafter(cap, math.inf)
    assert service.assess_beam_checks(request).result.status == "REVISE_SECTION"


@pytest.mark.parametrize(
    "field,value", [("stirrup_centreline_width_mm", 295.0), ("stirrup_centreline_depth_mm", 545.0)]
)
def test_stirrup_outer_fibre_cannot_project_outside_concrete(field, value):
    request = torsion_request()
    request["torsion_geometry"][field] = value
    with pytest.raises(InputOutOfRange, match="cage dimensions"):
        service.assess_beam_checks(request)


def test_tiny_opposite_equivalent_moment_is_refused_not_rounded_away():
    request = torsion_request()
    request["flexure"]["factored_moment_kn_m"] = 50.0 - 1e-8
    with pytest.raises(InputOutOfRange, match="Equivalent bending demand"):
        service.assess_beam_checks(request)
