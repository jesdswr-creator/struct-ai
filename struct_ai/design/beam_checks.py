"""Deterministic M2 component assessments; clients use engine_service. Units: N, mm internally."""

from __future__ import annotations

import math
from itertools import pairwise

from pydantic import ValidationError

from struct_ai import __version__
from struct_ai.checks import CheckResult
from struct_ai.codes.registry import CodeRegistry, CodeUseTracker
from struct_ai.design.beam_check_models import (
    BeamCheckInput,
    BeamCheckResult,
    BeamCheckRun,
    BeamShearTorsionInput,
    CoverSpacingInput,
    DeflectionCheckInput,
    DevelopmentLengthInput,
    TraceQuantity,
)
from struct_ai.design.beam_flexure import DRAFT_NOTICE, calculate_beam_flexure
from struct_ai.design.beam_materials import FlexureData
from struct_ai.design.beam_models import BeamFlexureAssessmentInput, BeamFlexureRun
from struct_ai.exceptions import CodeDataError, InputOutOfRange, ScopeRefusal
from struct_ai.serialization import content_hash
from struct_ai.units import kn_m_to_n_mm, kn_to_n, n_to_kn


class BeamCheckData:
    """Only cited data, with run-local use tracking and unit enforcement. Units: per record."""

    def __init__(self, registry: CodeRegistry, tracker: CodeUseTracker) -> None:
        """Bind exactly one catalogue revision. Units: none."""
        self.registry, self.tracker = registry, tracker

    def number(self, key: str, units: str = "1") -> float:
        """Require positive finite code values; never fall back. Units: `units`."""
        value = self.registry.require(
            "is456_2000.beam_checks." + key, self.tracker, expected_units=units
        )
        if value <= 0:
            raise CodeDataError(
                f"Nonpositive beam-check code value: {key}",
                clause=f"CODE DATA DOMAIN: {key}",
                value=value,
                limit=f"positive {units}",
            )
        return value

    def concrete_grade(self, strength: float) -> str:
        """No interpolation between grades or extrapolation above M40. Units: N/mm²."""
        key = f"m{strength:g}"
        if key not in ("m20", "m25", "m30", "m35", "m40"):
            raise InputOutOfRange(
                "M2 shear tables require a discrete supported concrete grade.",
                clause="IS 456:2000 Tables 19/20; restricted M2 draft domain",
                value={"fck_n_mm2": strength},
                limit="M20, M25, M30, M35 or M40; no interpolation",
            )
        stated = self.number(f"concrete.{key}.strength", "N/mm²")
        if stated != strength:
            raise CodeDataError(
                "Concrete table heading disagrees with selected strength.",
                clause="Tables 19/20 grade identity",
                value=stated,
                limit=strength,
            )
        return key

    def shear_strength(self, grade: str, percentage: float) -> tuple[float, float, float]:
        """
        Validate selected column; interpolate, retaining labelled end rows. Units:
        N/mm², %, %.
        """
        rows = tuple(
            (
                self.number(f"shear.table19.p{i:02}.percent", "%"),
                self.number(f"shear.table19.p{i:02}.{grade}", "N/mm²"),
            )
            for i in range(13)
        )
        maximum = self.number(f"shear.table20.{grade}", "N/mm²")
        if not all(a[0] < b[0] and a[1] <= b[1] for a, b in pairwise(rows)) or any(
            y > maximum for _, y in rows
        ):
            raise CodeDataError(
                "Table 19 axis/selected column is not ordered or exceeds Table 20.",
                clause="40.2.1/40.2.3 / Tables 19 and 20",
                value=rows,
                limit="strictly increasing axis, nondecreasing positive strengths <= tau_cmax",
            )
        if not math.isfinite(percentage) or percentage < 0:
            raise InputOutOfRange(
                "Invalid tensile percentage for shear.",
                clause="40.2.1 / Table 19",
                value=percentage,
                limit="finite nonnegative actual percentage",
            )
        if percentage <= rows[0][0]:
            return rows[0][1], rows[0][0], rows[0][0]
        if percentage >= rows[-1][0]:
            return rows[-1][1], rows[-1][0], rows[-1][0]
        for (left, a), (right, b) in pairwise(rows):
            if percentage <= right:
                if percentage == right:
                    return b, right, right
                return a + (b - a) * (percentage - left) / (right - left), left, right
        raise AssertionError("A validated in-domain percentage must be bracketed")


