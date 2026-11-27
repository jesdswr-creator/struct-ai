"""M0b selftest implementation, invoked only through engine_service. Units: kN, m, rad."""

from __future__ import annotations

import hashlib
import platform
import sys
from typing import Literal

from struct_ai.arms.diagnostic_models import DiagnosticRun
from struct_ai.checks import FrozenModel
from struct_ai.codes.registry import Digest
from struct_ai.exceptions import SolverFailure
from struct_ai.resources import resource_path
from struct_ai.serialization import canonical_json

REQUIRED_RESOURCES = (
    "codes/is456_2000/data/catalogue.json",
    "codes/is875/data/catalogue.json",
    "codes/is1893_2016/data/catalogue.json",
    "codes/is13920_2016/data/catalogue.json",
    "gui/resources/fonts/Inter-Variable.ttf",
    "gui/resources/fonts/OFL.txt",
    "gui/resources/app-icon.svg",
    "gui/resources/licenses/OpenSeesPy-LICENSE.md",
    "gui/resources/licenses/LGPL-3.0-only.txt",
    "gui/resources/NOTICES.md",
)


class ResourceEvidence(FrozenModel):
    """A resource that was actually opened and hashed. Units: none."""

    path: str
    sha256: Digest


class SelftestReport(FrozenModel):
    """Packaging evidence, explicitly NOT the future M14 full-design selftest. Units: payload."""

    kind: Literal["M0B_DIAGNOSTIC_SELFTEST"]
    status: Literal["PASS"]
    frozen: bool
    python_version: str
    platform: str
    resources: tuple[ResourceEvidence, ...]
    deterministic_repeat: Literal[True]
    diagnostic: DiagnosticRun
    not_tested: tuple[str, ...]


def run_selftest() -> SelftestReport:
    """Load real data/resources and repeat an independently verified solver run. Units: kN, m."""
    from struct_ai.services import engine_service

    engine_service.list_code_constants()  # Parse every catalogue, not merely test existence.
    resources = tuple(
        ResourceEvidence(
            path=name, sha256=hashlib.sha256(resource_path(name).read_bytes()).hexdigest()
        )
        for name in REQUIRED_RESOURCES
    )
    inputs = engine_service.diagnostic_example_input()
    first = engine_service.run_diagnostic(inputs)
    second = engine_service.run_diagnostic(inputs)
    if canonical_json(first) != canonical_json(second):
        raise SolverFailure(
            "Repeated diagnostic results differ in the same process/environment.",
            clause="DETERMINISM REQUIREMENT (software verification)",
            value=(first.result_hash, second.result_hash),
            limit="byte-identical canonical JSON and hashes",
        )
    return SelftestReport(
        kind="M0B_DIAGNOSTIC_SELFTEST",
        status="PASS",
        frozen=bool(getattr(sys, "frozen", False)),
        python_version=platform.python_version(),
        platform=platform.system(),
        resources=resources,
        deterministic_repeat=True,
        diagnostic=first,
        not_tested=(
            "BuildingInput / building analysis or design",
            "IS 456 beam/column design and Indian Standard checks",
            "DOCX, DXF and schedules (future M14 selftest scope)",
            "A clean Windows machine without Python (requires separate external evidence)",
            "GUI native plugins (use --gui-selftest in addition)",
        ),
    )
