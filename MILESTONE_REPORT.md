# Milestone report

## Latest continuation — Windows gate still blocked (2026-11-27)

The resumed checkout contained the implementation files but its Git HEAD was the original
`565b834` baseline; the earlier unpublished commit objects and excluded native caches/build
products were not present. All **86 recorded source/test/build files** and the saved evidence
files were checked against their SHA-256 manifests and matched. The restored implementation
was checkpointed as `ff496b8`; historical evidence below is preserved, not rewritten as a
new execution. `.gitattributes` now keeps resource text hashes stable across platforms while
preserving the upstream OFL notice byte-for-byte.

Fresh checks: **174 headless unit/integration tests passed**, Ruff and `pip check` passed,
and the real OpenSees library loaded. This is **not a fresh full 190-test gate**: the current
sandbox lacks the excluded Linux graphics prerequisites (`libGL.so.1` is the first missing
library), so 16 Qt-dependent tests and a new frozen build were not run. The earlier full
190-test/GUI/frozen evidence remains valid historical evidence, not new Windows acceptance.

A push of the baseline branch succeeded, but the subsequent **implementation/workflow push
was rejected again**: the GitHub App lacks `workflows` permission. The remote branch still
points to the initial README-only baseline. No Windows CI run, Windows binary or clean-VM
acceptance was produced. Reauthorising the repository connection with workflow-write access
is required; no permission bypass or deletion of the required workflows was attempted.

See [continuation record](docs/evidence/m0b/continuation-2026-11-27.json) and
[fresh headless test output](docs/evidence/m0b/headless-continuation-tests.txt).
M1 remains blocked by milestone acceptance and pending controlled-code data review.

After the user reported updating access, the same implementation push was retried and
GitHub returned the same missing-`workflows`-permission rejection. See
[repository-access troubleshooting](docs/GITHUB_WORKFLOW_ACCESS.md); no Windows CI execution
is implied by the user's confirmation alone.

### Requested public-reference research

The user selected public-reference research for review. Completed:
[review notes and M1 intake checklist](docs/research/M1_PUBLIC_REFERENCES.md) and
[a seven-entry source register](docs/research/M1_SOURCE_REGISTER.json). Four NPTEL lesson
texts were read; BIS primary-metadata pages returned HTTP 500 on direct retrieval and are
explicitly marked search-index-only. Source-specific extraction/interpretation issues and
an edition mismatch are flagged, not silently corrected or adopted.

All source entries remain unverified and **not adopted by the engine**. No PDF or standard
prose was copied into the project. The actual-use catalogue audit still contains zero
records with unchanged digest `21ad9599cc2c803b16200e8bee4f7bf30bafbccb6bd394aeee05abe70024fdcc`.
No M1 implementation or acceptance result is claimed.

A source-only ZIP was provided through the file viewer as an alternative local Windows
build handoff. It contains no EXE and is not a substitute for the documented clean-machine
execution. The 174-test continuation check remains a headless subset, not a full GUI gate.

## M0 — COMPLETE (local evidence, 2026-11-27)

### Built

- Installable `struct_ai` package, exact dependency lock and cross-platform CI definition.
- Unit conversions in one module, with explicit kN/m and N/mm/N/mm² contracts.
- Typed engineering errors with serialisable clause/value/limit context.
- Strict, immutable numerical `CheckResult`; contradictory ratios/statuses rejected.
- Canonical JSON and SHA-256 hashes; non-finite values rejected.
- Strict code-data registry, four required catalogues, missing-value blocking,
  duplicate-key/identifier detection and isolated actual-use provenance.
- `tools/list_unverified.py`, service-only CLI access and truthful empty-catalogue output.
- Unimplemented building pipeline and slab/footing/staircase design explicitly refuse.

### Clauses and constants

**No Indian Standard clauses implemented; zero engineering constants added.**
Catalogues are deliberately empty. Mathematical conversions are not code constants.
Synthetic loader test records are labelled non-code and exist only in temporary test data.

### Test evidence

Local host: Linux x86_64, CPython 3.11.2. Executed:

```text
python tools/check.py
115 passed, 0 skipped
ruff check: All checks passed
ruff format --check: 27 files already formatted
python tools/list_unverified.py
No engineering code constants implemented. Building design is unavailable.
An empty catalogue is NOT evidence of verified design.
python -m pip check
No broken requirements found.
python -m pip install --no-deps --no-build-isolation -e .
Successful editable package installation.
```

The earlier core step passed 76 tests before its commit. No expected numerical value
was altered to repair an implementation failure. No design/solver function was mocked.

### Assumptions and limitations

- No BuildingInput/analysis/design/verification/report workflow is available yet.
- `CheckResult` represents non-negative required demand versus positive available
  capacity. Signed actions remain analysis data; zero/undefined capacity must raise,
  not become infinity. Ratio representation tolerance does not relax pass/fail.
