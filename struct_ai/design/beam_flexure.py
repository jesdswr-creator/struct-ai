"""Continuous draft beam flexure; no analysis backend or LLM. Units: internally N, mm."""

from __future__ import annotations

import math
from collections.abc import Callable
from dataclasses import dataclass

from struct_ai import __version__
from struct_ai.checks import CheckResult
from struct_ai.codes.registry import CodeRegistry
from struct_ai.design.beam_materials import ConcreteLaw, FlexureData, SteelLaw
from struct_ai.design.beam_models import (
    BeamConstitutiveParameters,
    BeamFlexureAssessmentInput,
    BeamFlexureDesignInput,
    BeamFlexureResult,
    BeamFlexureRun,
    BeamLimits,
    BeamReinforcement,
    BeamRequest,
    BeamSectionState,
    BeamSizing,
)
from struct_ai.exceptions import InputOutOfRange, ScopeRefusal, SolverFailure
from struct_ai.serialization import content_hash
from struct_ai.units import kn_m_to_n_mm, n_mm_to_kn_m

# COMPUTATIONAL parameters, not engineering code values or pass/fail tolerances.
ROOT_MAX_ITERATIONS = 128
ROOT_RELATIVE_X_BRACKET = 1e-13
EQUILIBRIUM_RELATIVE_BUDGET = 1e-9
SIZING_MOMENT_RELATIVE_RESERVE = 1e-9
SIZING_X_RELATIVE_RESERVE = 1e-8

DRAFT_NOTICE = "DRAFT: must be reviewed and sealed by a licensed structural engineer."


def _check(name: str, clause: str, demand: float, capacity: float, units: str) -> CheckResult:
    """Form an unrounded check without a passing tolerance. Units: `units`."""
    return CheckResult(
        name=name,
        clause=clause,
        demand=demand,
        capacity=capacity,
        ratio=demand / capacity,
        ok=demand <= capacity,
        units=units,
    )


def _root(function: Callable[[float], float], upper: float) -> float:
    """Return upper endpoint of a certified negative/positive bracket. Units: root in mm.

    Callers establish the analytical negative limit at zero, avoiding division there.
    The returned upper endpoint is not a clamped engineering result. Invalid brackets
    and failure to converge raise; no guessed root is returned.
    """
    f_upper = function(upper)
    if not math.isfinite(f_upper) or f_upper < 0:
        raise SolverFailure(
            "Section root has no admissible upper bracket.",
            clause="M1 NUMERICAL ROOT DOMAIN (not a code allowance)",
            value={"upper_mm": upper, "residual": f_upper},
            limit="finite nonnegative upper residual",
        )
    if f_upper == 0:
        return upper
    lower = 0.0
    scale = upper
    for _ in range(ROOT_MAX_ITERATIONS):
        middle = (lower + upper) / 2
        residual = function(middle)
        if not math.isfinite(residual):
            raise SolverFailure(
                "Non-finite section residual.",
                clause="M1 NUMERICAL ROOT DOMAIN (not a code allowance)",
                value=residual,
                limit="finite force or moment equilibrium residual",
            )
        if residual == 0:
            return middle
        if residual < 0:
            lower = middle
        else:
            upper = middle
        if upper - lower <= scale * ROOT_RELATIVE_X_BRACKET:
            return upper
    raise SolverFailure(
        "Section root did not converge; no capacity was published.",
        clause="M1 NUMERICAL ROOT CONVERGENCE (not a code allowance)",
        value={"lower_mm": lower, "upper_mm": upper},
        limit={"relative_bracket": ROOT_RELATIVE_X_BRACKET, "iterations": ROOT_MAX_ITERATIONS},
    )


@dataclass(frozen=True)
class ConcreteBlock:
    """Gross concrete compression, before steel displacement. Units: N, N mm."""

    force: float
    first_moment: float


