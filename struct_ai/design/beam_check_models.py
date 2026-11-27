"""Restricted M2 subcheck contracts, never whole-member approval. Units: explicit suffixes."""

from __future__ import annotations

from typing import Annotated, Literal, Self

from pydantic import Field, model_validator

from struct_ai.checks import CheckResult, FrozenModel, NonEmptyText
from struct_ai.codes.registry import CodeUsageSnapshot, Digest
from struct_ai.design.beam_models import BeamFlexureAssessmentInput, BeamFlexureRun
from struct_ai.serialization import content_hash

# Software input bounds, not code allowances. No physical/project defaults.
SmallLength = Annotated[float, Field(gt=0, le=3_000)]
BarDiameter = Annotated[float, Field(ge=6, le=40)]
ConcreteGrade = Literal["M20", "M25", "M30", "M35", "M40"]


class DraftCheckInput(FrozenModel):
    """Explicit public-draft scope; current-amended requests remain blocked. Units: none."""

    calculation_label: NonEmptyText
    source_basis: Literal["PUBLIC_TEACHING_DRAFT", "CURRENT_AMENDED_CODE"]
    acknowledge_unverified: bool

    @model_validator(mode="after")
    def acknowledged(self) -> Self:
        """No implicit acceptance of unverified data. Units: none."""
        if not self.acknowledge_unverified:
            raise ValueError("Explicit acknowledge_unverified=true is required")
        return self


class VerticalStirrups(FrozenModel):
    """Supplied bars, not an automatically selected schedule. Units: mm, counts."""

    steel_grade: Literal["Fe250", "Fe415", "Fe500"]
    diameter_mm: BarDiameter
    effective_legs: Annotated[int, Field(ge=2, le=8)]
    spacing_mm: SmallLength
    enclosure_and_anchorage_confirmed: bool


class TorsionGeometry(FrozenModel):
    """Explicit closed-cage geometry; d1 is derived from principal layer centroids. Units: mm."""

    corner_bar_width_mm: SmallLength
    stirrup_centreline_width_mm: SmallLength
    stirrup_centreline_depth_mm: SmallLength
    closed_rectangular_stirrups_and_corner_bars_confirmed: bool


class SideFaces(FrozenModel):
    """Additional steel, not included in either M1 principal layer. Units: mm² and mm."""

    left_area_mm2: Annotated[float, Field(gt=0, le=100_000)]
    right_area_mm2: Annotated[float, Field(gt=0, le=100_000)]
    maximum_spacing_mm: SmallLength


class BeamShearTorsionInput(DraftCheckInput):
    """Assess one explicit station; no action generation or support enhancement. Units: kN, kN m."""

    operation: Literal["SHEAR_TORSION"]
    flexure: BeamFlexureAssessmentInput
    factored_shear_kn: Annotated[float, Field(ge=-1_000_000, le=1_000_000)]
    factored_torsion_kn_m: Annotated[float, Field(ge=-1_000_000, le=1_000_000)]
    section_conditions: Literal["UNIFORM_NO_AXIAL_NO_ENHANCEMENT_NO_CURTAILMENT"]
    critical_section_actions_confirmed: bool
    longitudinal_anchorage_and_continuity_confirmed: bool
    stirrups: VerticalStirrups
    torsion_geometry: TorsionGeometry | None
    side_faces: SideFaces | None

    @model_validator(mode="after")
    def same_basis(self) -> Self:
        """Prevent nested source-basis disagreement. Units: none."""
        if self.flexure.source_basis != self.source_basis:
            raise ValueError("Outer and flexure source_basis must agree")
        if self.factored_torsion_kn_m == 0 and self.torsion_geometry is not None:
            raise ValueError("torsion_geometry must be null when torsion is zero")
        return self


class DevelopmentLengthInput(DraftCheckInput):
    """Straight Ld only, not lap/bend/support/joint/confinement detailing. Units: mm, N/mm²."""

    operation: Literal["DEVELOPMENT_LENGTH"]
    concrete_grade: ConcreteGrade
    steel_grade: Literal["Fe415", "Fe500"]
    bar_type: Literal["DEFORMED_IS1786"]
    stress_state: Literal["TENSION", "COMPRESSION"]
    bar_diameter_mm: BarDiameter
    design_bar_stress_n_mm2: Annotated[float, Field(gt=0, le=1_000)]
    equal_diameter_bundle_count: Annotated[int, Field(ge=1, le=4)]
    available_straight_length_mm: Annotated[float, Field(gt=0, le=30_000)]


