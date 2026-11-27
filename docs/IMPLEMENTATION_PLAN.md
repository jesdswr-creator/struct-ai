# Approved scope: M0 + M0b

The user approved the foundation/packaging plan on 2026-11-27. This is not an
approval to invent code data or bypass milestone acceptance. M1–M15 remain future
work. No building design is available in these milestones.

## M0, before implementation

- Build unit conversions, structured exceptions, immutable numerical checks.
- Add a fail-closed JSON code registry, actual-use provenance and unverified audit.
- Provide only a service boundary, with unavailable engineering methods refusing.
- Test with independent arithmetic and synthetic, explicitly non-code fixtures.
- Run pytest and ruff after each coherent step; report before starting M0b.
- Add no engineering constants: all four initial catalogues are deliberately empty.

## M0b, after M0 is green and reported

- Use a real two-node OpenSeesPy elastic cantilever as a diagnostic, not a design.
- Compare against an independently calculated analytical solution; repeat the run.
- Build a small PySide6 Essentials window; all GUI calls go through the service.
- Run the solver in an isolated process with progress, cancellation and loud errors.
- Pin Python 3.12 / OpenSeesPy 3.7.1.2 for Windows; test the actual package combination.
- Build PyInstaller onedir and a frozen selftest, Windows CI and screenshot tooling.
- Capture light/dark screenshots; request design feedback before any later UI work.
- Record clean-Windows execution as pending unless it has actually been observed.

## Explicit assumptions and unresolved questions

- Proposed distribution target: Windows 11 x64. Windows 10 and ARM64 are not certified.
- Linux development tests are supplementary; they are not Windows acceptance.
- Local host initially supplies Python 3.11.2. The selected Windows OpenSeesPy wheel
  specifies Python ~=3.12.0, so Windows builds use Python 3.12, not the host version.
- Exact G+4-only vs up-to-six-storey scope, structural height convention, geometry,
  occupancy, site/soil/seismic factors, infill treatment, materials, exposure, cover,
  aggregate size, fire resistance and optional wind remain unanswered.
- Authorised code values/clauses and amendments have not been supplied.
- No LLM is installed or used, and no weights will be bundled.
- Determinism is defined for pinned input/data/engine environments. Cross-platform
  numerical comparisons require separately documented tolerances.
- No Python-free Windows VM is available in the local Linux sandbox. A reproducible
  verification procedure and evidence checklist must accompany the artifact.
