"""Independent M1 inputs/quadrature from documented primitives. Units: N, mm, N/mm².

No production kernel, curve, registry or units helper is imported. These are test
oracles for the explicitly chosen PUBLIC TEACHING DRAFT, not verified standard data.
See docs/research/M1_DRAFT_DESIGN_BASIS.md for derivations and source limits.
"""

from __future__ import annotations

from fractions import Fraction


def beam_request() -> dict:
    """Fresh explicit test request, not application defaults. Units: field suffixes."""
    return {
        "calculation_label": "SAMPLE analytical test, NOT a building",
        "operation": "DESIGN",
        "reinforcement_policy": "SINGLE_ONLY",
        "source_basis": "PUBLIC_TEACHING_DRAFT",
        "acknowledge_unverified": True,
        "method": "CONTINUOUS_STRAIN_COMPATIBILITY",
        "action_basis": "FACTORED_ULS",
        "geometry": {
            "web_width_mm": 300.0,
            "overall_depth_mm": 550.0,
            "top_centroid_from_top_mm": 50.0,
            "bottom_centroid_from_bottom_mm": 50.0,
            "flange": None,
        },
        "materials": {
            "fck_n_mm2": 25.0,
            "steel_grade": "Fe415",
            "steel_curve": "REPRESENTATIVE_COLD_WORKED",
        },
        "factored_moment_kn_m": 120.0,
        "axial_force_kn": 0.0,
    }


def flange_input() -> dict:
    """An explicitly hypothetical integral flange with coupling evidence. Units: mm, mm²/m."""
    return {
        "kind": "T",
        "face": "TOP",
        "thickness_mm": 100.0,
        "actual_width_mm": 1000.0,
        "zero_moment_distance_mm": 6000.0,
        "width_rule": "SLAB_BEAM",
        "composite_action_confirmed": True,
        "slab_main_parallel_to_beam": True,
        "main_steel_mm2_per_m": 800.0,
        "transverse_steel_mm2_per_m": 500.0,
    }


def assessment(request: dict, *, top: float, bottom: float) -> dict:
    """Change operation explicitly without mutating an input fixture. Units: areas mm²."""
    result = dict(request)
    result.pop("reinforcement_policy")
    return result | {"operation": "ASSESS", "reinforcement": {"top_mm2": top, "bottom_mm2": bottom}}


def limiting_ratio(fy: int) -> float:
    """Independent rational arithmetic from strain compatibility. Units: 1."""
    cu = Fraction(7, 2000)
    minimum_tension = Fraction(fy) / (Fraction(23, 20) * 200000) + Fraction(1, 500)
    return float(cu / (cu + minimum_tension))


def rectangular_reference(x: float, width: float, fck: float, d: float) -> tuple[float, float]:
    """Integrated rectangle: C/peak=17bx/21, Q/peak=33bx²/98. Units: N, N mm."""
    peak = float(Fraction(223, 500)) * fck
    force = peak * width * x * float(Fraction(17, 21))
    first_moment = peak * width * x * x * float(Fraction(33, 98))
    return force, force * d - first_moment


def quadrature_reference(
    x: float, *, bw: float, bf: float, thickness: float, fck: float, d: float
) -> tuple[float, float]:
    """Independent Simpson integration, exact on each quadratic/cubic piece. Units: N, N mm.

    The production algorithm uses antiderivatives, not this quadrature. Width and
    constitutive discontinuity points are split before evaluating the polynomial.
    """
    boundaries = sorted({0.0, 3 * x / 7, min(thickness, x), x})

    def stress(y: float) -> float:
        """Independent NPTEL constitutive formula. Units: N/mm²."""
        relative_strain = 7 * (1 - y / x) / 4
        if relative_strain >= 1:
            return 0.446 * fck
        return 0.446 * fck * (1 - (1 - relative_strain) ** 2)

    force = moment = 0.0
    for index in range(len(boundaries) - 1):
        left, right = boundaries[index : index + 2]
        middle = (left + right) / 2
        width = bf if middle < thickness else bw
        weight = width * (right - left) / 6
        force += weight * (stress(left) + 4 * stress(middle) + stress(right))
        moment += weight * (
            stress(left) * (d - left)
            + 4 * stress(middle) * (d - middle)
            + stress(right) * (d - right)
        )
    return force, moment


def compression_reference(strain: float, fy: float) -> float:
    """Independent interpolation using N02 primitive ratios/proof strains. Units: N/mm²."""
    sign = -1 if strain < 0 else 1
    strain = abs(strain)
    design_yield = fy / 1.15
    ratios = [0.8, 0.85, 0.9, 0.95, 0.975, 1.0]
    inelastic = [0, 0.0001, 0.0003, 0.0007, 0.001, 0.002]
    abscissae = [ratios[i] * design_yield / 200000 + inelastic[i] for i in range(6)]
    if strain <= abscissae[0]:
        return sign * 200000 * strain
    for index in range(1, 6):
        if strain <= abscissae[index]:
            left, right = abscissae[index - 1], abscissae[index]
            t = (strain - left) / (right - left)
            return sign * design_yield * ((1 - t) * ratios[index - 1] + t * ratios[index])
    return sign * design_yield
