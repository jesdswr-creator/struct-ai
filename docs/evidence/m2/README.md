# Scoped M2 verification and Windows draft publication — 2026-11-27

**Tested/bundled implementation:** `c60b6e933a8c514f0c33b6c3c3309caa0d033947`.
Branch: `arena/4feb7a32-struct-ai`. Later documentation commits record evidence; they
are not silently substituted for this executable's source revision.

## Download

**[Windows x64 draft EXE + required runtime](https://github.com/jesdswr-creator/struct-ai/actions/runs/46004913427/artifacts/15202120175)**

Artifact `struct-ai-windows-x64-draft-sections`: **55,037,568 bytes**, created
2026-11-27 13:12:59 UTC, expires **2026-12-04 13:12:55 UTC**. GitHub sign-in may be
required. Extract All and keep `_internal`; this is unsigned onedir, not an installer.
[Usage and remaining clean-machine checklist](../../WINDOWS_DRAFT_BUNDLE.md).

| Actual gate | Observed result |
|---|---|
| Windows source CI | **526 passed in 30.24 s**, Ruff/95-file format, pip, audit and source selftest passed |
| Ubuntu 24.04 source CI | **526 passed in 18.85 s**, Ruff/95-file format, pip, audit and source selftest passed |
| Push-run Windows packaging | **526 passed in 33.15 s**; actual onedir build, native diagnostic and section smoke passed; binary upload intentionally skipped |
| Authorised manual publication | **526 passed in 25.99 s**; all build/smoke/manifest steps and both artifact uploads passed |
| Frozen diagnostic | Headless and native-Qt GUI worker passed; five checks, ten resources, source-result comparison |
| Frozen section commands | **15 paths passed**: nine passing SAMPLEs, two `REVISE_SECTION`, three typed refusals and overwrite refusal; complete result/report comparison with source |
| Final distribution inventory | **431 files** inventoried, excluding `DRAFT-BUNDLE-MANIFEST.json` itself |
| Separate no-Python Windows acceptance | Not established for this newer bundle; earlier M0b acceptance is a distinct user report |

No tests were skipped in these full gates. A skipped Ubuntu-dependency setup step on
Windows, or a deliberately skipped push-run binary upload, is not a skipped test.
The local restricted Linux gate passed **510 tests, one deselected** (12.65 s at the
implementation commit); the GUI directory plus that selected-out integration test
account for the 16 Qt-dependent tests exercised by full CI instead. No skip markers
or passing tolerances were added to bypass failures.

- [Cross-platform run 46004541526](https://github.com/jesdswr-creator/struct-ai/actions/runs/46004541526)
  — jobs 140524287494 (Windows), 140524287895 (Ubuntu).
- [Push build 46004541424](https://github.com/jesdswr-creator/struct-ai/actions/runs/46004541424)
  — job 140524286979.
- [Manual publication 46004913427](https://github.com/jesdswr-creator/struct-ai/actions/runs/46004913427)
  — job 140525550027, explicit `publish_draft_binary=true`.
- [Evidence artifact](https://github.com/jesdswr-creator/struct-ai/actions/runs/46004913427/artifacts/15199867357)
  — `windows-draft-evidence`, 1,199,021 bytes, expires 2026-12-04 13:12:59 UTC.
- [Saved source/push metadata](ci-c60b6e9.json) · [Saved publication metadata](publication-c60b6e9.json).

## Distinct hashes and retrieval limits

- **Published artifact ZIP SHA-256 (GitHub API):**
  `16d1ded400e15f98eee3a86a8aef6bb2a250274824d3f194bdbeb46c5f62b02c`.
- **Published EXE SHA-256 (actual frozen-run evidence):**
  `16c75dff9fdbeb06d610e9af3f0cae6e2edb497d6e1d9ab971c482c000bb97ac`.
- Earlier diagnostic runtime-manifest SHA-256:
  `322d417d5397d6917f233d33180ce8d39020e85de013f821826a74505562bc8e`.
  That manifest covers 314 runtime files / 130,691,818 file bytes, before later copied
  evidence and the final 431-file distribution inventory. This is disk size, not RAM.

Metadata, job outcomes and bounded check-annotation log tails were retrieved through
the GitHub API. The ZIP was **not downloaded or independently rehashed here**; the full
431-file final manifest and all frozen report bodies were not individually reviewed
locally. Do not confuse the ZIP, EXE, runtime inventory or final inventory hashes.
The push and manual builds have different EXE bytes; only the **manual publication**
hash above identifies the downloadable EXE. Reproducible binary builds are not claimed.

## Preserved failure and repair

At `a5fb507`, Ubuntu passed **521 tests in 24.08 s**, but Windows source CI had
**520 passed, two errors in 31.72 s**, and packaging stopped at its quality gate with
**520 passed, two errors in 24.95 s**. The oversized Unicode JSON test generated a
pytest node ID larger than Windows' environment-variable limit. Explicit short IDs
fixed the transport of test names, not the oversized payload or refusal assertions.
[Failure metadata and excerpts](failed-first-gate-a5fb507.json).

A separate seeded numerical probe found 14 of 100 next-representable public-kN
shear overloads lost by conversion to stress. A failing regression preceded the
fix: compare the force in public kN as well as stress, with an exact equality
endpoint and **no passing tolerance**. A 35-example endpoint property, stirrup
outer-fibre geometry regressions and typed tiny-equivalent-moment refusal are
included in the current suite. Independent numerical expectations were not changed.

## What these results do not establish

All **159 code records remain unverified** (155 numeric/four null), with catalogue digest
`f417ef1d947cd46599faa65e17d18c5f9d03ea9a5f1f6fd4de176ab8e6694f3a`.
Software tests do not certify controlled/current-amended Indian Standard data.
Fire cover, maximum crack spacing and chart-deflection routes still fail closed;
full M2 acceptance, whole-building design, columns, seismic design, M3–M15 and
Ollama are not complete. The desktop remains a diagnostic, not a beam-design GUI.

The full future M14 DOCX/DXF/installer selftest is not implemented. The interactive
SAMPLE `.cmd` launcher itself was not observed end-to-end here; the underlying frozen
commands passed CI. Eight offscreen source-widget captures were generated, not
retrieved/visually reviewed here, and are not new beam screens or native DPI acceptance.
Windows Server 2025 with Python is not a clean no-Python Windows 11 machine. No native
startup/RAM/accessibility/AV measurements or new clean-machine acceptance is claimed.
Internal-use intent does not establish commercial redistribution rights.

**DRAFT: must be reviewed and sealed by a licensed structural engineer.**
