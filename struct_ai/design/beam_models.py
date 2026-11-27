"""Draft beam-section contracts, not BuildingInput. Units: mm, mm², N/mm² and kN m."""

from __future__ import annotations

from typing import Annotated, Literal, Self

from pydantic import Field, model_validator

from struct_ai.checks import CheckResult, FrozenModel, NonEmptyText, NonNegative, Positive
from struct_ai.codes.registry import CodeUsageSnapshot, Digest
from struct_ai.serialization import content_hash

Face = Literal["TOP", "BOTTOM"]
# These are tested computational domains, NOT limits prescribed by an Indian Standard.
Length = Annotated[float, Field(ge=1.0, le=30_000.0)]
Area = Annotated[float, Field(ge=0.0, le=100_000.0)]


class FlangeInput(FrozenModel):
    """Explicit slab participation; no inferred span factor. Units: mm and mm²/m.

    The caller supplies the actual available flange width and distance between zero
    moments, NOT an unlabelled span. Composite action must be confirmed when credited.
    Slab reinforcement is needed for the transverse-ratio check only when its main
    reinforcement is parallel to this beam. No slab design is performed.
    """

    kind: Literal["T", "L"]
    face: Face
    thickness_mm: Length
    actual_width_mm: Length
    zero_moment_distance_mm: Length
    width_rule: Literal["SLAB_BEAM", "ISOLATED"]
    composite_action_confirmed: bool
    slab_main_parallel_to_beam: bool
    main_steel_mm2_per_m: Positive | None
    transverse_steel_mm2_per_m: Positive | None


class BeamGeometry(FrozenModel):
    """Two layer centroids from their OWN faces, not nominal covers. Units: mm.

    Positive moment means top compression/bottom tension. Negative moment reverses
    those faces and uses the other explicitly supplied centroid; d is never reused
    silently. Geometry is not a cover, spacing, fire or constructability check.
    """

    web_width_mm: Annotated[float, Field(ge=50.0, le=2_000.0)]
    overall_depth_mm: Annotated[float, Field(ge=100.0, le=3_000.0)]
    top_centroid_from_top_mm: Length
    bottom_centroid_from_bottom_mm: Length
    flange: FlangeInput | None

    @model_validator(mode="after")
    def geometric_relationships(self) -> Self:
        """Reject crossing layers and impossible flange geometry. Units: mm."""
        if (
            self.top_centroid_from_top_mm + self.bottom_centroid_from_bottom_mm
            >= self.overall_depth_mm
        ):
            raise ValueError("Layer centroid offsets must sum to less than overall_depth_mm")
        if self.flange is not None:
            if self.flange.actual_width_mm < self.web_width_mm:
                raise ValueError("actual_width_mm must be at least web_width_mm")
            if self.flange.thickness_mm >= self.overall_depth_mm:
                raise ValueError("Flange thickness must be less than overall depth")
        return self


class BeamMaterialInput(FrozenModel):
    """Declared strengths and representative steel type. Units: fck in N/mm².

    The 20..40 range is the application's restricted draft test domain, not a claim
    that arbitrary strengths are standard grades or adequate for any exposure. TMT,
    Fe250/550 and manufacturer-specific curves are not silently mapped to this curve.
    """

    fck_n_mm2: Annotated[float, Field(ge=20.0, le=40.0)]
    steel_grade: Literal["Fe415", "Fe500"]
    steel_curve: Literal["REPRESENTATIVE_COLD_WORKED"]


class BeamRequest(FrozenModel):
    """Required basis and signed, already factored pure bending. Units: kN, kN m, mm."""

    calculation_label: NonEmptyText
    source_basis: Literal["PUBLIC_TEACHING_DRAFT", "CURRENT_AMENDED_CODE"]
    acknowledge_unverified: bool
    method: Literal["CONTINUOUS_STRAIN_COMPATIBILITY"]
    action_basis: Literal["FACTORED_ULS"]
    geometry: BeamGeometry
    materials: BeamMaterialInput
    factored_moment_kn_m: Annotated[float, Field(ge=-1_000_000.0, le=1_000_000.0)]
    axial_force_kn: Annotated[float, Field(ge=-100_000.0, le=100_000.0)]

    @model_validator(mode="after")
    def explicit_draft_and_direction(self) -> Self:
        """Require acknowledgement and a resolvable bending direction. Units: kN m."""
        if not self.acknowledge_unverified:
            raise ValueError("Explicit acknowledge_unverified=true is required")
        if abs(self.factored_moment_kn_m) < 1e-6:
            raise ValueError(
                "abs(factored_moment_kn_m) must be >= 1e-6 kN m; numerical domain, not a code limit"
            )
        return self


class BeamReinforcement(FrozenModel):
    """Continuous areas, NOT chosen bars or a reinforcement schedule. Units: mm²."""

    top_mm2: Area
    bottom_mm2: Area


class BeamFlexureDesignInput(BeamRequest):
    """Inverse sizing policy; no automatic section enlargement. Units: inherited."""

    operation: Literal["DESIGN"]
    reinforcement_policy: Literal["SINGLE_ONLY", "ALLOW_COMPRESSION_STEEL"]


