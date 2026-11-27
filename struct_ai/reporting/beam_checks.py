"""Display only returned M2 values/checks/provenance, no recalculation. Units: payload fields."""

from __future__ import annotations

from struct_ai.design.beam_check_models import BeamCheckRun


def _cell(value: object) -> str:
    """Escape table syntax without modifying underlying results. Units: unchanged."""
    return str(value).replace("|", "\\|").replace("\r", " ").replace("\n", " ")


def render_component_report(run: BeamCheckRun) -> str:
    """Render a service-revalidated run; all check decisions are already made. Units: declared."""
    result = run.result
    lines = ["# DRAFT — beam component checks", ""]
    lines.extend(f"> **{_cell(w)}**" for w in result.warnings)
    lines.extend(
        (
            "",
            f"**Calculation:** {_cell(result.inputs.calculation_label)}",
            f"**Operation:** `{result.inputs.operation}`",
            f"**Status:** `{result.status}` — requested subchecks ONLY, not code compliance.",
            f"**Engine / method:** `{result.engine_version}` / `{result.analysis_revision}`",
            f"**Result SHA-256:** `{run.result_hash}`",
            f"**Code-data SHA-256:** `{result.code_usage.data_digest}`",
            "",
            "## Explicit input (not a building model)",
            "",
            "```json",
            result.inputs.model_dump_json(indent=2),
            "```",
            "",
            "## Returned trace",
            "",
            "| Quantity | Value | Units | Basis |",
            "|---|---:|---|---|",
        )
    )
    for q in result.quantities:
        lines.append(f"| {_cell(q.name)} | {q.value:.15g} | {_cell(q.units)} | {_cell(q.basis)} |")
    lines.extend(
        (
            "",
            "## Checks — no passing tolerance",
            "",
            "Required minima are demand; supplied provisions are capacity. "
            "Display rounding never changes pass/fail.",
            "",
            "| Check | Outcome | Demand | Capacity | Ratio | Units | Clause |",
            "|---|---|---:|---:|---:|---|---|",
        )
    )
    for c in result.checks:
        lines.append(
            f"| {_cell(c.name)} | {'PASS' if c.ok else 'FAIL'} | {c.demand:.15g} | "
            f"{c.capacity:.15g} | {c.ratio:.15g} | {_cell(c.units)} | {_cell(c.clause)} |"
        )
    if result.flexure_evaluations:
        lines.extend(
            (
                "",
                "## Nested M1 forward evaluations",
                "",
                "Physical principal areas are assessed separately at each returned equivalent "
                "moment; side-face steel is not credited. Full child payloads are in JSON.",
            )
        )
        for index, child in enumerate(result.flexure_evaluations, 1):
            lines.append(
                f"- Flexure {index}: `{child.result.status}`; result SHA-256 `{child.result_hash}`."
            )
    lines.extend(("", "## Limitations and human review", ""))
    lines.extend(f"- {_cell(item)}" for item in result.limitations)
    lines.extend(
        (
            "",
            "## Actual-use unverified code-data trace",
            "",
            "The complete selected shear column/row axis is consumed to validate interpolation; "
            "unused grade columns and missing unrequested routes are not included.",
            "",
            "| Identifier | Value | Units | Verified | Clause | Source / review note |",
            "|---|---:|---|---|---|---|",
        )
    )
    for record in result.code_usage.constants:
        d = record.data
        lines.append(
            f"| `{record.identifier}` | {d.value} | {_cell(d.units)} | {d.verified} | "
            f"{_cell(d.clause)} | {_cell(d.source)}; {_cell(d.verification_note)} |"
        )
    lines.extend(
        ("", "**DRAFT: must be reviewed and sealed by a licensed structural engineer.**", "")
    )
    return "\n".join(lines)
