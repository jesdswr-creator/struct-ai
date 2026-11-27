# struct_ai

**DRAFT · M1 flexure + scoped M2 component checks · NOT FOR BUILDING DESIGN**

A staged structural engineering application with a deterministic Python engine and a
service-only desktop interface. The desktop runs a **real, independently checked
two-node OpenSeesPy cantilever diagnostic**. The source service/CLI now also provides
**unverified rectangular, doubly reinforced and T/L beam-section flexure** with traceable
public-source data, plus scoped shear/torsion, straight development length, base cover/clear
spacing and checks of supplied service deflections. It does **not** analyse or design a complete RC building, certify
current-code compliance, select bars or produce construction documents.

> DRAFT: must be reviewed and sealed by a licensed structural engineer.
> Do not use this prototype to issue designs or claim code compliance.

| Milestone | Current status |
|---|---|
| M0 — units, errors, checks, code provenance, service, tests | Complete; Linux and Windows CI pass |
| M0b — diagnostic desktop and packaging implementation | Implemented; Windows build and both frozen selftests pass |
| M0b — clean Windows/no-Python acceptance | **User reports full clean-machine success**; OS/JSON/screenshot audit evidence outstanding |
| M1 — beam-section flexure | Draft service/file commands implemented; included in the current **526-test Windows/Linux gates** |
| M2 — beam component checks | Scoped draft implemented and EXE published; **526 full tests pass on each OS**, 15 frozen section paths pass; full M2 acceptance remains open |
| M3–M15 — remaining engineering, building workflow, Ollama, full GUI, installer | Not implemented |

[Use the M1 section service](docs/M1_BEAM_FLEXURE.md) ·
[M2 component checks and limits](docs/M2_BEAM_CHECKS.md) ·
[Section-enabled Windows bundle instructions](docs/WINDOWS_DRAFT_BUNDLE.md) ·
[Draft source basis and independent derivations](docs/research/M1_DRAFT_DESIGN_BASIS.md).
The exact unverified-warning count accompanies every section result/report.
[Current M2 source/build/publication evidence](docs/evidence/m2/README.md), tested implementation
`c60b6e9`; [earlier M1 evidence](docs/evidence/m1/README.md) remains historical.

**Historical M0b baseline:** 206 tests passed on both Windows and Linux. Windows CI
built the onedir executable and passed both frozen selftests using the native Windows
Qt plugin, with matching source/frozen result hashes.
The CI host was Windows Server 2025—not a clean Windows 11 machine without Python.
[Recorded CI evidence](docs/evidence/m0b/windows-ci-2026-11-27/README.md) ·
[Milestone report and remaining acceptance gates](MILESTONE_REPORT.md).
A temporary diagnostic binary has now been uploaded with the user's explicit approval;
automatic push/PR binary uploads remain disabled. Commercial release/licensing review is
still outstanding.

## Windows draft EXE

