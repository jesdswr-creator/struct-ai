"""The ONLY engine entry point for GUI, CLI and future LLM tools. Units: API-specific."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from pathlib import Path
from typing import TYPE_CHECKING, Any, Literal, Never

from pydantic import BaseModel, ValidationError

from struct_ai import __version__
from struct_ai.arms.diagnostic_models import DiagnosticInput, DiagnosticResult, DiagnosticRun
from struct_ai.checks import FrozenModel
from struct_ai.codes.registry import CataloguedConstant, CodeRegistry, Digest
from struct_ai.exceptions import InputOutOfRange, SolverFailure
from struct_ai.resources import resource_path
from struct_ai.serialization import content_hash

if TYPE_CHECKING:
    from struct_ai.services.diagnostic_jobs import DiagnosticJob
    from struct_ai.services.selftest import SelftestReport


class EngineStatus(FrozenModel):
    """Truthful implemented capabilities, not a design result. Units: counts only."""

    version: str
    state: Literal["DIAGNOSTIC_ONLY"]
    building_design_available: Literal[False]
    message: str


class CodeAudit(FrozenModel):
    """Catalogue inventory, distinct from constants used in a run. Units: per record."""

    data_digest: Digest
    records: tuple[CataloguedConstant, ...]

    @property
    def unverified(self) -> tuple[CataloguedConstant, ...]:
        """List all unverified catalogue records, including missing values. Units: per record."""
        return tuple(record for record in self.records if not record.data.verified)


def get_engine_status() -> EngineStatus:
    """Report capability without importing Qt, OpenSeesPy or an LLM. Units: none."""
    return EngineStatus(
        version=__version__,
        state="DIAGNOSTIC_ONLY",
        building_design_available=False,
        message="Building analysis/design is not implemented. No IS-code compliance is claimed.",
    )


def list_code_constants(*, data_root: Path | None = None) -> CodeAudit:
    """Audit source data, without treating unused records as consumed. Units: per record."""
    root = resource_path("codes") if data_root is None else data_root
    registry = CodeRegistry.load(root)
    return CodeAudit(data_digest=registry.data_digest, records=registry.records)


def design_building(building_input: object) -> Never:
    """Refuse design until the validated pipeline exists. Units: not accepted yet."""
    raise NotImplementedError(
        "Building analysis/design is not implemented in M0/M0b. "
        "BuildingInput, scope screening and engineering milestones must be completed first. "
        "No design or partial building result has been produced."
    )


def diagnostic_example_input() -> DiagnosticInput:
    """Return explicitly SYNTHETIC benchmark inputs, never building defaults. Units: kN, m."""
    return DiagnosticInput(
        length_m=3.0,
        force_kn=12.0,
        area_m2=0.12,
        elastic_modulus_kn_m2=25_000_000.0,
        inertia_m4=0.0008,
    )


def validate_diagnostic_input(data: DiagnosticInput | Mapping[str, Any]) -> DiagnosticInput:
    """Bound strict inputs and translate failures with context. Units: field suffixes."""
    if not isinstance(data, DiagnosticInput | Mapping):
        raise InputOutOfRange(
            "Diagnostic input must be a named input object, not an implicit sequence or null.",
            clause="DIAGNOSTIC INPUT DOMAIN (not an IS-code clause)",
            value=data,
            limit="DiagnosticInput or a mapping with all five explicit numerical fields",
        )
    payload = data.model_dump() if isinstance(data, DiagnosticInput) else dict(data)
    try:
        return DiagnosticInput.model_validate(payload)
    except ValidationError as error:
        raise InputOutOfRange(
            "Invalid synthetic diagnostic input. These are software bounds, not IS-code limits.",
            clause="DIAGNOSTIC INPUT DOMAIN (not an IS-code clause)",
            value=payload,
            limit=error.errors(include_url=False),
        ) from error


def parse_diagnostic_form(fields: Mapping[str, str]) -> DiagnosticInput:
    """Parse explicit decimal-point form text in the service, never in GUI code. Units: suffixes."""
    parsed: dict[str, float] = {}
    for key, text in fields.items():
        try:
            if not isinstance(text, str) or not text.strip():
                raise ValueError("a nonempty decimal number is required")
            parsed[key] = float(text)
        except (ValueError, TypeError, OverflowError) as error:
            raise InputOutOfRange(
                f"{key}: enter a finite decimal number using a decimal point.",
                clause="DIAGNOSTIC INPUT FORMAT (not an IS-code clause)",
                value={key: text},
                limit="explicit finite numeric input; no silent defaults",
            ) from error
    return validate_diagnostic_input(parsed)


def run_diagnostic(
    data: DiagnosticInput | Mapping[str, Any],
    *,
    progress: Callable[[str], None] | None = None,
) -> DiagnosticRun:
    """Fixed validate → model → static → independent-check pipeline. Units: kN, m, rad."""
    from struct_ai.arms.diagnostic_verification import analytical_reference, verify_observations
    from struct_ai.arms.solver_diagnostic import solve_cantilever

    def notify(stage: str) -> None:
        """Forward progress only when a client subscribes. Units: none."""
        if progress is not None:
            progress(stage)

    notify("Validating synthetic inputs")
    inputs = validate_diagnostic_input(data)
    registry = CodeRegistry.load(resource_path("codes"))
    usage = registry.new_tracker().snapshot()  # No code constants are used by this diagnostic.
    observations, solver_version, package_version = solve_cantilever(inputs, notify)
    notify("Checking independent analytical solution")
    reference = analytical_reference(inputs)
    checks = verify_observations(observations, reference)
    if not all(check.ok for check in checks):
        raise SolverFailure(
            "Independent diagnostic verification failed. No verified result was published.",
            clause="ANALYTIC CANTILEVER / GLOBAL EQUILIBRIUM (not an IS-code check)",
            value=[check.model_dump(mode="json") for check in checks],
            limit="every numerical verification check must pass",
        )
    result = DiagnosticResult(
        kind="SYNTHETIC_SOLVER_DIAGNOSTIC",
        building_design_available=False,
        analysis_revision="cantilever-diagnostic-v1",
        engine_version=__version__,
        solver_version=solver_version,
        solver_package_version=package_version,
        inputs=inputs,
        observations=observations,
        analytical_reference=reference,
        checks=checks,
        code_usage=usage,
        limitations=(
            "DIAGNOSTIC ONLY: synthetic two-node elastic cantilever, not a building.",
            "No Indian Standard checks or engineering code constants are implemented.",
            "No self-weight, shear deformation, mass, seismic or member design is included.",
            "The numerical-error checks are not structural utilisation checks.",
            "DRAFT: must be reviewed and sealed by a licensed structural engineer.",
        ),
    )
    return DiagnosticRun(result=result, result_hash=content_hash(result))


def run_diagnostic_form(
    fields: Mapping[str, str], *, progress: Callable[[str], None] | None = None
) -> DiagnosticRun:
    """Validate a form then execute the same fixed service pipeline. Units: field suffixes."""
    return run_diagnostic(parse_diagnostic_form(fields), progress=progress)


def start_diagnostic_job(fields: dict[str, str]) -> DiagnosticJob:
    """Start a process-isolated service job; no GUI or LLM is imported. Units: field suffixes."""
    from struct_ai.services.diagnostic_jobs import DiagnosticJob

    return DiagnosticJob(fields)


def get_diagnostics_text() -> str:
    """Return copyable operational information, not engineering results. Units: none."""
    from struct_ai.services.diagnostics import diagnostics_text

    return diagnostics_text()


def initialise_logging() -> Path:
    """Initialise local operational logs through the service boundary. Units: none."""
    from struct_ai.services.diagnostics import configure_logging

    return configure_logging()


def run_packaging_selftest() -> SelftestReport:
    """Run the M0b solver/resource diagnostic, not the future M14 design test. Units: kN, m."""
    from struct_ai.services.selftest import run_selftest

    return run_selftest()


def write_diagnostic_evidence(path: Path, payload: BaseModel | dict[str, Any]) -> None:
    """Save diagnostic evidence via the sole service entry point. Units: payload-specific."""
    from struct_ai.services.project_io import write_evidence

    write_evidence(path, payload)