class SectionCalculation:
    """Run-local calculation; clients use engine_service. Units: N, mm."""

    def __init__(self, request: BeamRequest, registry: CodeRegistry) -> None:
        """Validate basis/scope then resolve only required coefficients. Units: N, mm, N/mm²."""
        self.request = request
        self.tracker = registry.new_tracker()
        self.data = FlexureData(registry, self.tracker)
        if request.source_basis == "CURRENT_AMENDED_CODE":
            registry.require("is456_2000.applicability.current_amendment_review", self.tracker)
            raise NotImplementedError(
                "Current-amended-code compliance is not implemented, even if a catalogue is edited."
            )
        if request.axial_force_kn != 0:
            raise ScopeRefusal(
                "M1 is pure beam bending; axial action must not be silently ignored.",
                clause="M1 BEAM-SECTION SCOPE (not a code limit)",
                value={"axial_force_kn": request.axial_force_kn},
                limit={"axial_force_kn": 0},
            )
        self.geometry = request.geometry
        self.compression_face = "TOP" if request.factored_moment_kn_m > 0 else "BOTTOM"
        self.tension_face = "BOTTOM" if self.compression_face == "TOP" else "TOP"
        if self.compression_face == "TOP":
            self.d = self.geometry.overall_depth_mm - self.geometry.bottom_centroid_from_bottom_mm
            self.dp = self.geometry.top_centroid_from_top_mm
        else:
            self.d = self.geometry.overall_depth_mm - self.geometry.top_centroid_from_top_mm
            self.dp = self.geometry.bottom_centroid_from_bottom_mm
        self.concrete = ConcreteLaw.load(self.data, request.materials.fck_n_mm2)
        self.steel = SteelLaw.load(self.data, request.materials.steel_grade)
        self.x_ratio = self.concrete.ultimate_strain / (
            self.concrete.ultimate_strain + self.steel.minimum_tension_strain
        )
        self.x_limit = self.x_ratio * self.d
        # Construct a conservative REPRESENTABLE limit, not a relaxed check or input clamp.
        while self.tension_strain(self.x_limit) < self.steel.minimum_tension_strain:
            self.x_limit = math.nextafter(self.x_limit, 0)
        self.participation_checks: list[CheckResult] = []
        self.bf = self.geometry.web_width_mm
        self.uncapped_bf: float | None = None
        self.active_flange = False
        self._resolve_flange()
        self.limits = self._limits()

    def tension_strain(self, x: float) -> float:
        """Tension strain magnitude from the active-face geometry. Units: strain."""
        return self.concrete.ultimate_strain * (self.d / x - 1)

    def _resolve_flange(self) -> None:
        """Credit only confirmed compression flanges, with explicit code width caps. Units: mm."""
        flange = self.geometry.flange
        if flange is None or flange.actual_width_mm == self.geometry.web_width_mm:
            return
        if flange.face != self.compression_face:
            # The ordinary negative-moment web-only idealisation needs the flange in tension.
            if self.x_limit >= self.geometry.overall_depth_mm - flange.thickness_mm:
                raise ScopeRefusal(
                    "An unusually deep opposite-face flange may enter the compression zone.",
                    clause="M1 flange-in-tension idealisation; NPTEL N04/N10, not a code limit",
                    value={"flange_thickness_mm": flange.thickness_mm},
                    limit={"less_than_mm": self.geometry.overall_depth_mm - self.x_limit},
                )
            return  # No flange-width or coupling constants are consumed in this path.
        if not flange.composite_action_confirmed:
            raise ScopeRefusal(
                "Compression-flange participation needs explicit integral/bonded-action "
                "confirmation.",
                clause="IS 456:2000 23.1.1(a), secondary N10; unverified",
                value=flange.composite_action_confirmed,
                limit="confirmed integral construction or effective bonding, reviewed by engineer",
            )
        if flange.slab_main_parallel_to_beam:
            if flange.main_steel_mm2_per_m is None or flange.transverse_steel_mm2_per_m is None:
                raise InputOutOfRange(
                    "Parallel main slab steel requires both reinforcement areas for coupling.",
                    clause="IS 456:2000 23.1.1(b), secondary N10; unverified",
                    value=flange.model_dump(mode="json"),
                    limit="explicit positive main and transverse slab areas in mm²/m",
                )
            required = (
                self.data.number("flange.transverse_reinforcement_ratio")
                * flange.main_steel_mm2_per_m
            )
            check = _check(
                "Flange transverse reinforcement",
                "IS 456:2000 23.1.1(b); public draft",
                required,
                flange.transverse_steel_mm2_per_m,
                "mm²/m",
            )
            if not check.ok:
                raise InputOutOfRange(
                    "Flange participation check failed; no flanged capacity was calculated.",
                    clause=check.clause,
                    value=check.model_dump(mode="json"),
                    limit="required transverse reinforcement <= provided transverse reinforcement",
                )
            self.participation_checks.append(check)
        if flange.width_rule == "SLAB_BEAM":
            prefix = flange.kind.lower()
            self.uncapped_bf = (
                self.geometry.web_width_mm
                + flange.zero_moment_distance_mm / self.data.number(f"flange.{prefix}_span_divisor")
                + self.data.number(f"flange.{prefix}_thickness_factor") * flange.thickness_mm
            )
        else:
            numerator = flange.zero_moment_distance_mm
            if flange.kind == "L":
                numerator *= self.data.number("flange.isolated_l_numerator_factor")
            self.uncapped_bf = self.geometry.web_width_mm + numerator / (
                flange.zero_moment_distance_mm / flange.actual_width_mm
                + self.data.number("flange.isolated_denominator_offset")
            )
        # This is the explicitly prescribed lesser-of widths, NOT clamping an invalid input.
        self.bf = min(self.uncapped_bf, flange.actual_width_mm)
        self.active_flange = True

    def concrete_block(self, x: float) -> ConcreteBlock:
        """Integrate the width profile continuously through x=Df. Units: N, N mm."""
        area, first = self.concrete.strip_integrals(x, 0, x)
        force = area * self.geometry.web_width_mm
        moment = first * self.geometry.web_width_mm
        if self.active_flange:
            flange = self.geometry.flange
            assert flange is not None  # Internal invariant established by _resolve_flange.
            flange_area, flange_first = self.concrete.strip_integrals(
                x, 0, min(x, flange.thickness_mm)
            )
            extra_width = self.bf - self.geometry.web_width_mm
            force += flange_area * extra_width
            moment += flange_first * extra_width
        return ConcreteBlock(force, moment)

    def _limits(self) -> BeamLimits:
        """Derive reference coefficients and longitudinal bounds. Units: mm, mm², kN m."""
        a = self.data.number("annex_g.resultant_factor")
        beta = self.data.number("annex_g.centroid_factor")
        block = self.concrete_block(self.x_limit)
        # Rectangular comparison is deliberately separate from the flanged section's limit.
        force_per_width, q_per_width = self.concrete.strip_integrals(self.x_limit, 0, self.x_limit)
        coefficient = (force_per_width * self.d - q_per_width) / (
            self.request.materials.fck_n_mm2 * self.d**2
        )
        return BeamLimits(
            xu_max_over_d=self.x_ratio,
            xu_max_mm=self.x_limit,
            rectangular_annex_g_coefficient=a * self.x_ratio * (1 - beta * self.x_ratio),
            rectangular_integrated_curve_coefficient=coefficient,
            concrete_only_limiting_moment_kn_m=n_mm_to_kn_m(
                block.force * self.d - block.first_moment
            ),
            minimum_tension_steel_mm2=self.data.number(
                "reinforcement.minimum_tension_factor", "N/mm²"
            )
            * self.geometry.web_width_mm
            * self.d
            / self.steel.fy,
            maximum_tension_steel_mm2=self.data.number("reinforcement.maximum_tension_ratio")
            * self.geometry.web_width_mm
            * self.geometry.overall_depth_mm,
            maximum_compression_steel_mm2=self.data.number(
                "reinforcement.maximum_compression_ratio"
            )
            * self.geometry.web_width_mm
            * self.geometry.overall_depth_mm,
        )

    def opposite_stresses(self, x: float) -> tuple[float, float, float]:
        """Compatible opposite-layer strain/stress and displaced concrete. Units: strain, N/mm²."""
        strain = self.concrete.ultimate_strain * (1 - self.dp / x)
        return strain, self.steel.stress(strain), self.concrete.stress(strain)

    def equivalent_tension_area(self, x: float, opposite_area: float) -> float:
        """Area balancing compression at x; tension steel is ductile/yielded. Units: mm²."""
        force = self.concrete_block(x).force
        if opposite_area:
            _, steel_stress, displaced = self.opposite_stresses(x)
            force += opposite_area * (steel_stress - displaced)
        return force / self.steel.design_yield

    def layer_areas(self, tension: float, opposite: float) -> BeamReinforcement:
        """Map active-face areas back to physical top/bottom layers. Units: mm²."""
        if max(tension, opposite) > 100_000:
            raise InputOutOfRange(
                "Required steel exceeds the section service's numerical area domain; revise "
                "section.",
                clause="M1 NUMERICAL AREA DOMAIN (not a code allowance)",
                value={"tension_mm2": tension, "opposite_mm2": opposite},
                limit={"area_per_layer_mm2": 100_000},
            )
        if self.tension_face == "BOTTOM":
            return BeamReinforcement(top_mm2=opposite, bottom_mm2=tension)
        return BeamReinforcement(top_mm2=tension, bottom_mm2=opposite)

    def size(self, request: BeamFlexureDesignInput) -> tuple[BeamReinforcement, BeamSizing]:
        """Size continuous steel, then forward-assess it separately. Units: N, mm, mm²."""
        demand_kn_m = abs(request.factored_moment_kn_m)
        limit_kn_m = self.limits.concrete_only_limiting_moment_kn_m
        opposite_area = 0.0
        governing = "FLEXURE"
        # Decide the boundary in the SAME units as the published capacity and CheckResult.
        # A round-trip conversion must not turn exact endpoint equality into an overload.
        if demand_kn_m <= limit_kn_m:
            reserve_kn_m = min(
                demand_kn_m * SIZING_MOMENT_RELATIVE_RESERVE, (limit_kn_m - demand_kn_m) / 2
            )
            target_kn_m = demand_kn_m + reserve_kn_m
            if target_kn_m == limit_kn_m:
                x = self.x_limit  # Exact public-unit endpoint; no inequality tolerance.
            else:
                target = kn_m_to_n_mm(target_kn_m)

                def moment_residual(x: float) -> float:
                    """Concrete-only moment about the tension layer minus target. Units: N mm."""
                    block = self.concrete_block(x)
                    return block.force * self.d - block.first_moment - target

                x = _root(moment_residual, self.x_limit)
            tension_area = self.equivalent_tension_area(x, 0.0)
        else:
            if request.reinforcement_policy == "SINGLE_ONLY":
                check = _check(
                    "Singly reinforced limiting moment",
                    "IS 456:2000 38.1(f); continuous public-draft strain model",
                    abs(request.factored_moment_kn_m),
                    self.limits.concrete_only_limiting_moment_kn_m,
                    "kN m",
                )
                raise InputOutOfRange(
                    "Singly reinforced limit exceeded; no neutral-axis clamp or resizing "
                    "performed.",
                    clause=check.clause,
                    value=check.model_dump(mode="json"),
                    limit="explicit compression-steel policy or a separately revised section",
                )
            # Small, disclosed computational reserve keeps inversion below the ductility limit.
            x = self.x_limit * (1 - SIZING_X_RELATIVE_RESERVE)
            if self.dp >= x:
                raise InputOutOfRange(
                    "The nominated opposite layer cannot act as compression steel at the sizing "
                    "limit.",
                    clause="38.1 / compatible compression layer; secondary N08 §4.8.4",
                    value={"opposite_layer_depth_mm": self.dp},
                    limit={"less_than_mm": x},
                )
            target_kn_m = demand_kn_m * (1 + SIZING_MOMENT_RELATIVE_RESERVE)
            target = kn_m_to_n_mm(target_kn_m)
            block = self.concrete_block(x)
            _, stress, displaced = self.opposite_stresses(x)
            net = stress - displaced
            if net <= 0:
                raise InputOutOfRange(
                    "Compression steel has no positive net resistance after displaced concrete.",
                    clause="38.1 / net compression-steel force; secondary N08 §4.8.3",
                    value={"net_stress_n_mm2": net},
                    limit="positive net compression stress",
                )
            opposite_area = (target - (block.force * self.d - block.first_moment)) / (
                net * (self.d - self.dp)
            )
            tension_area = (block.force + opposite_area * net) / self.steel.design_yield
            governing = "DOUBLY_REINFORCED"
        adopted_tension = tension_area
        if tension_area < self.limits.minimum_tension_steel_mm2:
            adopted_tension = self.limits.minimum_tension_steel_mm2
            governing = "MINIMUM_TENSION_STEEL"
        sizing = BeamSizing(
            governing=governing,
            tension_area_from_flexure_mm2=tension_area,
            compression_area_from_flexure_mm2=opposite_area,
            moment_sizing_target_kn_m=target_kn_m,
            numerical_moment_reserve_kn_m=target_kn_m - demand_kn_m,
            neutral_axis_sizing_target_mm=x,
        )
        return self.layer_areas(adopted_tension, opposite_area), sizing

    def assess(self, areas: BeamReinforcement) -> tuple[BeamSectionState, tuple[CheckResult, ...]]:
        """Solve actual force balance; over-reinforcement is refused, never capped. Units: N, mm."""
        if self.tension_face == "BOTTOM":
            tension_area, opposite_area = areas.bottom_mm2, areas.top_mm2
        else:
            tension_area, opposite_area = areas.top_mm2, areas.bottom_mm2
        if tension_area == 0:
            raise InputOutOfRange(
                "No reinforcement is present at the designated tension face.",
                clause="M1 positive tension-area domain / IS 456:2000 26.5.1.1",
                value={"tension_area_mm2": tension_area, "tension_face": self.tension_face},
                limit="positive tension area at the actual tension face",
            )
        available_at_limit = self.equivalent_tension_area(self.x_limit, opposite_area)
        if available_at_limit <= 0:
            raise InputOutOfRange(
                "The nominated layers cannot balance a positive tension area within the ductile "
                "domain.",
                clause="38.1 / M1 compatible layer geometry; no positive available capacity",
                value={"available_tension_area_mm2": available_at_limit},
                limit="positive available tension area at the strain-derived limit",
            )
        if tension_area > available_at_limit:
            check = _check(
                "Ductile tension-area limit for supplied opposite steel",
                "IS 456:2000 38.1(f); no over-reinforced clamping",
                tension_area,
                available_at_limit,
                "mm²",
            )
            raise InputOutOfRange(
                "Force equilibrium requires a neutral axis beyond the ductility limit. REVISE "
                "SECTION.",
                clause=check.clause,
                value=check.model_dump(mode="json"),
                limit="tension area <= compatible area at xu,max; no capacity was published",
            )
        x = _root(
            lambda value: self.equivalent_tension_area(value, opposite_area) - tension_area,
            self.x_limit,
        )
        block = self.concrete_block(x)
        strain = steel_stress = None
        displaced = net_force = 0.0
        if opposite_area:
            strain, steel_stress, displaced = self.opposite_stresses(x)
            net_force = opposite_area * (steel_stress - displaced)
        if block.force - opposite_area * displaced <= 0:
            raise InputOutOfRange(
                "Steel displacement leaves no positive concrete compression; revise layer "
                "geometry.",
                clause="M1 smeared-layer geometry domain; not a code allowance",
                value={"net_concrete_force_n": block.force - opposite_area * displaced},
                limit="positive concrete compression after steel displacement",
            )
        tension_force = self.steel.design_yield * tension_area
        residual = block.force + net_force - tension_force
        moment = block.force * self.d - block.first_moment + net_force * (self.d - self.dp)
        numerical_check = _check(
            "Numerical axial equilibrium (not utilisation)",
            "M1 numerical force-balance budget; not an IS-code tolerance",
            abs(residual),
            max(block.force, abs(net_force), tension_force) * EQUILIBRIUM_RELATIVE_BUDGET,
            "N",
        )
        if not numerical_check.ok or moment <= 0:
            raise SolverFailure(
                "Section equilibrium/positive moment verification failed; no result was published.",
                clause=numerical_check.clause,
                value={"check": numerical_check.model_dump(mode="json"), "moment_n_mm": moment},
                limit="passing force balance and positive moment capacity",
            )
        case = "RECTANGULAR"
        flange = self.geometry.flange
        if flange is not None and flange.actual_width_mm > self.geometry.web_width_mm:
            if not self.active_flange:
                case = "FLANGE_IN_TENSION_IGNORED"
            elif x <= flange.thickness_mm:
                case = "NA_IN_FLANGE"
            elif flange.thickness_mm <= x * (
                1 - self.concrete.plateau_strain / self.concrete.ultimate_strain
            ):
                case = "NA_IN_WEB_FLANGE_PLATEAU"
            else:
                case = "NA_IN_WEB_FLANGE_PART_PARABOLIC"
        state = BeamSectionState(
            compression_face=self.compression_face,
            tension_face=self.tension_face,
            effective_depth_mm=self.d,
            opposite_layer_depth_mm=self.dp,
            effective_flange_width_mm=self.bf,
            uncapped_flange_width_mm=self.uncapped_bf,
            flange_width_capped_by_actual=self.uncapped_bf is not None
            and self.bf < self.uncapped_bf,
            compression_case=case,
            neutral_axis_mm=x,
            tensile_strain=self.tension_strain(x),
            opposite_layer_strain=strain,
            tension_steel_stress_n_mm2=self.steel.design_yield,
            opposite_steel_stress_n_mm2=steel_stress,
            displaced_concrete_stress_n_mm2=displaced,
            concrete_force_n=block.force,
            concrete_centroid_mm=block.first_moment / block.force,
            opposite_net_force_n=net_force,
            tension_force_n=tension_force,
            axial_residual_n=residual,
            moment_capacity_kn_m=n_mm_to_kn_m(moment),
        )
        # If the opposite layer is actually in tension, it counts towards maximum tension steel.
        total_tension_area = tension_area + (
            opposite_area if strain is not None and strain < 0 else 0
        )
        checks = (
            *self.participation_checks,
            _check(
                "Flexural moment",
                "IS 456:2000 38.1; integrated public-draft curve",
                abs(self.request.factored_moment_kn_m),
                state.moment_capacity_kn_m,
                "kN m",
            ),
            _check(
                "Neutral-axis ductility limit",
                "IS 456:2000 38.1(f); strain-derived, unrounded",
                x,
                self.x_limit,
                "mm",
            ),
            _check(
                "Minimum tensile strain",
                "IS 456:2000 38.1(f); public draft",
                self.steel.minimum_tension_strain,
                state.tensile_strain,
                "1",
            ),
            _check(
                "Minimum principal tension steel",
                "IS 456:2000 26.5.1.1(a); public draft",
                self.limits.minimum_tension_steel_mm2,
                tension_area,
                "mm²",
            ),
            _check(
                "Maximum tension steel (overall D)",
                "IS 456:2000 26.5.1.1(b); public draft",
                total_tension_area,
                self.limits.maximum_tension_steel_mm2,
                "mm²",
            ),
            _check(
                "Maximum opposite-layer steel (overall D)",
                "IS 456:2000 26.5.1.2; public draft",
                opposite_area,
                self.limits.maximum_compression_steel_mm2,
                "mm²",
            ),
            numerical_check,
        )
        return state, checks


