"""Readable trace of a draft beam result; no design calculations. Units: from result fields."""

from __future__ import annotations

import html

from struct_ai.design.beam_models import BeamFlexureRun


def _text(value: object) -> str:
    """Escape data for a Markdown cell; labels are not trusted markup. Units: unchanged."""
    return html.escape(str(value)).replace("|", "&#124;").replace("\n", " ").replace("`", "&#96;")


def render_beam_report(run: BeamFlexureRun) -> str:
    """Render returned fields/checks, preserving provenance and failures. Units: explicitly
    labelled.
    """
    result = run.result
    section, limits = result.section, result.limits
    geometry = result.inputs.geometry
    parameters = result.parameters
    lines = [
        "# DRAFT — beam-section flexure",
        "",
        *(f"> **{_text(warning)}**" for warning in result.warnings),
        "",
        f"**Calculation:** {_text(result.inputs.calculation_label)}  ",
        f"**Status:** `{result.status}` — section checks only, NOT code-compliance approval.  ",
        f"**Operation:** {result.inputs.operation}  ",
        f"**Engine / method revision:** `{result.engine_version}` / `{result.analysis_revision}`  ",
        f"**Result SHA-256:** `{run.result_hash}`  ",
        f"**Code-data SHA-256:** `{result.code_usage.data_digest}`",
        "",
        "## Basis and geometry",
        "",
        "Continuous parabolic-rectangular concrete using the catalogued **NPTEL rounded peak "
        f"{parameters.concrete_peak_factor:.9g} fck**; steel uses "
        f"**fy/{parameters.steel_partial_factor:.9g}**, not rounded 0.87fy. "
        "The Annex G equivalent-block comparison below is a different approximation and is "
        "not substituted into this response.",
        "",
        "| Returned quantity | Value | Units |",
        "|---|---:|---|",
        f"| Factored signed moment (input) | {result.inputs.factored_moment_kn_m:.9g} | kN m |",
        f"| Axial force (input; pure-bending scope) | {result.inputs.axial_force_kn:.9g} | kN |",
        f"| Web width | {geometry.web_width_mm:.9g} | mm |",
        f"| **Overall D** | {geometry.overall_depth_mm:.9g} | mm |",
        f"| Effective d, active direction | {section.effective_depth_mm:.9g} | mm |",
        f"| Opposite-layer depth, active direction | {section.opposite_layer_depth_mm:.9g} | mm |",
        f"| Compression / tension face | {section.compression_face} / {section.tension_face} | — |",
        f"| Effective compression width | {section.effective_flange_width_mm:.9g} | mm |",
        f"| Actual-width cap active | {section.flange_width_capped_by_actual} | — |",
        f"| Compression case | {section.compression_case} | — |",
        f"| Concrete fck (explicit input) | {result.inputs.materials.fck_n_mm2:.9g} | N/mm² |",
        f"| Steel grade / curve | {result.inputs.materials.steel_grade} / "
        f"{result.inputs.materials.steel_curve} | — |",
        "",
        "## Continuous steel areas — NOT selected bars",
        "",
        f"- Physical top layer: **{result.reinforcement.top_mm2:.9g} mm²**.",
        f"- Physical bottom layer: **{result.reinforcement.bottom_mm2:.9g} mm²**.",
        "- No bar diameters, bar counts, cover/spacing compliance or constructability are implied.",
    ]
    if result.sizing is not None:
        sizing = result.sizing
        lines += [
            f"- Sizing governs by: **{sizing.governing}**.",
            f"- Tension area from flexure before minimum provision: "
            f"{sizing.tension_area_from_flexure_mm2:.9g} mm².",
            f"- Compression area from flexure: {sizing.compression_area_from_flexure_mm2:.9g} mm².",
            f"- Sizing target: {sizing.moment_sizing_target_kn_m:.12g} kN m; disclosed numerical "
            f"reserve {sizing.numerical_moment_reserve_kn_m:.9g} kN m.",
            f"- Sizing neutral-axis target: {sizing.neutral_axis_sizing_target_mm:.12g} mm.",
        ]
    lines += [
        "",
        "## Strain compatibility and equilibrium",
        "",
        "| Returned quantity | Value | Units |",
        "|---|---:|---|",
        f"| Neutral axis | {section.neutral_axis_mm:.12g} | mm |",
        f"| Strain-derived limiting xu/d | {limits.xu_max_over_d:.12g} | 1 |",
        f"| Limiting xu (representable conservative endpoint) | {limits.xu_max_mm:.12g} | mm |",
        f"| Tensile strain | {section.tensile_strain:.12g} | 1 |",
        f"| Opposite-layer strain (none when absent) | {section.opposite_layer_strain} | 1 |",
        f"| Tensile steel stress | {section.tension_steel_stress_n_mm2:.12g} | N/mm² |",
        f"| Opposite steel stress (signed; none when absent) | "
        f"{section.opposite_steel_stress_n_mm2} "
        "| N/mm² |",
        f"| Displaced concrete stress at opposite steel | "
        f"{section.displaced_concrete_stress_n_mm2:.12g} | N/mm² |",
        f"| Gross concrete compression | {section.concrete_force_n:.12g} | N |",
        f"| Concrete centroid from active compression face | {section.concrete_centroid_mm:.12g} "
        "| mm |",
        f"| Net opposite-layer force (steel minus displaced concrete) | "
        f"{section.opposite_net_force_n:.12g} | N |",
        f"| Tension force | {section.tension_force_n:.12g} | N |",
        f"| Axial residual | {section.axial_residual_n:.12g} | N |",
        f"| Moment capacity, magnitude | {section.moment_capacity_kn_m:.12g} | kN m |",
        f"| Concrete-only limiting moment, integrated model | "
        f"{limits.concrete_only_limiting_moment_kn_m:.12g} | kN m |",
        f"| Rectangular Annex G **comparison** coefficient | "
        f"{limits.rectangular_annex_g_coefficient:.12g} | 1 |",
        f"| Rectangular integrated-curve coefficient | "
        f"{limits.rectangular_integrated_curve_coefficient:.12g} | 1 |",
        "",
        "## Checks — literal demand ≤ capacity, no passing tolerance",
        "",
        "Minimum provisions use required minimum as demand and actual provision as capacity. "
        "The numerical equilibrium ratio is **error/budget**, not structural utilisation. "
        "Display rounding never changes stored CheckResult values or pass/fail.",
        "",
        "| Check | Outcome | Demand | Capacity | Ratio | Units | Clause / basis |",
        "|---|---|---:|---:|---:|---|---|",
    ]
    for check in result.checks:
        lines.append(
            f"| {_text(check.name)} | {'PASS' if check.ok else '**FAIL**'} | "
            f"{check.demand:.12g} | {check.capacity:.12g} | {check.ratio:.12g} | "
            f"{_text(check.units)} | {_text(check.clause)} |"
        )
    lines += [
        "",
        "## Limitations and review requirements",
        "",
        *(f"- {_text(limitation)}" for limitation in result.limitations),
        "",
        "## Actual-use code-data trace",
        "",
        "Only consumed records appear here; the separate audit command also lists unused/missing "
        "records. All shipped values remain unverified. Unknown current-amendment applicability "
        "is not consumed as a guessed coefficient.",
        "",
        "| Identifier | Value | Units | Verified | Clause | Source / review note |",
        "|---|---:|---|---|---|---|",
    ]
    for record in result.code_usage.constants:
        data = record.data
        lines.append(
            f"| `{record.identifier}` | {data.value} | {_text(data.units)} | {data.verified} | "
            f"{_text(data.clause)} | {_text(data.source)}; {_text(data.verification_note)} |"
        )
    lines += ["", "**DRAFT: must be reviewed and sealed by a licensed structural engineer.**", ""]
    return "\n".join(lines)
