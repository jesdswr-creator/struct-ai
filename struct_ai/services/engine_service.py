"""The ONLY engine entry point for GUI, CLI and future LLM tools. Units: API-specific."""

from __future__ import annotations

import json
from collections.abc import Callable, Mapping
from pathlib import Path
from typing import TYPE_CHECKING, Any, Literal, Never, TypeVar

from pydantic import BaseModel, ValidationError
from pydantic_core import PydanticSerializationError

from struct_ai import __version__
from struct_ai.arms.diagnostic_models import DiagnosticInput, DiagnosticResult, DiagnosticRun
from struct_ai.checks import FrozenModel
from struct_ai.codes.registry import CataloguedConstant, CodeRegistry, Digest
from struct_ai.exceptions import InputOutOfRange, SolverFailure
from struct_ai.resources import resource_path
from struct_ai.serialization import content_hash

if TYPE_CHECKING:
    from struct_ai.design.beam_check_models import BeamCheckInput, BeamCheckRun
    from struct_ai.design.beam_models import (
        BeamFlexureAssessmentInput,
        BeamFlexureDesignInput,
        BeamFlexureRun,
    )
    from struct_ai.services.diagnostic_jobs import DiagnosticJob
    from struct_ai.services.selftest import SelftestReport


class EngineStatus(FrozenModel):
    """Truthful implemented capabilities, not a design result. Units: counts only."""

    version: str
    state: Literal["DRAFT_BEAM_SECTIONS"]
    building_design_available: Literal[False]
    draft_beam_flexure_available: Literal[True]
    draft_beam_component_checks_available: Literal[True]
    ollama_integration_available: Literal[False]
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
        state="DRAFT_BEAM_SECTIONS",
        building_design_available=False,
        draft_beam_flexure_available=True,
        draft_beam_component_checks_available=True,
        ollama_integration_available=False,
        message=(
            "Unverified draft beam flexure and scoped component checks are available through "
            "the service."
            "Building analysis/design and Ollama are not implemented. No IS-code compliance is "
            "claimed."
        ),
    )


def list_code_constants(*, data_root: Path | None = None) -> CodeAudit:
    """Audit source data, without treating unused records as consumed. Units: per record."""
    root = resource_path("codes") if data_root is None else data_root
    registry = CodeRegistry.load(root)
    return CodeAudit(data_digest=registry.data_digest, records=registry.records)


