"""Strict data contracts for a synthetic cantilever, NOT a building. Units: kN, m, rad."""

from __future__ import annotations

from typing import Annotated, Literal, Self

from pydantic import Field, model_validator

from struct_ai.checks import CheckResult, FrozenModel
from struct_ai.codes.registry import CodeUsageSnapshot, Digest
from struct_ai.serialization import content_hash


class DiagnosticInput(FrozenModel):
    """Explicit synthetic inputs; bounds are computational, not IS limits. Units: suffixes.

    A vertical 2D Euler-Bernoulli cantilever has a fixed base, positive length along Y,
    and signed tip force along global X. No self-weight, mass or code design is included.
    """

    length_m: Annotated[float, Field(ge=0.001, le=100.0)]
    force_kn: Annotated[float, Field(ge=-10_000.0, le=10_000.0)]
    area_m2: Annotated[float, Field(ge=1e-6, le=10.0)]
    elastic_modulus_kn_m2: Annotated[float, Field(ge=1_000.0, le=1e10)]
    inertia_m4: Annotated[float, Field(ge=1e-12, le=100.0)]

    @model_validator(mode="after")
    def nonzero_load(self) -> Self:
        """Exclude zero/subnormal-response benchmarks. Units: force in kN; NOT an IS limit."""
        if abs(self.force_kn) < 1e-6:
            raise ValueError(
                "abs(force_kn) must be at least 1e-6 kN for this numerical diagnostic; "
                "this is a software-domain bound, not an engineering code limit"
            )
        return self


class SolverObservations(FrozenModel):
    """Unaltered signed solver outputs. Units: m, rad, kN, kN·m as named."""

    tip_displacement_m: float
    tip_rotation_rad: float
    support_fx_kn: float
    support_fy_kn: float
    support_mz_kn_m: float


class DiagnosticResult(FrozenModel):
    """Traceable diagnostic only; never a building or code-compliance result. Units: explicit."""

    kind: Literal["SYNTHETIC_SOLVER_DIAGNOSTIC"]
    building_design_available: Literal[False]
    analysis_revision: Literal["cantilever-diagnostic-v1"]
    engine_version: str
    solver_version: str
    solver_package_version: str
    inputs: DiagnosticInput
    observations: SolverObservations
    analytical_reference: SolverObservations
    checks: tuple[CheckResult, ...]
    code_usage: CodeUsageSnapshot
    limitations: tuple[str, ...]


class DiagnosticRun(FrozenModel):
    """A verified immutable payload and its canonical hash. Units: payload-specific."""

    result: DiagnosticResult
    result_hash: Digest

    @model_validator(mode="after")
    def check_hash(self) -> Self:
        """Reject altered payloads and failed diagnostics. Units: none."""
        if self.result_hash != content_hash(self.result):
            raise ValueError("Diagnostic payload does not match its content hash")
        if not self.result.checks or not all(check.ok for check in self.result.checks):
            raise ValueError("Failed or empty verification cannot be published as a verified run")
        return self