- Foundation tests are local evidence. CI is configured but not claimed to have run.
- No UI exists at M0, so no UI screenshot claim applies.

### Human engineer checklist

- [ ] Supply authorised numerical code data, clause references and amendments before M1.
- [ ] Resolve exact scope, storey/height definitions and irregularity criteria.
- [ ] Supply site/soil, occupancy, materials, durability/cover and infill decisions.
- [ ] Review unit conventions and required/provided utilisation representation.
- [ ] Confirm the Windows 11 x64 target and arrange clean-Windows acceptance testing.

## M0b — IMPLEMENTED; WINDOWS ACCEPTANCE PENDING (2026-11-27)

**Not marked complete:** the mandatory clean-Windows/no-Python criterion has not been
observed. The implementation is prepared and supplementary Linux source/frozen checks
pass. Windows-specific behaviour is not validated. M1 and later have not started.
No production engineering results are available.

### Built

- A real two-node OpenSeesPy elastic cantilever through the sole service entry point.
- An independent closed-form path for displacement/rotation and global equilibrium.
- Fixed stages, strict bounded synthetic inputs, raw signed solver observations,
  immutable CheckResults, data provenance and canonical result hashes.
- Run-local isolated processes supervised by an actual **QThread**. Process startup,
  polling and cleanup stay off the UI thread; queued signals return to the UI. Cancel
  suppresses even an already-queued late result. Shutdown reaps the thread and child.
- Explicit error propagation, domain cleanup and refusal of overlapping in-process
  OpenSees domains. No QThread termination or forced thread destruction is used.
- PySide6 Essentials desktop: in-house Light/Dark tokens, remembered theme, Inter/OFL,
  real progress, cancellation, clause/value/limit error details and copy action,
  accessible controls, model/proxy checks table, no initial fake results, stale-result
  invalidation, and persistent DRAFT / DIAGNOSTIC ONLY notices.
- A windowed onedir spec with native OpenSees collection, resources, icon/version info,
  multiprocessing freeze support, local logs and separate headless/GUI selftests.
- Pinned Windows build script, Windows CI definition, frozen smoke runner and explicit
  clean-VM procedure. No installer or Windows binary is claimed to have been generated.

### Clauses and constants

**No Indian Standard clauses implemented; zero engineering constants added.**
All four shipped code catalogues remain empty. Synthetic benchmark parameters and
software-domain/numerical tolerances are explicitly not code values.

### Verification and observed results

The synthetic benchmark uses P=12 kN, L=3 m, E=25,000,000 kN/m² and I=0.0008 m⁴.
Independent integration of EI x''=P(L−y), with fixed-base conditions, gives:

- x(L)=PL³/(3EI)=0.0054 m;
- global Z rotation = −PL²/(2EI)=−0.0027 rad;
- global reactions Rx=−12 kN, Ry=0, Mz=PL=36 kN·m.

The real solver matches these and all five numerical-error CheckResults pass.
No expected engineering/code value was invented. No engineering function was mocked.
A concurrency test's initial exact float comparison was corrected to the same 1e-12
relative comparison already used in analytical tests. The expected reactions remained
±12 kN; raw roundoff (for example −12.000000000000002 kN) was preserved.

The result hash agrees across repeated source runs, isolated source workers and both
frozen execution paths:

```text
33431478a4aa16c5d5c11c4fcbe09c69dfd57c00c00823b6bce440893fb9c1b0
```

| Gate | Observed outcome |
|---|---|
| Final pytest suite | **190 passed, 0 skipped** |
| Ruff lint / formatting | **Clean; 68 Python/spec files formatted** |
| Pinned dependency consistency | `pip check` passes |
| Source headless selftest | PASS, actual OpenSees and required resources |
| Source GUI selftest | PASS, real Qt window + spawned solver |
| Linux PyInstaller onedir build | Successful; supplementary only |
| Frozen headless and GUI selftests | PASS with external Python/library paths removed and unrelated cwd |
| Frozen GUI platform | `offscreen`; not a Linux graphical desktop or Windows certification |
| Windows build / clean VM / CI artifact | **Not run — acceptance still pending** |

The suite includes 15 real Qt tests, including thread-affinity, queued-result cancellation,
re-entry and shutdown/child-cleanup checks. Additional input-boundary tests reject wrong
top-level types, underflow-prone diagnostic forces and ambiguous catalogue schema versions;
none supplies or changes engineering-code values.