def design_building(building_input: object) -> Never:
    """Refuse design until the validated pipeline exists. Units: not accepted yet."""
    raise NotImplementedError(
        "Building analysis/design is not implemented; M1 supplies draft sections only. "
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
            "This solver diagnostic performs no Indian Standard checks and consumes no code "
            "constants.",
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


_SectionInput = TypeVar("_SectionInput", bound=BaseModel)


def _validate_section_input(
    data: BaseModel | Mapping[str, Any], model: type[_SectionInput], *, milestone: str = "M1"
) -> _SectionInput:
    """Revalidate even constructed model instances; preserve all context. Units: field suffixes."""
    if not isinstance(data, BaseModel | Mapping):
        raise InputOutOfRange(
            "Beam-section input must be a complete named object.",
            clause=f"{milestone} SECTION INPUT DOMAIN (software bounds, not code allowances)",
            value=data,
            limit="explicit geometry, strengths/curve, factored actions and draft acknowledgement",
        )
    payload: Any = data
    try:
        payload = data.model_dump(warnings="error") if isinstance(data, BaseModel) else dict(data)
        return model.model_validate(payload)
    except (ValidationError, PydanticSerializationError) as error:
        raise InputOutOfRange(
            "Invalid beam-section input; no defaults or coerced values were used.",
            clause=f"{milestone} SECTION INPUT DOMAIN (software bounds, not code allowances)",
            value=payload,
            limit=error.errors(include_url=False)
            if isinstance(error, ValidationError)
            else str(error),
        ) from error


def validate_beam_flexure_design(
    data: BeamFlexureDesignInput | Mapping[str, Any],
) -> BeamFlexureDesignInput:
    """Validate inverse inputs without calculating a section. Units: field suffixes."""
    from struct_ai.design.beam_models import BeamFlexureDesignInput

    return _validate_section_input(data, BeamFlexureDesignInput)


def validate_beam_flexure_assessment(
    data: BeamFlexureAssessmentInput | Mapping[str, Any],
) -> BeamFlexureAssessmentInput:
    """Validate supplied areas and explicit bending direction. Units: field suffixes."""
    from struct_ai.design.beam_models import BeamFlexureAssessmentInput

    return _validate_section_input(data, BeamFlexureAssessmentInput)


def _run_beam_section(
    request: BeamFlexureDesignInput | BeamFlexureAssessmentInput, data_root: Path | None
) -> BeamFlexureRun:
    """Execute only deterministic code; no solver, GUI or assistant import. Units: API-specific."""
    from struct_ai.design.beam_flexure import calculate_beam_flexure

    registry = CodeRegistry.load(resource_path("codes") if data_root is None else data_root)
    try:
        return calculate_beam_flexure(request, registry)
    except (ArithmeticError, ValidationError) as error:
        raise SolverFailure(
            "Section arithmetic/result-contract failure; no draft result was published.",
            clause="M1 NUMERICAL RESULT DOMAIN (not a code allowance)",
            value=str(error),
            limit="finite, self-consistent section results within the supported numerical domain",
        ) from error


def design_beam_flexure(
    data: BeamFlexureDesignInput | Mapping[str, Any], *, data_root: Path | None = None
) -> BeamFlexureRun:
    """Draft continuous steel sizing then forward equilibrium/checks. Units: input mm, N/mm², kN m.

    No analysis, action factoring, bars, detailing or code-compliance certification.
    An alternate data root is explicit and validated, never a missing-data fallback.
    """
    return _run_beam_section(validate_beam_flexure_design(data), data_root)


def assess_beam_flexure(
    data: BeamFlexureAssessmentInput | Mapping[str, Any], *, data_root: Path | None = None
) -> BeamFlexureRun:
    """Draft assessment of supplied physical top/bottom areas. Units: mm, mm², N/mm², kN m."""
    return _run_beam_section(validate_beam_flexure_assessment(data), data_root)


def _parse_section_json(text: str, operations: tuple[str, ...]) -> dict[str, Any]:
    """Reject duplicate, nonfinite or oversized JSON. Units: explicit field suffixes."""

    def unique_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        """Disallow ambiguous duplicate fields, including nested objects. Units: none."""
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f"Duplicate JSON field: {key}")
            result[key] = value
        return result

    def reject_constant(token: str) -> Never:
        """Reject NaN/Infinity tokens. Units: none."""
        raise ValueError(f"Non-finite JSON token: {token}")

    try:
        if not isinstance(text, str) or len(text.encode("utf-8")) > 1_000_000:
            raise ValueError("Request must be UTF-8 JSON text of at most 1,000,000 bytes")
        payload = json.loads(text, object_pairs_hook=unique_pairs, parse_constant=reject_constant)
        if not isinstance(payload, dict) or payload.get("operation") not in operations:
            raise ValueError(f"operation must explicitly be one of {operations}")
    except (ValueError, TypeError, UnicodeError, RecursionError) as error:
        raise InputOutOfRange(
            "Cannot parse beam-section JSON; no calculation was started.",
            clause="SECTION JSON INPUT FORMAT (not a code clause)",
            value=str(error),
            limit="unambiguous finite JSON object with an explicit operation",
        ) from error
    return payload


def run_beam_flexure_json(text: str) -> BeamFlexureRun:
    """Parse strict JSON then use the same service pipeline. Units: field suffixes."""
    payload = _parse_section_json(text, ("DESIGN", "ASSESS"))
    if payload["operation"] == "DESIGN":
        return design_beam_flexure(payload)
    return assess_beam_flexure(payload)