**[Download the section-enabled EXE + required runtime — ZIP, about 55 MB](https://github.com/jesdswr-creator/struct-ai/actions/runs/46004913427/artifacts/15202120175)**

Built from **`c60b6e9`** in [successful manual run 46004913427](https://github.com/jesdswr-creator/struct-ai/actions/runs/46004913427).
The artifact expires **2026-12-04 13:12:55 UTC**; GitHub sign-in may be required.
Choose **Extract All** and keep `_internal` beside `struct_ai.exe`. Open the EXE for
the diagnostic desktop, or explicitly confirm **`RUN-SAMPLE-SECTIONS.cmd`** to try
the synthetic flexure/torsion samples and read their JSON/Markdown reports.

The **Windows draft EXE** workflow passed 526 tests, the actual onedir build, native
headless/GUI diagnostics and **15 frozen section-command paths** with source-result/report
comparison. Both binary and evidence uploads succeeded. Automatic push/PR binary uploads
remain disabled; publication requires manual `publish_draft_binary=true`.
[Instructions, hashes and exact scope](docs/WINDOWS_DRAFT_BUNDLE.md) ·
[Persistent CI/publication evidence](docs/evidence/m2/README.md).

**This is an unsigned draft test bundle, not a complete structural-design app or an
installer.** All code constants remain unverified; full M2 acceptance, columns, building
analysis/design, seismic design, Ollama and the full design GUI are not complete.
Clean-machine testing of this newer bundle is still required; it does not inherit the
earlier M0b acceptance.

### Earlier diagnostic-only download (historical)

**[Download EXE + required runtime files — ZIP, about 54 MB](https://github.com/jesdswr-creator/struct-ai/actions/runs/45991582390/artifacts/15193683657)**

Choose **Extract All**, then double-click **`struct_ai.exe`** and click **Run diagnostic**.
Keep the `_internal` folder and other files beside the EXE. This is a portable Windows x64
benchmark, not a source ZIP, MSI installer or building-design application. **This earlier
binary does not contain the new M1 section service/UI or Ollama.** The download
expires **2026-12-04 11:35:32 UTC**; GitHub may require sign-in.
[Launch instructions, hashes and troubleshooting](docs/TEST_WINDOWS_EXE.md).
The executable is unsigned; do not disable security protections if it is blocked.

## Desktop preview

Historical M0b PySide6 captures of a real solver run—not mockups, new beam screens or
made-up building results. Current CI captures were generated but not visually reviewed here:

![Light diagnostic workspace](docs/screenshots/m0b/light-1366x768-scale-1-checked.png)

[Dark theme](docs/screenshots/m0b/dark-1366x768-scale-1-checked.png) ·
[Empty initial state](docs/screenshots/m0b/light-1366x768-scale-1-idle.png) ·
[Milestone report and evidence](MILESTONE_REPORT.md)

The app starts with **empty result fields**. Run diagnostic explicitly to produce
numbers. Editing an input clears stale results. The disabled Building design action
explains that engineering milestones are incomplete. There is no LLM dependency,
network service or model download needed to use the implemented diagnostic.

## Supported development/build versions

**Windows target (proposed): Windows 11 x64, CPython 3.12.10 x64.**

- OpenSeesPy / Windows native wheel: **3.7.1.2**.
- PySide6 **Essentials** / Shiboken: **6.8.3** — no PyQt or QtWebEngine.
- PyInstaller: **6.14.2**, hooks **2025.5**, **onedir** and windowed.
- Pydantic: **2.11.7**. Exact runtime/test/build pins: `requirements.lock`.

The Windows OpenSees wheel requires Python `~=3.12.0` and its loader enforces Python
3.12 / 64-bit, despite the broad wheel filename. Do not substitute Python 3.11 or
3.13 for a Windows build. Supplementary Linux tests here use Python 3.11.2 and the
pinned Linux native wheel; Linux evidence is not Windows acceptance.

### Windows source checkout

In Command Prompt, with CPython 3.12 x64 installed:

```bat
py -3.12 -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.lock
.venv\Scripts\python.exe -m pip install --no-deps --no-build-isolation -e .
.venv\Scripts\python.exe -m struct_ai
```

The synthetic form inputs belong only to a software benchmark. They are **not** default
building geometry or material values. Positive force acts in global +X; negative force
reverses it. No self-weight, mass or shear deformation is included.

### Tests and audit

```bat
set QT_QPA_PLATFORM=offscreen
set PYTEST_QT_API=pyside6
set PYTHONUTF8=1
.venv\Scripts\python.exe tools\check.py
.venv\Scripts\python.exe tools\list_unverified.py
.venv\Scripts\python.exe -m struct_ai --selftest --output .artifacts\source-selftest.json
.venv\Scripts\python.exe -m struct_ai --gui-selftest --output .artifacts\source-gui-selftest.json
```

`tools/check.py` runs pytest, ruff lint and ruff format checks, returning nonzero on
failure. The full CI gates at **`c60b6e9` passed 526 tests, zero skipped, on each of
Windows and Ubuntu 24.04**. They exercise actual OpenSees, spawned workers, Qt widgets,
independent section arithmetic, quadrature, property checks, strict inputs, provenance,
real CLI paths and packaging helpers. Ruff/format and `pip check` also passed.

The restricted local sandbox passed **510 headless tests**. Its graphics prerequisites
remain absent: the GUI directory and one GUI-dependent integration test are excluded
locally, not skipped or removed from full CI. Actual Windows frozen diagnostics and
15 section-command paths also passed before the manual artifact upload.
[Current CI/publication evidence](docs/evidence/m2/README.md) and the
[milestone report](MILESTONE_REPORT.md) preserve the initial failure and subsequent
repairs. These test implemented, explicitly unverified draft behaviour—not controlled
textbook values, complete-code coverage or current-code compliance.

To return to the ordinary Windows display after offscreen tests, run
`set QT_QPA_PLATFORM=` before launching the source app normally.

### Linux development

Install the matching Python development/shared-runtime package and native prerequisites
(`libgl1`, `libegl1`, `libxkbcommon0`, `libdbus-1-3`, `libblas3`, `liblapack3`) through your
OS package manager. Create a Python 3.11/3.12 venv, install the same lock file, then use
`QT_QPA_PLATFORM=offscreen PYTEST_QT_API=pyside6 python tools/check.py` in headless CI.
A Linux freeze additionally needs a compatible `libpython` shared library.
See [packaging notes](docs/packaging-spike.md) for the restricted sandbox's supplementary
test environment and its limitations; scratch native dependencies are not committed.

## Packaging and Windows acceptance

```bat
packaging\build_windows.bat
```

This **legacy local diagnostic recipe** runs pinned installation → pytest/ruff →
PyInstaller → real frozen headless and GUI-worker selftests. It produces an **entire
onedir folder**, not a standalone EXE. Unlike the current Actions workflow, this local
recipe does **not** copy the section SAMPLE launcher/docs, run the separate section smoke
or inventory the final distribution. Use the Actions artifact above for the documented
section-enabled bundle; do not infer equivalent section-packaging verification from the
legacy script alone.
The Windows smoke runner exercises the native Windows Qt platform plugin with Python
removed from PATH; Linux smoke uses offscreen rendering. It compares headless/GUI
result hashes and removes external Python/library/plugin path overrides. CI builds/tests
now run automatically; binary artifact upload is a separate manual opt-in after
distribution-permission review. In a public repository, a diagnostic
artifact's label is not an access restriction.

**The user reports clean-Windows acceptance:** no Python/Qt/OpenSees/Ollama installed,
five diagnostic checks and both documented selftests passed. This is not independent
review of a particular OS version or the JSON reports. Retain actual exit codes, both
reports, OS/build, hashes and native screenshots for audit; see the
[separate user report](docs/evidence/m0b/user-reported-windows-acceptance-2026-11-27.json)
and [repeatable checklist](docs/packaging-spike.md#clean-windows-acceptance--must-actually-be-performed).
Frozen section file commands now have a separate smoke gate; the complete M14
beam/DOCX/DXF/export selftest and Inno Setup installer remain unimplemented.

The spike is unsigned. See the packaging notes for antivirus/SmartScreen precautions
and a future code-signing plan. Do not disable security protections to run a build.

### Distribution licence blocker

The actual bundled **OpenSeesPy licence requires a separate licence for commercial
redistribution**. Internal/research/education permissions do not establish permission
to ship a commercial application. PySide6 is used under its LGPL alternative with
replaceable dynamic libraries; Inter includes its SIL OFL licence. See
[third-party notices](struct_ai/gui/resources/NOTICES.md). A release licence audit is
still required; no public commercial installer/release was created.

## Architecture and traceability

```text
Client (desktop / CLI / future LLM tool)
    → services/engine_service.py   [only engine entry point]
    → strict validated input
    → deterministic solver + independent verification
    → immutable result + CheckResults + actual-use code provenance + SHA-256
    → display/export of those same objects
```

The implemented schemas are `DiagnosticInput` and explicit **beam-section** design/
assessment inputs, **not** a substitute `BuildingInput`. `design_building()` refuses
every request with `NotImplementedError`. Slab, footing, staircase design and BuildingInput
project I/O also refuse explicitly. M1 executes deterministic section mathematics without
loading OpenSees, Qt or an LLM; it never infers building actions.

The diagnostic uses fixed stages: validation → model → linear static analysis →
independent analytical/equilibrium checks. The GUI only supplies text fields and
renders service outputs. A **QThread** owns service-process startup, polling and cleanup;
OpenSees itself runs in an isolated spawned child. UI signals return to the main thread.
Cancellation terminates the child and suppresses even an already-queued late result.
OpenSees domains are wiped before/after runs and concurrent in-process calls are rejected.

Each numerical check retains `name`, `ok`, `clause`, `demand`, `capacity`, `ratio` and
`units`. Diagnostic checks compare **numerical error** to a documented numerical error
budget, not member utilisation. Raw signed solver outputs are preserved. Conversions
between kN/m and N/mm/N/mm² live only in `struct_ai/units.py`.

Canonical payloads exclude timestamps and machine-dependent paths. Identical validated
inputs, code-data revision and pinned engine environment reproduce identical results;
that is tested in-process, across source workers and across frozen headless/GUI paths.
Different OS/toolchain environments are not assumed bit-identical.

## Code source-of-truth policy

The user authorised cited public-source **draft numerical implementation**. IS 456 now
has **159 unverified records** (155 numeric, four missing values/workflows); the
other three code namespaces remain empty. Required absent/null values raise
`MissingCodeValue`; incomplete metadata or mismatched units also block consumption.
No remembered value or amendment-completeness claim is silently substituted.

Every shipped record has `verified=false`, `verified_by=null`, explicit units,
code edition and clause references. The actual-use tracker records distinct consumed
constants and emits `UNVERIFIED CODE CONSTANTS USED: N` when N > 0. Audit inventory
counts and per-run usage counts are deliberately different. See
[the code-data policy](docs/CODE_DATA_POLICY.md).

## Screenshots, logs and next gates

```sh
QT_QPA_PLATFORM=offscreen python tools/make_screenshots.py
QT_QPA_PLATFORM=offscreen python tools/make_screenshots.py --scale 1.25 --sizes 1366x768 --checked-only
QT_QPA_PLATFORM=offscreen python tools/make_screenshots.py --scale 1.5 --sizes 1366x768 --checked-only
```

The 12 captures cover the one implemented page in both themes at 1366×768 and
1920×1080 logical pixels, plus scaled captures. Manifests record physical pixel sizes
and actual result hashes. KPI size/contrast/accessibility tests run automatically.
Native Windows DPI testing and design feedback are still required before later UI work.

Logs: `%APPDATA%\struct_ai\logs` on Windows, XDG state storage on Linux. Copy diagnostics
shows versions and the log path without exposing environment secrets.

Current engineering work: **M2 scoped checks** plus actual section-enabled Windows
packaging. Fire/crack-spacing/chart routes remain blocked; M3–M15 are not advanced. Source review remains mandatory. Retain the
clean-machine audit evidence; resolve building design-basis inputs and current
amendments. The selected use is **internal** and OpenSees is retained; commercial
redistribution still requires separate review. Ollama integration remains a later
bounded assistant milestone with a form-only fallback, not an engineering calculator.
**A passing diagnostic or draft section check is not building-design approval.**
See [known limitations](docs/KNOWN_LIMITATIONS.md) and the
[human-verification checklist](MILESTONE_REPORT.md).