class ComponentCalculation:
    """One request, one catalogue, one trace; no GUI/LLM imports. Units: N, mm and suffixes."""

    def __init__(self, request: BeamCheckInput, registry: CodeRegistry) -> None:
        """Fail closed on current-code requests before any calculation. Units: none."""
        self.request, self.registry = request, registry
        self.tracker = registry.new_tracker()
        self.data = BeamCheckData(registry, self.tracker)
        self.quantities: list[TraceQuantity] = []
        self.checks: list[CheckResult] = []
        self.flexure: list[BeamFlexureRun] = []
        self.limits: list[str] = []
        if request.source_basis == "CURRENT_AMENDED_CODE":
            registry.require("is456_2000.applicability.current_amendment_review", self.tracker)
            raise NotImplementedError("Current-amended-code compliance is not implemented")

    def quantity(self, name: str, value: float, units: str, basis: str) -> None:
        """Record unrounded results; reporting will not recompute them. Units: `units`."""
        self.quantities.append(TraceQuantity(name=name, value=value, units=units, basis=basis))

    def check(self, name: str, demand: float, capacity: float, units: str, clause: str) -> None:
        """Literal upper-bound comparison, no passing tolerance. Units: `units`."""
        self.checks.append(
            CheckResult(
                name=name,
                demand=demand,
                capacity=capacity,
                ratio=demand / capacity,
                ok=demand <= capacity,
                units=units,
                clause=clause,
            )
        )

    def flexure_at(self, request: BeamShearTorsionInput, moment: float) -> None:
        """Forward-assess actual principal layers at a labelled equivalent demand. Units: kN m."""
        payload = request.flexure.model_dump()
        payload["factored_moment_kn_m"] = moment
        payload["calculation_label"] += " / M2 equivalent flexure demand"
        try:
            assessment = BeamFlexureAssessmentInput.model_validate(payload)
        except ValidationError as error:
            raise InputOutOfRange(
                "Equivalent bending demand lies outside the validated M1 input domain.",
                clause="41.4.2 / M1 software domain, not a code allowance",
                value={"equivalent_moment_kn_m": moment},
                limit=error.errors(include_url=False),
            ) from error
        run = calculate_beam_flexure(assessment, self.registry)
        self.flexure.append(run)
        for check in run.result.checks:
            self.checks.append(
                check.model_copy(update={"name": f"Flexure {len(self.flexure)} / {check.name}"})
            )
        for record in run.result.code_usage.constants:
            self.tracker.capture(run.result.code_usage.data_digest, record)

    def shear_torsion(self, request: BeamShearTorsionInput) -> None:
        """Assess vertical stirrups, equivalent bending and side faces. Units: N, mm internally."""
        if not (
            request.critical_section_actions_confirmed
            and request.longitudinal_anchorage_and_continuity_confirmed
            and request.stirrups.enclosure_and_anchorage_confirmed
        ):
            raise ScopeRefusal(
                "Critical section, longitudinal continuity and stirrup anchorage must be "
                "confirmed.",
                clause="22.6.2 / 26.2 / 26.5.1.4 / Table 19 note",
                value=request.model_dump(mode="json"),
                limit="explicit confirmations; no automated support/action/anchorage inference",
            )
        f = request.flexure
        if f.axial_force_kn != 0:
            raise ScopeRefusal(
                "Axial action is outside M2 beam scope.",
                clause="M2 no-axial scope",
                value=f.axial_force_kn,
                limit="0 kN",
            )
        g = f.geometry
        b, depth = g.web_width_mm, g.overall_depth_mm
        d = depth - (
            g.bottom_centroid_from_bottom_mm
            if f.factored_moment_kn_m > 0
            else g.top_centroid_from_top_mm
        )
        steel = (
            f.reinforcement.bottom_mm2 if f.factored_moment_kn_m > 0 else f.reinforcement.top_mm2
        )
        grade = self.data.concrete_grade(f.materials.fck_n_mm2)
        percentage = 100 * steel / (b * d)
        tau_c, low, high = self.data.shear_strength(grade, percentage)
        tau_max = self.data.number(f"shear.table20.{grade}", "N/mm²")
        v, t = (
            kn_to_n(abs(request.factored_shear_kn)),
            kn_m_to_n_mm(abs(request.factored_torsion_kn_m)),
        )
        # Retain the action in its public units; kN -> N -> stress may erase an overload.
        equivalent_v_kn = abs(request.factored_shear_kn)
        mt = 0.0
        if t:
            if g.flange is not None:
                raise ScopeRefusal(
                    "Flanged torsion needs specialist validation; not approximated here.",
                    clause="41.1 / restricted M2 torsion scope",
                    value=g.flange.kind,
                    limit="solid rectangular beam for nonzero torsion",
                )
            tg = request.torsion_geometry
            corner_depth = depth - g.top_centroid_from_top_mm - g.bottom_centroid_from_bottom_mm
            if (
                tg is None
                or request.stirrups.effective_legs != 2
                or not tg.closed_rectangular_stirrups_and_corner_bars_confirmed
            ):
                raise ScopeRefusal(
                    "Torsion requires a confirmed two-legged closed corner-bar cage.",
                    clause="41.4.3 / 26.5.1.7",
                    value=tg,
                    limit="two effective legs and explicit closed-cage geometry",
                )
            if not (
                tg.corner_bar_width_mm < tg.stirrup_centreline_width_mm
                and tg.stirrup_centreline_width_mm + request.stirrups.diameter_mm < b
                and corner_depth < tg.stirrup_centreline_depth_mm
                and tg.stirrup_centreline_depth_mm + request.stirrups.diameter_mm < depth
            ):
                raise InputOutOfRange(
                    "Torsion cage dimensions do not enclose the principal corner bars.",
                    clause="41.4.3 / physical b1,d1,x1,y1 geometry",
                    value=tg.model_dump(),
                    limit={
                        "web_width_mm": b,
                        "overall_depth_mm": depth,
                        "corner_bar_depth_mm": corner_depth,
                    },
                )
            equivalent_v_kn += n_to_kn(self.data.number("torsion.equivalent_shear_factor") * t / b)
            mt = (
                abs(request.factored_torsion_kn_m)
                * (1 + depth / b)
                / self.data.number("torsion.equivalent_moment_divisor")
            )
        maximum_shear_kn = n_to_kn(tau_max * b * d)
        # Exact published endpoint, not an inequality tolerance or a demand clamp.
        tau_ve = (
            tau_max if equivalent_v_kn == maximum_shear_kn else kn_to_n(equivalent_v_kn) / (b * d)
        )
        self.check(
            "Maximum equivalent shear force (public units)",
            equivalent_v_kn,
            maximum_shear_kn,
            "kN",
            "40.2.3 / 41.3.1 / Table 20; direct public-action comparison",
        )
        original_fy = (
            self.data.number("steel.fe250.yield_strength", "N/mm²")
            if request.stirrups.steel_grade == "Fe250"
            else FlexureData(self.registry, self.tracker).number(
                f"steel.{request.stirrups.steel_grade.lower()}.yield_strength", "N/mm²"
            )
        )
        credited_fy = min(original_fy, self.data.number("shear.maximum_credited_fy", "N/mm²"))
        stress = self.data.number("steel.design_stress_factor") * credited_fy
        asv = request.stirrups.effective_legs * math.pi * request.stirrups.diameter_mm**2 / 4
        provided_rate = asv / request.stirrups.spacing_mm
        minimum_rate = self.data.number("shear.minimum_stress", "N/mm²") * b / stress
        shear_rate = (tau_ve - tau_c) * b / stress if tau_ve > tau_c else 0.0
        maximum_spacing = min(
            self.data.number("shear.maximum_spacing_depth_factor") * d,
            self.data.number("shear.maximum_spacing", "mm"),
        )
        self.check(
            "Maximum equivalent shear stress",
            tau_ve,
            tau_max,
            "N/mm²",
            "40.2.3 / 41.3.1 / Table 20",
        )
        self.check(
            "Minimum vertical stirrup rate", minimum_rate, provided_rate, "mm²/mm", "26.5.1.6"
        )
        self.check(
            "Equivalent shear stirrup rate", shear_rate, provided_rate, "mm²/mm", "40.4 / 41.4.3"
        )
        self.check(
            "Vertical stirrup spacing",
            request.stirrups.spacing_mm,
            maximum_spacing,
            "mm",
            "26.5.1.5",
        )
        for name, value, unit, clause in (
            ("effective_depth", d, "mm", "active physical tension layer"),
            ("tensile_steel_percentage", percentage, "%", "Table 19: 100Ast/(bw*d)"),
            ("table19_lower_row", low, "%", "40.2.1 / Table 19"),
            ("table19_upper_row", high, "%", "40.2.1 / Table 19"),
            ("concrete_shear_strength", tau_c, "N/mm²", "40.2.1 / Table 19"),
            ("equivalent_shear", equivalent_v_kn, "kN", "41.3.1; public-action units"),
            ("stirrup_area", asv, "mm²", "geometry: effective_legs*pi*diameter²/4"),
            ("stirrup_input_yield", original_fy, "N/mm²", "declared steel grade"),
            ("stirrup_credited_yield", credited_fy, "N/mm²", "40.4 / explicit fy ceiling"),
            ("stirrup_design_stress", stress, "N/mm²", "40.4 / rounded 0.87 formula, not M1 law"),
            ("torsion_equivalent_moment", mt, "kN m", "41.4.2 / uses overall D"),
        ):
            self.quantity(name, value, unit, clause)
        if t:
            torsion_rate = t / (tg.corner_bar_width_mm * corner_depth * stress) + v / (
                self.data.number("torsion.transverse_shear_divisor") * corner_depth * stress
            )
            x1, y1 = sorted((tg.stirrup_centreline_width_mm, tg.stirrup_centreline_depth_mm))
            limit_spacing = min(
                x1,
                (x1 + y1) / self.data.number("torsion.spacing_sum_divisor"),
                self.data.number("shear.maximum_spacing", "mm"),
            )
            self.check(
                "Combined torsion/shear stirrup rate",
                torsion_rate,
                provided_rate,
                "mm²/mm",
                "41.4.3",
            )
            self.check(
                "Closed torsion stirrup spacing",
                request.stirrups.spacing_mm,
                limit_spacing,
                "mm",
                "26.5.1.7(a)",
            )
            self.quantity(
                "corner_bar_depth",
                corner_depth,
                "mm",
                "actual two-layer centroids; d1 not effective d",
            )
        threshold_key = "depth_with_torsion" if t else "depth_without_torsion"
        if depth > self.data.number("side_face." + threshold_key, "mm"):
            if request.side_faces is None:
                raise InputOutOfRange(
                    "Required side-face steel is not supplied.",
                    clause="26.5.1.3 / 26.5.1.7(b)",
                    value={"overall_depth_mm": depth},
                    limit="explicit separate face areas and spacing",
                )
            face_required = self.data.number("side_face.total_web_ratio") * b * depth / 2
            face_spacing = min(b, self.data.number("side_face.maximum_spacing", "mm"))
            self.check(
                "Left side-face reinforcement",
                face_required,
                request.side_faces.left_area_mm2,
                "mm²",
                "26.5.1.3 / overall bw*D",
            )
            self.check(
                "Right side-face reinforcement",
                face_required,
                request.side_faces.right_area_mm2,
                "mm²",
                "26.5.1.3 / overall bw*D",
            )
            self.check(
                "Side-face spacing",
                request.side_faces.maximum_spacing_mm,
                face_spacing,
                "mm",
                "26.5.1.3",
            )
        primary = math.copysign(abs(f.factored_moment_kn_m) + mt, f.factored_moment_kn_m)
        self.quantity(
            "primary_equivalent_moment",
            primary,
            "kN m",
            "41.4.2; conservative equivalent-moment policy for all nonzero torsion",
        )
        self.flexure_at(request, primary)
        if mt > abs(f.factored_moment_kn_m):
            opposite = -math.copysign(mt - abs(f.factored_moment_kn_m), f.factored_moment_kn_m)
            self.quantity(
                "opposite_equivalent_moment",
                opposite,
                "kN m",
                "41.4.2 / opposite physical tension face",
            )
            # Tiny nonzero equivalent actions may fall outside M1's numerical domain; refuse,
            # never silently remove the opposite-face check or round the action to zero.
            self.flexure_at(request, opposite)
        self.limits.extend(
            (
                "One caller-confirmed critical station, uniform depth, no axial action, "
                "enhancement or curtailment; no IS 13920 capacity design.",
                "Torsion: rectangular two-legged closed cage only; equivalent-moment and "
                "transverse-torsion checks are retained for every nonzero torsion, even below "
                "tau_c.",
                "M1 principal-layer checks do not credit side-face steel; all cage, continuity "
                "and anchorage confirmations remain caller responsibilities.",
                "No bar selection, crack control, fire, full anchorage, service deflection or "
                "complete-member approval is performed by this operation.",
            )
        )

    def development(self, request: DevelopmentLengthInput) -> None:
        """Compare actual straight anchorage with force-equilibrium Ld. Units: mm, N/mm²."""
        data = FlexureData(self.registry, self.tracker)
        fy = data.number(f"steel.{request.steel_grade.lower()}.yield_strength", "N/mm²")
        allowed_stress = fy / data.number("steel.partial_factor")
        if request.design_bar_stress_n_mm2 > allowed_stress:
            raise InputOutOfRange(
                "Bar stress exceeds the supported M1 design-yield basis.",
                clause="38.1(e) / supplied stress domain",
                value=request.design_bar_stress_n_mm2,
                limit={"maximum_n_mm2": allowed_stress},
            )
        bond = self.data.number(f"bond.plain_tension.{request.concrete_grade.lower()}", "N/mm²")
        bond *= self.data.number("bond.deformed_multiplier")
        if request.stress_state == "COMPRESSION":
            bond *= self.data.number("bond.compression_multiplier")
        # Four is the circle area/perimeter ratio, not a remembered code coefficient.
        required = request.bar_diameter_mm * request.design_bar_stress_n_mm2 / (4 * bond)
        if request.equal_diameter_bundle_count > 1:
            required *= self.data.number(
                f"bond.bundle_{request.equal_diameter_bundle_count}_multiplier"
            )
        self.quantity(
            "design_bond_stress", bond, "N/mm²", "26.2.1.1; multiplicative bond-stress increases"
        )
        self.quantity(
            "required_straight_development_length",
            required,
            "mm",
            "26.2.1/26.2.1.2; force equilibrium and bundle factor",
        )
        self.check(
            "Straight development length",
            required,
            request.available_straight_length_mm,
            "mm",
            "26.2.1 / 26.2.1.2",
        )
        self.limits.append(
            "Ld only for declared IS 1786 deformed equal-diameter bars. No bend/hook credit, "
            "lap, support M/V, bundle-layout, joint anchorage or seismic/confinement approval."
        )

    def cover_spacing(self, request: CoverSpacingInput) -> None:
        """Partial base-cover and minimum-clear-spacing checks. Units: mm."""
        if request.request_fire_check:
            self.data.number("cover.fire_table16a", "mm")
            raise NotImplementedError(
                "Fire-cover workflow is not implemented even if a scalar is filled"
            )
        if request.request_maximum_crack_spacing_check:
            self.data.number("spacing.maximum_table15", "mm")
            raise NotImplementedError("Maximum crack-spacing workflow is not implemented")
        if request.number_of_rows > 1 and not request.rows_vertically_aligned:
            raise ScopeRefusal(
                "Multiple rows must be vertically aligned in this spacing route.",
                clause="26.3.2(c)",
                value=False,
                limit="confirmed aligned, nonbundled beam bars",
            )
        required_cover = max(
            request.largest_bar_diameter_mm,
            self.data.number("cover." + request.exposure.lower(), "mm"),
        )
        horizontal = max(
            request.largest_bar_diameter_mm,
            request.nominal_maximum_aggregate_mm
            + self.data.number("spacing.horizontal_aggregate_addition", "mm"),
        )
        self.check(
            "Base durability and bar-diameter cover",
            required_cover,
            request.nominal_cover_to_outermost_steel_mm,
            "mm",
            "26.4.1/26.4.2 / Table 16; no reductions",
        )
        self.check(
            "Minimum horizontal clear spacing",
            horizontal,
            request.minimum_horizontal_clear_mm,
            "mm",
            "26.3.2(a)",
        )
        if request.number_of_rows > 1:
            vertical = max(
                request.largest_bar_diameter_mm,
                self.data.number("spacing.vertical_minimum", "mm"),
                request.nominal_maximum_aggregate_mm
                * self.data.number("spacing.vertical_aggregate_factor"),
            )
            self.check(
                "Minimum vertical clear spacing",
                vertical,
                request.minimum_vertical_clear_mm,
                "mm",
                "26.3.2(c)",
            )
        self.limits.append(
            "Partial cover/spacing only: no fire resistance, maximum crack spacing, "
            "redistribution, mix durability, cage-fit, bundle or construction-tolerance "
            "approval. No cover/vibrator reduction credited."
        )

    def deflection(self, request: DeflectionCheckInput) -> None:
        """Check documented external final service deflections, not ULS displacement. Units: mm."""
        if request.method == "SPAN_DEPTH_CHARTS":
            self.data.number("deflection.chart_factors")
            raise NotImplementedError("Span/depth chart workflow is not implemented")
        if not request.includes_creep_shrinkage_temperature:
            raise ScopeRefusal(
                "Immediate deflection alone cannot satisfy final service checks.",
                clause="23.2(a)/(b)",
                value=False,
                limit="explicit final and post-finish all-effects deflections",
            )
        final = request.effective_span_mm / self.data.number("deflection.final_span_divisor")
        post = min(
            request.effective_span_mm / self.data.number("deflection.post_finish_span_divisor"),
            self.data.number("deflection.post_finish_absolute_limit", "mm"),
        )
        self.check(
            "Final all-effects deflection",
            request.final_all_effects_deflection_mm,
            final,
            "mm",
            "23.2(a)",
        )
        self.check(
            "After partitions/finishes deflection",
            request.after_partitions_finishes_deflection_mm,
            post,
            "mm",
            "23.2(b)",
        )
        self.limits.append(
            "Checks externally supplied documented service deflections only. No "
            "stiffness/cracking/creep/shrinkage/temperature or building deflection is "
            "calculated or independently certified here."
        )