def calculate_beam_flexure(
    request: BeamFlexureDesignInput | BeamFlexureAssessmentInput,
    registry: CodeRegistry,
) -> BeamFlexureRun:
    """Fixed scope/data → optional inverse → forward → checks → audit. Units: field-specific."""
    calculation = SectionCalculation(request, registry)
    sizing = None
    if isinstance(request, BeamFlexureDesignInput):
        areas, sizing = calculation.size(request)
    else:
        areas = request.reinforcement
    state, checks = calculation.assess(areas)
    usage = calculation.tracker.snapshot()
    warnings = (
        *((usage.warning,) if usage.warning else ()),
        "PUBLIC TEACHING DRAFT: current amendments and code compliance are NOT established.",
        DRAFT_NOTICE,
    )
    result = BeamFlexureResult(
        kind="DRAFT_BEAM_FLEXURE",
        analysis_revision="beam-flexure-draft-v1",
        engine_version=__version__,
        building_design_available=False,
        verified_code_compliance=False,
        inputs=request,
        reinforcement=areas,
        sizing=sizing,
        parameters=BeamConstitutiveParameters(
            concrete_peak_factor=calculation.concrete.peak_factor,
            concrete_peak_stress_n_mm2=calculation.concrete.peak_stress,
            concrete_plateau_strain=calculation.concrete.plateau_strain,
            concrete_ultimate_strain=calculation.concrete.ultimate_strain,
            steel_yield_strength_n_mm2=calculation.steel.fy,
            steel_elastic_modulus_n_mm2=calculation.steel.elastic_modulus,
            steel_partial_factor=calculation.steel.partial_factor,
            steel_design_yield_n_mm2=calculation.steel.design_yield,
            minimum_tensile_strain=calculation.steel.minimum_tension_strain,
        ),
        limits=calculation.limits,
        section=state,
        checks=checks,
        code_usage=usage,
        status="DRAFT_SECTION_CHECKS_PASS" if all(c.ok for c in checks) else "REVISE_SECTION",
        warnings=warnings,
        limitations=(
            "Single section, one signed already-factored pure bending action, no building "
            "analysis.",
            "Continuous NPTEL parabolic-rectangular concrete uses the catalogued rounded peak; "
            "NOT the Annex G equivalent stress block. Its reference coefficient is reported "
            "separately.",
            "Steel uses fy/gamma and the explicitly selected representative cold-worked curve; "
            "no inferred TMT/manufacturer curve and no SP16 table digitisation.",
            "Flange coupling confirmation and zero-moment distance are caller responsibilities. "
            "No slab design, local flange bending, torsion or out-of-plane response is checked.",
            "No shear, torsion, anchorage, cover, spacing, serviceability, seismic/ductile "
            "detailing, "
            "bar selection, redistribution or construction-document approval.",
            "Continuous areas are NOT a reinforcement schedule. Section dimensions are never "
            "resized.",
            "Sizing reserves: nominal moment reserve 1e-9 relative; double-steel neutral axis 1e-8 "
            "below its "
            "limit. These are disclosed numerical reserves, NOT passing tolerances or code "
            "factors.",
            "No controlled or amendment-complete standard was reviewed. Current-code requests "
            "are blocked.",
        ),
    )
    return BeamFlexureRun(result=result, result_hash=content_hash(result))
