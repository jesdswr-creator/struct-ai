# Windows draft EXE bundle — diagnostic desktop + section file commands

**DRAFT: must be reviewed and sealed by a licensed structural engineer.**
**All code data is unverified. NOT a complete structural-design application.**

This onedir bundle contains a real `struct_ai.exe`, its Python/native runtime in
`_internal`, explicit SAMPLE input files and build/test evidence. Do not copy only
the EXE or delete `_internal`. No installed Python, Qt or Ollama is required to use
the bundled functions. Actual clean-machine testing of this newer bundle is still
required; CI has Python installed and cannot establish that acceptance by itself.

## Extract and run

1. Download the `struct-ai-windows-x64-draft-sections` artifact from the successful
   manually dispatched **Windows draft EXE** Actions run. It is retained for seven days.
2. Use **Extract All** into a normal writable folder. Keep every file/subfolder.
3. Double-click `struct_ai.exe` for the existing solver-diagnostic desktop. It is
   deliberately NOT labelled as a whole-building design screen.
4. To exercise the new calculations without Python, double-click
   **`RUN-SAMPLE-SECTIONS.cmd`** and explicitly confirm the synthetic SAMPLE run.
   It runs one rectangular flexure and one torsion/stirrup assessment, saves JSON and
   Markdown under a new `%TEMP%\struct_ai_SAMPLE_...` folder, and opens the reports in
   Notepad. These are demonstration inputs, not a project design or selected bar schedule.
5. Review every warning, failed check and limitation; never use a passing SAMPLE result
   as approval of an actual structure.

This is an unsigned **onedir test bundle, not an MSI/installer or commercial release**.
Do not disable antivirus or bypass organisation security policy. Check the source commit,
artifact metadata and hashes, scan the extracted files and seek IT approval as needed.
The OpenSees backend is retained for the confirmed internal-use intent; this does not
provide commercial redistribution permission. Licences/notices remain bundled.

## Run an explicit input in PowerShell

Use fresh paths each time. Windows windowed programs should be invoked with `Start-Process
-Wait -PassThru` so you actually wait for completion and inspect the exit code.
From the extracted bundle folder (the following relative paths contain no spaces):

```powershell
$p = Start-Process -FilePath .\struct_ai.exe -Wait -PassThru -ArgumentList @(
  '--beam-checks', '.\examples\SAMPLE_beam_torsion.json',
  '--output', '.\torsion-result.json', '--report', '.\torsion-report.md',
  '--error-output', '.\torsion-error.json'
)
$p.ExitCode
```

For flexure use `--beam-flexure` and an M1 SAMPLE JSON, e.g.
`examples\SAMPLE_beam_rectangular.json`. Quote argument paths containing spaces when
using Start-Process; the included `.cmd` launcher already handles a bundle path with spaces.

- Exit **0**: the requested draft checks passed, not code verification.
- Exit **1**: completed assessment with `REVISE_SECTION`; read failed checks in the result.
- Exit **2**: input/data/scope/file error; inspect `--error-output` and application logs.
- Output/report/error paths must be distinct and new. No existing input or result is
  overwritten. A file-writing failure may leave partial output: nonzero exit is not success.

Implemented M2 operations: `SHEAR_TORSION`, `DEVELOPMENT_LENGTH`, `COVER_SPACING`,
`DEFLECTION_LIMITS`. See the copied `M1-BEAM-FLEXURE.md`, `M2-BEAM-CHECKS.md` and example
JSON for required inputs. Fire cover, maximum crack spacing and deflection-chart routes
fail closed; direct deflection checks require documented **externally calculated** values.

## Diagnostic selftests

```powershell
$p = Start-Process .\struct_ai.exe -Wait -PassThru -ArgumentList '--selftest --output selftest.json'
$p.ExitCode
$p = Start-Process .\struct_ai.exe -Wait -PassThru -ArgumentList '--gui-selftest --output gui-selftest.json'
$p.ExitCode
```

These two switches remain **M0b solver/GUI diagnostics**, not full building-design tests.
The separate CI `section-commands` evidence covers actual frozen section commands.
The full future M14 beam/DOCX/DXF/installer selftest is not complete.

## What Actions verifies before upload

- Exact-pinned environment, pip consistency, full tests, Ruff and formatting.
- Real source solver diagnostic, actual windowed onedir build, headless and native-Qt
  GUI/worker frozen tests with source/frozen comparison and restricted environment paths.
- **15 real section-command paths:** nine explicitly requested passing samples, two
  deliberately failed assessments, three typed input/data refusals and overwrite refusal.
  Successful/failed-assessment payloads and Markdown traces must equal source execution
  on the same Windows host. No fake solver or mocked calculation substitutes are used.
- Final `DRAFT-BUNDLE-MANIFEST.json` hashes all distribution files except itself,
  including copied evidence/docs/samples. Earlier runtime-smoke inventory is not a hash
  of the later GitHub artifact ZIP. GitHub reports the ZIP digest separately.
- The build upload happens only after all these steps pass and manual publication is true.

The tests verify implemented draft behaviour, not current-standard applicability,
controlled numerical data or suitability of a real building. There is no new beam GUI,
whole-building design, Ollama, columns, seismic design, BBS/DXF/DOCX export or installer.

## Feedback/evidence needed

On a separate Windows machine without Python/Qt/OpenSees/Ollama, record OS/build, source
commit/EXE hash, both selftest JSONs/exit codes and the two SAMPLE report/results. Report
startup errors without dismissing them; logs are under `%APPDATA%\struct_ai\logs`.
Earlier user-reported clean-machine M0b acceptance is preserved, but it does not test
this newer section-enabled bundle. Keep engineer review and security review separate.