class CoverSpacingInput(DraftCheckInput):
    """Only base cover/minimum clear spacings; requests for missing data fail. Units: mm."""

    operation: Literal["COVER_SPACING"]
    scope: Literal["BASE_COVER_AND_MINIMUM_CLEAR_SPACING_ONLY"]
    exposure: Literal["MILD", "MODERATE", "SEVERE", "VERY_SEVERE", "EXTREME"]
    nominal_cover_to_outermost_steel_mm: SmallLength
    largest_bar_diameter_mm: BarDiameter
    nominal_maximum_aggregate_mm: Annotated[float, Field(gt=0, le=80)]
    minimum_horizontal_clear_mm: SmallLength
    number_of_rows: Annotated[int, Field(ge=1, le=6)]
    minimum_vertical_clear_mm: SmallLength | None
    rows_vertically_aligned: bool
    request_fire_check: bool
    request_maximum_crack_spacing_check: bool

    @model_validator(mode="after")
    def row_contract(self) -> Self:
        """Do not silently ignore absent or extraneous clear distances. Units: mm."""
        if self.number_of_rows == 1 and self.minimum_vertical_clear_mm is not None:
            raise ValueError("One row has no vertical spacing: specify null")
        if self.number_of_rows > 1 and self.minimum_vertical_clear_mm is None:
            raise ValueError("Multiple rows require minimum_vertical_clear_mm")
        return self


class DeflectionCheckInput(DraftCheckInput):
    """Check documented external deflections, not compute them. Units: mm."""

    operation: Literal["DEFLECTION_LIMITS"]
    method: Literal["SUPPLIED_FINAL_DEFLECTIONS", "SPAN_DEPTH_CHARTS"]
    action_basis: Literal["SERVICE_UNFACTORED"]
    reference_level: Literal["AS_CAST_SUPPORTS"]
    effective_span_mm: Annotated[float, Field(gt=0, le=30_000)]
    final_all_effects_deflection_mm: Annotated[float, Field(ge=0, le=3_000)]
    after_partitions_finishes_deflection_mm: Annotated[float, Field(ge=0, le=3_000)]
    includes_creep_shrinkage_temperature: bool
    external_calculation_reference: NonEmptyText


BeamCheckInput = Annotated[
    BeamShearTorsionInput | DevelopmentLengthInput | CoverSpacingInput | DeflectionCheckInput,
    Field(discriminator="operation"),
]


class TraceQuantity(FrozenModel):
    """Returned numbers for display only; not report-side recomputation. Units: `units`."""

    name: NonEmptyText
    value: float
    units: NonEmptyText
    basis: NonEmptyText


class BeamCheckResult(FrozenModel):
    """
    Only the requested subchecks; a passing status is not complete-member approval. Units:
    mixed.
    """

    kind: Literal["DRAFT_BEAM_COMPONENT_CHECKS"]
    analysis_revision: Literal["beam-checks-draft-v1"]
    engine_version: str
    building_design_available: Literal[False]
    complete_member_design_available: Literal[False]
    verified_code_compliance: Literal[False]
    inputs: BeamCheckInput
    quantities: tuple[TraceQuantity, ...]
    flexure_evaluations: tuple[BeamFlexureRun, ...]
    checks: tuple[CheckResult, ...]
    code_usage: CodeUsageSnapshot
    status: Literal["DRAFT_COMPONENT_CHECKS_PASS", "REVISE_SECTION"]
    warnings: tuple[str, ...]
    limitations: tuple[str, ...]

    @model_validator(mode="after")
    def honest_complete_trace(self) -> Self:
        """Reject contradictory status, missing warnings or lost child checks. Units: unchanged."""
        if not self.checks:
            raise ValueError("At least one check is required")
        expected = (
            "DRAFT_COMPONENT_CHECKS_PASS" if all(c.ok for c in self.checks) else "REVISE_SECTION"
        )
        if self.status != expected:
            raise ValueError("Status must agree with every returned check")
        if self.code_usage.warning and self.code_usage.warning not in self.warnings:
            raise ValueError("Actual-use unverified warning must be visible")
        if len({q.name for q in self.quantities}) != len(self.quantities):
            raise ValueError("Trace quantity names must be unique")
        for i, run in enumerate(self.flexure_evaluations, 1):
            if run.result.code_usage.data_digest != self.code_usage.data_digest:
                raise ValueError("Nested flexure cannot use a different catalogue revision")
            for child in run.result.checks:
                expected_check = child.model_copy(update={"name": f"Flexure {i} / {child.name}"})
                if expected_check not in self.checks:
                    raise ValueError("Every child flexure check must be present")
        return self


class BeamCheckRun(FrozenModel):
    """
    Integrity-bound service return; hash is NOT independent engineering verification. Units:
    mixed.
    """

    result: BeamCheckResult
    result_hash: Digest

    @model_validator(mode="after")
    def intact_payload(self) -> Self:
        """Reject altered result payloads. Units: none."""
        if content_hash(self.result) != self.result_hash:
            raise ValueError("Beam subcheck result hash does not match its payload")
        return self
