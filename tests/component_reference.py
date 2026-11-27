"""Explicit synthetic M2 inputs and independent arithmetic, not production calculations."""

from tests.beam_reference import assessment, beam_request


def basis():
    return {
        "calculation_label": "SAMPLE component check — NOT a building",
        "source_basis": "PUBLIC_TEACHING_DRAFT",
        "acknowledge_unverified": True,
    }


def shear_request():
    return basis() | {
        "operation": "SHEAR_TORSION",
        "flexure": assessment(
            beam_request() | {"factored_moment_kn_m": 80.0}, top=300.0, bottom=1500.0
        ),
        "factored_shear_kn": 120.0,
        "factored_torsion_kn_m": 0.0,
        "section_conditions": "UNIFORM_NO_AXIAL_NO_ENHANCEMENT_NO_CURTAILMENT",
        "critical_section_actions_confirmed": True,
        "longitudinal_anchorage_and_continuity_confirmed": True,
        "stirrups": {
            "steel_grade": "Fe415",
            "diameter_mm": 10.0,
            "effective_legs": 2,
            "spacing_mm": 150.0,
            "enclosure_and_anchorage_confirmed": True,
        },
        "torsion_geometry": None,
        "side_faces": None,
    }


def torsion_request():
    request = shear_request()
    request.update(
        factored_torsion_kn_m=30.0,
        torsion_geometry={
            "corner_bar_width_mm": 200.0,
            "stirrup_centreline_width_mm": 230.0,
            "stirrup_centreline_depth_mm": 480.0,
            "closed_rectangular_stirrups_and_corner_bars_confirmed": True,
        },
        side_faces={"left_area_mm2": 100.0, "right_area_mm2": 100.0, "maximum_spacing_mm": 200.0},
    )
    request["stirrups"]["spacing_mm"] = 100.0
    return request


def development_request():
    return basis() | {
        "operation": "DEVELOPMENT_LENGTH",
        "concrete_grade": "M25",
        "steel_grade": "Fe415",
        "bar_type": "DEFORMED_IS1786",
        "stress_state": "TENSION",
        "bar_diameter_mm": 20.0,
        "design_bar_stress_n_mm2": 300.0,
        "equal_diameter_bundle_count": 1,
        "available_straight_length_mm": 800.0,
    }


def cover_request():
    return basis() | {
        "operation": "COVER_SPACING",
        "scope": "BASE_COVER_AND_MINIMUM_CLEAR_SPACING_ONLY",
        "exposure": "MODERATE",
        "nominal_cover_to_outermost_steel_mm": 35.0,
        "largest_bar_diameter_mm": 20.0,
        "nominal_maximum_aggregate_mm": 20.0,
        "minimum_horizontal_clear_mm": 30.0,
        "number_of_rows": 2,
        "minimum_vertical_clear_mm": 25.0,
        "rows_vertically_aligned": True,
        "request_fire_check": False,
        "request_maximum_crack_spacing_check": False,
    }


def deflection_request():
    return basis() | {
        "operation": "DEFLECTION_LIMITS",
        "method": "SUPPLIED_FINAL_DEFLECTIONS",
        "action_basis": "SERVICE_UNFACTORED",
        "reference_level": "AS_CAST_SUPPORTS",
        "effective_span_mm": 6000.0,
        "final_all_effects_deflection_mm": 18.0,
        "after_partitions_finishes_deflection_mm": 10.0,
        "includes_creep_shrinkage_temperature": True,
        "external_calculation_reference": "SAMPLE supplied numbers, not an analysis",
    }


def quantities(run):
    return {q.name: q.value for q in run.result.quantities}


def checks(run):
    return {c.name: c for c in run.result.checks}