Evidence: [source selftest](docs/evidence/m0b/source-selftest.json),
[source GUI selftest](docs/evidence/m0b/source-gui-selftest.json),
[frozen selftest](docs/evidence/m0b/linux-frozen-selftest.json),
[frozen GUI selftest](docs/evidence/m0b/linux-frozen-gui-selftest.json),
[quality-gate output](docs/evidence/m0b/quality-gate.txt), and
[environment/build record](docs/evidence/m0b/environment.json).
The record identifies application/packaging commit `fd261de`, source file hashes,
the full Linux bundle inventory and actual build-log warnings. Build products and
native scratch dependencies are ignored, not committed; the 337 MiB bundle is not
archived as a persistent release. Source, tests and frozen evidence use the same code.

### Packaging findings and limits

The actual Windows wheel metadata and loader require Python 3.12 x64. Its PE imports
were inspected; runtime execution on Windows is still required. The proposed build
uses Python 3.12.10 / OpenSeesPy 3.7.1.2 / PySide6 Essentials 6.8.3 / PyInstaller 6.14.2.

The restricted Linux host lacked graphics libraries and a matching libpython shared
runtime. Native prerequisites and a CPython 3.11.2 shared runtime with the host's
builtin-module set were built for this supplementary test. The first frozen smoke
exposed a missing builtin and then a missing graphics library; those were resolved,
not skipped. The final smoke runs without the developer LD_LIBRARY_PATH. Optional
XCB/GTK plugin dependency warnings remain; only offscreen Linux execution is claimed.
See [packaging details](docs/packaging-spike.md).

The Linux bundle occupies about 337 MiB on disk. This is **not an idle-RAM measurement**.
Windows cold-start, idle-memory, antivirus and DPI acceptance are not claimed.
No QtWebEngine files or external absolute symlinks were found in the Linux bundle.

### UI evidence and feedback gate

These are real `widget.grab()` captures, not mockups. Checked states use actual solver
runs. All implemented main pages (one M0b diagnostic page, not the nine future M13
pages) were captured in both themes. Twelve captures and three manifests are saved.

![Light diagnostic](docs/screenshots/m0b/light-1366x768-scale-1-checked.png)
![Dark diagnostic](docs/screenshots/m0b/dark-1366x768-scale-1-checked.png)

| Viewport / scale | Light | Dark |
|---|---|---|
| 1366×768, idle | [Capture](docs/screenshots/m0b/light-1366x768-scale-1-idle.png) | [Capture](docs/screenshots/m0b/dark-1366x768-scale-1-idle.png) |
| 1920×1080, idle | [Capture](docs/screenshots/m0b/light-1920x1080-scale-1-idle.png) | [Capture](docs/screenshots/m0b/dark-1920x1080-scale-1-idle.png) |
| 1920×1080, checked | [Capture](docs/screenshots/m0b/light-1920x1080-scale-1-checked.png) | [Capture](docs/screenshots/m0b/dark-1920x1080-scale-1-checked.png) |
| 1366×768, 125%, checked | [Capture](docs/screenshots/m0b/light-1366x768-scale-1.25-checked.png) | [Capture](docs/screenshots/m0b/dark-1366x768-scale-1.25-checked.png) |
| 1366×768, 150%, checked | [Capture](docs/screenshots/m0b/light-1366x768-scale-1.5-checked.png) | [Capture](docs/screenshots/m0b/dark-1366x768-scale-1.5-checked.png) |

Viewports above are **logical pixels**. Manifests record physical pixel sizes and
result hashes. These do not certify native Windows scaling. The minimum 1100×700
logical window conflicts with fitting a 1366×768 physical screen at larger scaling;
resolve that trade-off before M13. Prototype content is scrollable. Contrast tests
check text token pairs ≥4.5:1 and KPI fit/accessibility tests pass.

**Please review the Light/Dark screenshots and provide design feedback before the next
UI milestone.** No user design approval has been assumed.

### External blockers and human-verification checklist

- [ ] Reconnect GitHub in Arena with workflow access. The attempted push was rejected
      because the GitHub App cannot create/update workflow files. Local commits remain
      on `arena/4feb7a32-struct-ai`; no PR/release or successful CI run is claimed.
- [ ] Build on Windows 11 x64 and run both frozen selftests on a clean VM without Python.
- [ ] After distribution-permission review, explicitly opt in to a CI binary upload and
      repeat the clean-VM test with that artifact; retain hashes, exit codes and screenshots.
      Public-repository artifacts are not made private by an "internal-use" label.
- [ ] Resolve OpenSeesPy commercial redistribution licensing and audit all dependency obligations.
- [ ] Confirm Windows versions/architecture and native DPI/performance requirements.
- [ ] Review benchmark conventions, numerical tolerances and source-to-output traceability.
- [ ] Supply authorised M1 code values, clauses/editions and applicable amendments.
- [ ] Resolve building geometry/scope, site/soil, occupancy, infill, materials, exposure,
      cover, aggregate, fire resistance and optional wind. No defaults have been selected.

The full structural design assistant is **not complete**. This deliberately stops at
the unfulfilled M0b acceptance gate rather than inventing data or bypassing verification.
