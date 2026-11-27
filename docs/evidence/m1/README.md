# M1 verification evidence — 2026-11-27

Tested implementation: **66637358ded77062d2898cc42bfeb2cbed0966d8**, branch
`arena/4feb7a32-struct-ai`.

| Observed gate | Result |
|---|---|
| Windows source suite | **342 passed, 14.90 s**; Ruff/83 formatted files, pip check, audit/source selftest passed |
| Ubuntu 24.04 source suite | **342 passed, 13.38 s**; Ruff/83 formatted files, pip check, audit/source selftest passed |
| Windows packaging suite | **342 passed, 13.29 s**; actual onedir build passed |
| Existing frozen headless + real GUI-worker diagnostic | **PASS**, native Qt `windows`, source/frozen equality |
| New binary publication | **Not performed** — intentional push-run upload guard |
| Frozen beam/DOCX/DXF engineering selftest | **Not implemented** (M14), not implied by the diagnostic smoke |
| M1 beam GUI / new clean-machine acceptance | **Not performed**; M1 is a source service/CLI increment |
| Current-code verification | **Not established**; all adopted data unverified, amendment applicability missing |

Runs: [source quality](https://github.com/jesdswr-creator/struct-ai/actions/runs/45999677118)
and [Windows packaging](https://github.com/jesdswr-creator/struct-ai/actions/runs/45999677169).
Exact API metadata, job IDs, quality annotations and the frozen diagnostic summary are
preserved in [ci-6663735.json](ci-6663735.json). No pytest skips were reported by these
full quality summaries; the skipped **binary upload workflow step** is not a test skip.

The evidence was retrieved through GitHub REST run/job metadata and check-run annotations.
Full build-artifact ZIPs/log archives were not downloaded or independently rehashed here.
EXE/runtime-manifest hashes in the summary are CI-computed, not local archive verification.
The native host was Windows Server 2025 / Python 3.12.10, not a Python-free Windows 11 VM.
The frozen result is still a five-check, ten-resource **M0b solver diagnostic**. Its result
hash changed with the now-nonempty catalogue digest and truthful limitation wording;
its analytical numbers and tolerances were not modified.

The local restricted Linux sandbox passed **326 selected headless tests**; 15 GUI tests
were not selected and one GUI selftest was deselected because libGL is absent. The full
342-case CI gate above includes these Qt-dependent tests. No skip workaround was added.

M1 adds independent rational concrete integration, independent flange quadrature, curve
primitive/interpolation checks, compression steel/displaced concrete, signed geometry,
actual-width/coupling/overall-D checks, unit endpoint regressions, typed failures,
missing-data provenance, real CLI, fresh-process determinism and Hypothesis properties.
Those validate the **specified draft implementation**, not the correctness of an
unreviewed standard interpretation or fitness for a real building.

Data: **33 unverified records (32 numeric, one missing)**, digest
`f46cc15afdd50d1ad58d6e0055c49cb09fc8a55d02a47bb5e633d5b3a6460014`.
[Source/basis review and derivations](../../research/M1_DRAFT_DESIGN_BASIS.md).

The user's earlier clean-Windows M0b test report remains a separate
[user-report record](../m0b/user-reported-windows-acceptance-2026-11-27.json). It is not
rewritten as independently reviewed evidence or as a test of this newer M1 service.
