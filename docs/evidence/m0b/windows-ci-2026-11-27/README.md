# Actual Windows CI evidence — 2026-11-27

Tested implementation revision: `8768572fbaa38f99bdd5f1a2bf19bfda1b46db64`.
This is **CI build/runtime evidence, not clean Windows/no-Python acceptance**.

## Observed successful runs

| Run / job | Outcome |
|---|---|
| [Tests and lint — 45986697648](https://github.com/jesdswr-creator/struct-ai/actions/runs/45986697648), Ubuntu 24.04 | 206 passed in 6.22 s; Ruff, pip consistency, audit and source selftest passed |
| Same run, Windows | 206 passed in 13.30 s; Ruff, pip consistency, audit and source selftest passed |
| [Windows packaging — 45986697708](https://github.com/jesdswr-creator/struct-ai/actions/runs/45986697708) | 206 passed in 12.54 s; actual onedir build, source and both frozen selftests passed |

No pytest cases were skipped. The optional binary-publication **workflow step** was
intentionally not run; this is not a skipped engineering or dependency test.

The frozen host reported **Windows Server 2025, build 10.0.26100**, CPython 3.12.10,
and the native Qt **`windows`** platform plugin. The smoke tool removed external
Python/library/plugin overrides and Python from PATH, used an unrelated working directory
and isolated application-data directories, and compared source/headless-frozen/GUI-frozen
result hashes. Ten required resources and five numerical checks were exercised.

Result hash:

```text
33431478a4aa16c5d5c11c4fcbe09c69dfd57c00c00823b6bce440893fb9c1b0
```

Runtime inventory: **297 regular files, zero symlinks, 129,441,769 file bytes** before
handoff documents and evidence were appended. This is neither an installer size nor a
RAM/performance measurement. Executable SHA-256:

```text
5788ef8a3cbb53dfa47409e768c7ad7206ebd974e171628e06cbbd89267c3a5c
```

The build log still contains API-set DLL resolution warnings, including an optional
`qdirect2d` dependency. Successful use of `qwindows` does not certify every plugin or
Windows version. The exact runtime must still be tested on the proposed Windows 11 target.

## What is saved here

- [runs.json](runs.json): actual run/job outcomes, step results, artifact metadata and expiry.
- [annotations.json](annotations.json): API-returned command summaries and bounded log tails.
- [frozen-summary.json](frozen-summary.json): actual smoke JSON parsed from its CI annotation;
  includes executable, report and runtime-manifest hashes. It was not reconstructed from
  the historical Linux results.
- [source-manifest.json](source-manifest.json): 92 tracked source/test/build/resource file
  hashes at the tested revision; byte basis and Windows batch line-ending caveat recorded.
- [preceding-runs.json](preceding-runs.json): preceding failures/successes, not erased by reruns.
- [provenance.json](provenance.json): retrieval method and explicit acceptance limitations.

The sandbox cannot download the separate redirected Actions storage host. The full Windows
selftest JSON payloads, bundle inventory, command/application logs and eight offscreen
source-widget captures remain in the CI artifact; **they were not downloaded or visually
reviewed here**. The summary and annotations above are persistently saved in Git.

Evidence artifact: `m0b-windows-evidence`, ID `15191732791`, 946,795 compressed bytes.
The recorded API expiry is **2026-12-04 11:00:59 UTC**. Retrieve it from the packaging run
before expiration if full raw evidence is needed. Source job artifacts and their expiry
are also recorded in `runs.json`. This artifact contains evidence, **not a Windows EXE**.

## Acceptance still required

- [ ] Separate clean Windows 11 x64 execution with no installed Python/Qt/OpenSees/Ollama.
- [ ] Both local-build and authorised CI-binary acceptance records, native screenshots,
      tester/OS identity and hashes; follow [the checklist](../../../packaging-spike.md).
- [ ] Native DPI, manual interaction, accessibility, cold-start/idle-memory and AV checks.
- [ ] Distribution/licensing review before enabling any public binary upload.
- [ ] Engineer-supplied controlled code data and unresolved building design-basis decisions.

**M0b is not accepted. M1 has not started. No building design or code-compliance result exists.**
