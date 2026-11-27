# Implementation plan and decisions

## Current authorisation — 2026-11-27

The user requests the complete structural-design application, optional local Ollama
integration, and a suitable alternative solver if OpenSees proves insufficient.
The agreed milestone sequence and life-safety gates still apply.

Explicit decisions, recorded without inferring missing evidence:

- **M0b clean-machine execution:** `windows_acceptance=clean_full_test`. The user
  reports no Python/Qt/OpenSees/Ollama installed, five GUI diagnostic checks passing,
  and both documented selftests passing. This is **user-reported acceptance**, not
  independent review of OS details, JSON reports or screenshots. See the separate
  [acceptance record](evidence/m0b/user-reported-windows-acceptance-2026-11-27.json).
  Historical CI/download records retain their original evidence flags.
- **Code-data route:** `engineering_data_route=authorize_public_draft_data` permits
  numerical transcription from cited public sources for **draft implementation**.
  Every record remains unverified. Missing, ambiguous and amendment-dependent values
  block the affected calculation. This supersedes research-only permission, not the
  provenance/testing policy, and does not establish current-code compliance.
- **Distribution:** `distribution_intent=internal_use`. Retain the tested OpenSees
  backend initially. PyNite's MIT licence and upstream capabilities were researched,
  but no alternative has been installed, technically validated or selected.
- **Assistant:** optional local Qwen/Ollama, form-only fallback, no bundled weights,
  no inference during deterministic analysis. No change moving M12 before the
  engineering milestones has been agreed.

## M1 — implemented draft increment; original plan below

M1 implementation `6663735` passed **342 full tests on Windows and Linux**, Ruff and the
existing native Windows packaging regression. [Evidence](evidence/m1/README.md).
The standalone draft service/CLI is implemented, not a building result or current-code
verification. The scoped M2 increment now also passes full CI and its section-enabled
Windows bundle is published; [evidence](evidence/m2/README.md). This is not full M2
acceptance or authorisation to bypass remaining engineering gates.

The announced plan was to deliver a **standalone draft beam-section service and
independent tests**, not a building result. All clients use `services/engine_service.py`.

1. Adopt only explicitly cited public-source primitives, with unverified provenance.
   Record the outstanding current-amendment review as missing, not a guessed value.
2. Strict, explicit inputs for factored signed bending, geometry, material/curve basis,
   flange participation and reinforcement policy. Reject unsupported axial action,
   material domains and missing assumptions; no default building or site values.
3. Singly/doubly reinforced rectangular and T/L section response and inverse sizing.
   Compression steel uses its actual compatible strain and displaced-concrete
   correction. No automatic section resizing or neutral-axis clamping.
4. Use a continuous parabolic-rectangular concrete curve for response, with a clearly
   identified public teaching precision convention. Derive and report the separate
   Annex G rectangular approximation coefficients (approximately 0.138 / 0.133),
   rather than silently mixing rounded equivalent-block and integrated-curve models.
5. Explicit effective-width rules/caps and flange-in-tension treatment. Longitudinal
   maximum steel uses **overall D**, not effective d. This is not ductile detailing.
6. CheckResult objects, actual-use constant snapshot/warning, deterministic result
   hashes, machine-readable output and a readable trace report. Whole-building and
   current-amended-code compliance requests remain blocked.
7. Independent hand arithmetic/quadrature, both steel grades, double reinforcement,
   flange transition/bending sign/unit/missing-data tests and Hypothesis monotonicity.
   Inverse/forward flexure-controlled round trips must be within 0.1%; minimum-steel
   governed cases are identified, not forced to reproduce an undersized demand.
8. Run pytest/Ruff after coherent increments. Record results/limitations and report
   M1 before M2. No new GUI is implied; actual UI integration remains a later gate.

The detailed source/basis note must distinguish equations actually implemented from
research leads and approximations not adopted. No standard prose, SP16 charts, PDFs,
model weights or large generated artifacts are to be bundled.

## M2 scoped implementation and EXE request — 2026-11-27

The user requested the balance of work, verification and an EXE inside GitHub Actions.
The [M2 draft source/basis plan](research/M2_DRAFT_DESIGN_BASIS.md) was announced before
implementation. Scoped checks and file commands are implemented at `c60b6e9`, with
**526 full tests passing on each of Windows and Ubuntu 24.04**, Ruff/format/pip gates,
and actual frozen diagnostic plus **15 section-command paths** passing. The local
restricted sandbox passed 510 headless cases; full CI included the 16 Qt-dependent ones.
The [authorised manual run](https://github.com/jesdswr-creator/struct-ai/actions/runs/46004913427)
also passed and uploaded the [section-enabled EXE](WINDOWS_DRAFT_BUNDLE.md).

This is not full M2 acceptance: fire cover, maximum crack spacing and chart-derived
deflection checks remain blocked. M3 is not advanced. Publication remains an unsigned,
seven-day, non-commercial onedir test artifact, not an installer. New-bundle clean-machine
acceptance and human source/engineering review remain separate requirements.

## Remaining sequence (not implemented by this plan)

M2 shear/torsion/anchorage/spacing/serviceability → M3 column interaction → M4 ductile
 detailing → M5 loads/combinations → M6 validated 3D frame → M7 seismic/modal/drift →
M8 station envelopes/sign/face checks → M9 bars/detailing/BBS → M10 independent building
verification → M11 reports/drawings → M12 bounded assistant integration → M13 desktop
workflow → M14 installer/frozen engineering selftest → M15 complete verification.
Each milestone requires a short plan, green tests and an honest report before advancing.

## Unresolved building assumptions

G+4-only versus up-to-six-storey scope, structural-height convention, geometry,
occupancy, site/soil/seismic factors, infill treatment, materials/exposure/cover,
aggregate size, fire resistance, wind selection and controlled amendment sets are
not silently selected. M1 section examples are opt-in **SAMPLE**, not project defaults.

Windows 11 x64 remains the proposed target; the user's unspecified Windows OS does
not certify that version, Windows 10 or ARM64. Windows builds use CPython 3.12.10 /
OpenSeesPy 3.7.1.2. Determinism is for pinned input/data/engine environments; numerical
cross-platform comparisons need separately documented tolerances.

## Historical approved M0/M0b plan

M0: units, structured errors, immutable checks, fail-closed registry, actual-use audit,
sole service boundary, independent synthetic tests, no code values. M0b: actual
OpenSees two-node cantilever, independent analytical checks, PySide6 Essentials with
isolated process/QThread, pinned Windows packaging, frozen tests and honest acceptance
checklist. Those implementation/CI results and the later user report remain separate
items of evidence; no earlier record is rewritten as a test it did not perform.