def calculate_beam_checks(request: BeamCheckInput, registry: CodeRegistry) -> BeamCheckRun:
    """
    Fixed validation/data → requested checks → provenance/hash pipeline. Units: field-
    specific.
    """
    calculation = ComponentCalculation(request, registry)
    if isinstance(request, BeamShearTorsionInput):
        calculation.shear_torsion(request)
    elif isinstance(request, DevelopmentLengthInput):
        calculation.development(request)
    elif isinstance(request, CoverSpacingInput):
        calculation.cover_spacing(request)
    elif isinstance(request, DeflectionCheckInput):
        calculation.deflection(request)
    else:
        raise TypeError("Unsupported component request; no partial result")
    usage = calculation.tracker.snapshot()
    result = BeamCheckResult(
        kind="DRAFT_BEAM_COMPONENT_CHECKS",
        analysis_revision="beam-checks-draft-v1",
        engine_version=__version__,
        building_design_available=False,
        complete_member_design_available=False,
        verified_code_compliance=False,
        inputs=request,
        quantities=tuple(calculation.quantities),
        flexure_evaluations=tuple(calculation.flexure),
        checks=tuple(calculation.checks),
        code_usage=usage,
        status="DRAFT_COMPONENT_CHECKS_PASS"
        if all(c.ok for c in calculation.checks)
        else "REVISE_SECTION",
        warnings=(
            *((usage.warning,) if usage.warning else ()),
            "PUBLIC TEACHING DRAFT: current amendments and code compliance are NOT established.",
            DRAFT_NOTICE,
        ),
        limitations=(
            *calculation.limits,
            "Only requested component checks; NOT a complete member, building or reinforcement "
            "schedule.",
        ),
    )
    return BeamCheckRun(result=result, result_hash=content_hash(result))
