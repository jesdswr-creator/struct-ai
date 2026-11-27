"""Independent closed-form diagnostic path; never calls OpenSees. Units: kN, m, rad."""

from __future__ import annotations

from struct_ai.arms.diagnostic_models import DiagnosticInput, SolverObservations
from struct_ai.checks import CheckResult

# Computational comparison tolerances, NOT engineering acceptance/code limits.
# Nonzero reference responses use a relative 1e-9 numerical error budget.
# The exactly-zero vertical reaction uses an absolute 1e-9 kN error budget.
RELATIVE_NUMERICAL_TOLERANCE = 1e-9
ZERO_REACTION_TOLERANCE_KN = 1e-9


def analytical_reference(inputs: DiagnosticInput) -> SolverObservations:
    """Integrate EI*x''(y)=P*(L-y), with fixed-base conditions. Units: kN, m, rad.

    x(L)=P*L³/(3*EI); the global Z rotation is -x'(L)=-P*L²/(2*EI).
    Global equilibrium gives Rx=-P, Ry=0, Mz=P*L. This path does not import or
    assemble the numerical model, and uses no Indian Standard constants.
    """
    rigidity = inputs.elastic_modulus_kn_m2 * inputs.inertia_m4
    return SolverObservations(
        tip_displacement_m=inputs.force_kn * inputs.length_m**3 / (3 * rigidity),
        tip_rotation_rad=-inputs.force_kn * inputs.length_m**2 / (2 * rigidity),
        support_fx_kn=-inputs.force_kn,
        support_fy_kn=0.0,
        support_mz_kn_m=inputs.force_kn * inputs.length_m,
    )


def verify_observations(
    actual: SolverObservations, reference: SolverObservations
) -> tuple[CheckResult, ...]:
    """Compare signed observations without correcting them. Units: each check's units."""
    comparisons = (
        ("tip_displacement_m", "Tip displacement error", "m", "ANALYTIC: PL³/(3EI)"),
        ("tip_rotation_rad", "Tip rotation error", "rad", "ANALYTIC: -PL²/(2EI)"),
        ("support_fx_kn", "Horizontal equilibrium error", "kN", "STATICS: Rx + P = 0"),
        ("support_fy_kn", "Vertical equilibrium error", "kN", "STATICS: Ry = 0"),
        ("support_mz_kn_m", "Moment equilibrium error", "kN m", "STATICS: Mz - PL = 0"),
    )
    checks: list[CheckResult] = []
    for field, name, units, identity in comparisons:
        expected = getattr(reference, field)
        capacity = (
            ZERO_REACTION_TOLERANCE_KN
            if field == "support_fy_kn"
            else abs(expected) * RELATIVE_NUMERICAL_TOLERANCE
        )
        demand = abs(getattr(actual, field) - expected)
        checks.append(
            CheckResult(
                name=name,
                ok=demand <= capacity,
                clause=f"{identity}; numerical diagnostic, NOT an IS-code check",
                demand=demand,
                capacity=capacity,
                ratio=demand / capacity,
                units=units,
            )
        )
    return tuple(checks)
