# M1: draft beam-section service

> **DRAFT: must be reviewed and sealed by a licensed structural engineer.**
> This is a public-source **unverified section calculator**, not a complete structural
> design application, a current-code compliance result or a bar schedule.

## What is available

- Single/double reinforcement, rectangular and T/L section flexure.
- Continuous strain-compatible concrete/steel response, displaced-concrete correction.
- Signed moments with separate physical top/bottom steel centroids.
- Explicit flange participation and effective-width rules/caps.
- Longitudinal min/max checks, using overall D for maximum steel.
- Strict input/missing-data failures; no over-reinforcement clamp or section resizing.
- CheckResult objects, actual-use warnings, source/data/result hashes, JSON and Markdown trace.

The numerical model is **not** the rounded Annex G equivalent block. It integrates the
explicitly adopted public teaching curve, and separately reports derived Annex G
comparison coefficients. Read the [full draft basis, derivations and limitations](research/M1_DRAFT_DESIGN_BASIS.md)
before comparing numbers from another program or a differently rounded textbook example.

## Run from a source checkout

Install the existing pinned environment as described in the README. No Ollama, Qt import,
OpenSees call or network access is needed for these section calculations.

```bat
.venv\Scripts\python.exe -m struct_ai.cli.beam_flexure examples\SAMPLE_beam_rectangular.json --output .artifacts\beam-result.json --report .artifacts\beam-report.md
```

On Linux replace the interpreter with `.venv/bin/python`. The installed console command
is `struct-ai-beam`. Output paths must be **new**; the CLI refuses to overwrite input or
old evidence. Without `--output`, result JSON goes to stdout; warnings go to stderr.
Exit codes: **0** draft section checks pass, **1** REVISE_SECTION, **2** refused/error.
No result is written for a missing-data or unsupported-input failure.

Other opt-in examples:

- `examples/SAMPLE_beam_doubly_reinforced.json`
- `examples/SAMPLE_beam_T.json`
- `examples/SAMPLE_beam_L.json`

These are deliberately labelled SAMPLE, not inferred building geometry or loading.
The earlier downloadable Windows EXE still contains the M0b diagnostic; it is **not**
updated by changing this source checkout and has no beam-section screen.

## Sole service API

```python
from struct_ai.services import engine_service

# Strict JSON file contents; no defaults inserted.
run = engine_service.run_beam_flexure_json(input_text)
print(run.result.status)
print(run.result.code_usage.warning)
report_markdown = engine_service.beam_flexure_report(run)
```

For typed clients use `validate_beam_flexure_design`, `design_beam_flexure`,
`validate_beam_flexure_assessment` and `assess_beam_flexure`. Do not call the private
section or material modules from the GUI/CLI/assistant. Importing the service, or
running a beam calculation, does not load Qt/OpenSees/Ollama/Torch/NumPy.

## Input conventions

- Every field shown in the sample is explicit and required, including `flange:null`.
- mm, mm², N/mm² for section/materials; input factored signed moment in **kN m**.
  Internally the calculation uses **N mm**, with conversion only in `units.py`.
- Moment >0: top compression / bottom tension. Moment <0 reverses the faces.
- Centroid offsets are measured from each layer's **own face**, not nominal covers.
- Actions are already factored ULS; there is no hidden load factor or combination.
- Axial force must explicitly be zero. No moment interaction or shear/torsion check.
- Concrete strength 20..40 N/mm² is a restricted **software test domain**, not a code
  grade/exposure selection. Steel: explicit Fe415/Fe500 representative cold-worked
  curve only; no automatic TMT substitution.
- `SINGLE_ONLY` refuses a demand beyond the compatible single limit. The optional
  `ALLOW_COMPRESSION_STEEL` policy permits continuous double-steel sizing but never
  changes section dimensions.
- To assess supplied areas, use `operation:"ASSESS"`, remove `reinforcement_policy`
  and supply `reinforcement:{"top_mm2":...,"bottom_mm2":...}`.
- `PUBLIC_TEACHING_DRAFT` and `acknowledge_unverified:true` are required for draft
  calculations. `CURRENT_AMENDED_CODE` is explicitly blocked by missing applicability
  data; a scalar edit cannot enable an unimplemented compliance workflow.

## Read the output correctly

`DRAFT_SECTION_CHECKS_PASS` means only the listed checks pass in the specified draft
model. It is **not** a safe-building conclusion. A failed strength or reinforcement
check is retained as `REVISE_SECTION`, with literal unrounded demand/capacity/ratio.
Other unsupported/invalid calculations return no fabricated result. Minimum provision
can govern, so its capacity may exceed the requested moment substantially. Continuous
areas must not be mistaken for selected bars or evidence that bars fit in the section.

Results/report retain the exact warning **UNVERIFIED CODE CONSTANTS USED: N**. N is the
number of **distinct records actually consumed**, not the catalogue inventory count.
Use `python tools/list_unverified.py` for the separate complete inventory, including
unused and null records. Results include exact data and result hashes; displayed
rounding does not alter checks.

Building design, M2–M15 checks/workflows, Ollama integration and an engineering installer
are not implemented by M1. The tested OpenSees backend is retained for the selected
internal-use intent; a replacement has not been validated or selected.