class BeamFlexureAssessmentInput(BeamRequest):
    """Assess actual declared layer areas under one bending direction. Units: inherited."""

    operation: Literal["ASSESS"]
    reinforcement: BeamReinforcement


class BeamConstitutiveParameters(FrozenModel):
    """The actual consumed material parameters, not report literals. Units: field suffixes."""

    concrete_peak_factor: Positive
    concrete_peak_stress_n_mm2: Positive
    concrete_plateau_strain: Positive
    concrete_ultimate_strain: Positive
    steel_yield_strength_n_mm2: Positive
    steel_elastic_modulus_n_mm2: Positive
    steel_partial_factor: Positive
    steel_design_yield_n_mm2: Positive
    minimum_tensile_strain: Positive


class BeamLimits(FrozenModel):
    """Derived limits and explicitly DIFFERENT model comparisons. Units: field suffixes."""

    xu_max_over_d: Positive
    xu_max_mm: Positive
    rectangular_annex_g_coefficient: Positive
    rectangular_integrated_curve_coefficient: Positive
    concrete_only_limiting_moment_kn_m: Positive
    minimum_tension_steel_mm2: Positive
    maximum_tension_steel_mm2: Positive
    maximum_compression_steel_mm2: Positive


class BeamSizing(FrozenModel):
    """Inverse-sizing trace, before any bar selection. Units: mm² and kN m.

    The tiny explicit target reserve controls floating-point inversion, not code
    acceptance. It increases the sizing target; it never relaxes a passing check.
    """

    governing: Literal["FLEXURE", "MINIMUM_TENSION_STEEL", "DOUBLY_REINFORCED"]
    tension_area_from_flexure_mm2: Positive
    compression_area_from_flexure_mm2: NonNegative
    moment_sizing_target_kn_m: Positive
    numerical_moment_reserve_kn_m: NonNegative
    neutral_axis_sizing_target_mm: Positive


class BeamSectionState(FrozenModel):
    """Unrounded section equilibrium at ultimate concrete strain. Units: explicit suffixes."""

    compression_face: Face
    tension_face: Face
    effective_depth_mm: Positive
    opposite_layer_depth_mm: Positive
    effective_flange_width_mm: Positive
    uncapped_flange_width_mm: Positive | None
    flange_width_capped_by_actual: bool
    compression_case: Literal[
        "RECTANGULAR",
        "FLANGE_IN_TENSION_IGNORED",
        "NA_IN_FLANGE",
        "NA_IN_WEB_FLANGE_PLATEAU",
        "NA_IN_WEB_FLANGE_PART_PARABOLIC",
    ]
    neutral_axis_mm: Positive
    tensile_strain: Positive
    opposite_layer_strain: float | None
    tension_steel_stress_n_mm2: Positive
    opposite_steel_stress_n_mm2: float | None
    displaced_concrete_stress_n_mm2: NonNegative
    concrete_force_n: Positive
    concrete_centroid_mm: Positive
    opposite_net_force_n: float
    tension_force_n: Positive
    axial_residual_n: float
    moment_capacity_kn_m: Positive


class BeamFlexureResult(FrozenModel):
    """An unverified section result, never a building approval. Units: field-specific."""

    kind: Literal["DRAFT_BEAM_FLEXURE"]
    analysis_revision: Literal["beam-flexure-draft-v1"]
    engine_version: str
    building_design_available: Literal[False]
    verified_code_compliance: Literal[False]
    inputs: Annotated[
        BeamFlexureDesignInput | BeamFlexureAssessmentInput, Field(discriminator="operation")
    ]
    reinforcement: BeamReinforcement
    sizing: BeamSizing | None
    parameters: BeamConstitutiveParameters
    limits: BeamLimits
    section: BeamSectionState
    checks: tuple[CheckResult, ...]
    code_usage: CodeUsageSnapshot
    status: Literal["DRAFT_SECTION_CHECKS_PASS", "REVISE_SECTION"]
    warnings: tuple[str, ...]
    limitations: tuple[str, ...]

    @model_validator(mode="after")
    def honest_status(self) -> Self:
        """Reject a false pass, empty checks or hidden unverified usage. Units: unchanged."""
        if not self.checks:
            raise ValueError("A section result requires checks")
        expected = (
            "DRAFT_SECTION_CHECKS_PASS" if all(c.ok for c in self.checks) else "REVISE_SECTION"
        )
        if self.status != expected:
            raise ValueError("Section status must agree with every CheckResult")
        if self.code_usage.warning and self.code_usage.warning not in self.warnings:
            raise ValueError("The actual-use unverified warning must be visible")
        return self


class BeamFlexureRun(FrozenModel):
    """Immutable payload and reproducibility hash, including FAILED checks. Units: inherited."""

    result: BeamFlexureResult
    result_hash: Digest

    @model_validator(mode="after")
    def intact_payload(self) -> Self:
        """Reject a changed payload; a hash is integrity, NOT engineering verification. Units:
        none.
        """
        if self.result_hash != content_hash(self.result):
            raise ValueError("Beam result hash does not match its payload")
        return self