def beam_flexure_report(run: BeamFlexureRun) -> str:
    """Render revalidated results, failures and warnings. Units: payload-defined."""
    from struct_ai.design.beam_models import BeamFlexureRun
    from struct_ai.reporting.beam_flexure import render_beam_report

    if not isinstance(run, BeamFlexureRun):
        raise InputOutOfRange(
            "A beam report requires a completed, hashed beam-section run.",
            clause="M1 REPORT INPUT CONTRACT (not an engineering code clause)",
            value=type(run).__name__,
            limit="BeamFlexureRun from the deterministic service",
        )
    try:
        checked_run = BeamFlexureRun.model_validate(run.model_dump(warnings="error"))
    except (ValidationError, PydanticSerializationError) as error:
        raise InputOutOfRange(
            "Beam payload failed integrity/contract validation; no report was rendered.",
            clause="M1 REPORT INPUT CONTRACT (not an engineering code clause)",
            value=str(error),
            limit="unaltered, self-consistent section result with its matching hash",
        ) from error
    return render_beam_report(checked_run)


def validate_beam_checks(data: BaseModel | Mapping[str, Any]) -> BeamCheckInput:
    """
    Validate the explicitly selected M2 subcheck, including constructed models. Units:
    suffixes.
    """
    from struct_ai.design.beam_check_models import (
        BeamShearTorsionInput,
        CoverSpacingInput,
        DeflectionCheckInput,
        DevelopmentLengthInput,
    )

    models = {
        "SHEAR_TORSION": BeamShearTorsionInput,
        "DEVELOPMENT_LENGTH": DevelopmentLengthInput,
        "COVER_SPACING": CoverSpacingInput,
        "DEFLECTION_LIMITS": DeflectionCheckInput,
    }
    operation = (
        getattr(data, "operation", None)
        if isinstance(data, BaseModel)
        else (data.get("operation") if isinstance(data, Mapping) else None)
    )
    if not isinstance(operation, str) or operation not in models:
        raise InputOutOfRange(
            "An explicit supported beam-component operation is required.",
            clause="M2 INPUT CONTRACT (not a code allowance)",
            value=operation,
            limit=tuple(models),
        )
    return _validate_section_input(data, models[operation], milestone="M2")


def assess_beam_checks(
    data: BaseModel | Mapping[str, Any],
    *,
    data_root: Path | None = None,
) -> BeamCheckRun:
    """Run only requested draft subchecks; no building/member approval. Units: field suffixes."""
    from struct_ai.design.beam_checks import calculate_beam_checks

    request = validate_beam_checks(data)
    registry = CodeRegistry.load(resource_path("codes") if data_root is None else data_root)
    try:
        return calculate_beam_checks(request, registry)
    except (ArithmeticError, ValidationError) as error:
        raise SolverFailure(
            "Beam component arithmetic/result-contract failure; no result was published.",
            clause="M2 NUMERICAL RESULT DOMAIN (not a code allowance)",
            value=str(error),
            limit="finite self-consistent subcheck result",
        ) from error


def run_beam_checks_json(text: str) -> BeamCheckRun:
    """Strict bounded JSON ingress shared with flexure. Units: explicit field suffixes."""
    return assess_beam_checks(
        _parse_section_json(
            text, ("SHEAR_TORSION", "DEVELOPMENT_LENGTH", "COVER_SPACING", "DEFLECTION_LIMITS")
        )
    )


def beam_checks_report(run: BeamCheckRun) -> str:
    """Render revalidated values/checks, never perform report-side engineering. Units: payload."""
    from struct_ai.design.beam_check_models import BeamCheckRun
    from struct_ai.reporting.beam_checks import render_component_report

    if not isinstance(run, BeamCheckRun):
        raise InputOutOfRange(
            "A component report requires a completed hashed run.",
            clause="M2 REPORT CONTRACT",
            value=type(run).__name__,
            limit="BeamCheckRun from engine_service",
        )
    try:
        checked = BeamCheckRun.model_validate(run.model_dump(warnings="error"))
    except (ValidationError, PydanticSerializationError) as error:
        raise InputOutOfRange(
            "Component report integrity/contract validation failed.",
            clause="M2 REPORT CONTRACT",
            value=str(error),
            limit="unaltered result and matching hash",
        ) from error
    return render_component_report(checked)
