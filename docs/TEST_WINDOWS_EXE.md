# Download and run the Windows test EXE

**Portable Windows x64 diagnostic only — NOT for building design. No MSI installer.**

## Download

[Download the actual EXE + runtime ZIP](https://github.com/jesdswr-creator/struct-ai/actions/runs/45991582390/artifacts/15193683657)

- Artifact: `struct-ai-m0b-windows-x64-diagnostic` — **53,771,752 bytes**, about 54 MB.
- Available until **2026-12-04 11:35:32 UTC**, unless removed earlier.
- GitHub may ask you to sign in. If the direct link does not open, visit
  [the successful build](https://github.com/jesdswr-creator/struct-ai/actions/runs/45991582390),
  scroll to **Artifacts**, and select the artifact name above, **not** `m0b-windows-evidence`.
- This is the executable bundle, unlike the earlier `source` ZIP. The user explicitly
  authorised this public, seven-day diagnostic upload. Automatic push/PR binary uploads
  remain disabled; commercial redistribution/licensing review is not waived.

## Open the app

1. On Windows x64, right-click the downloaded ZIP and choose **Extract All** into a
   writable folder. Do not try to run the program from inside the ZIP preview.
2. Open the extracted folder and double-click **`struct_ai.exe`**. Explorer may hide
   the `.exe` extension and show it as `struct_ai`, type **Application**.
3. Keep **`_internal`** and the other extracted files beside the EXE. Copying only the
   EXE will break this onedir build. It includes its Python runtime; do not install
   Python merely to perform the intended no-Python acceptance test.
4. Click **Run diagnostic**. The synthetic benchmark should produce **five passing
   numerical checks**. Building design remains disabled deliberately.
5. Send a screenshot of the result, or the exact error/warning if it does not start.
   For an in-app error, use **Copy diagnostics**; logs are under
   `%APPDATA%\struct_ai\logs`.

The executable is **unsigned**. If SmartScreen or antivirus blocks it, preserve the exact
warning and verify the hash below. **Do not disable security protections.** A successful
CI run is not an antivirus clearance, code signature or Windows 11 acceptance result.

## Verify this specific download

ZIP SHA-256, reported by GitHub's artifact API:

```text
5d6d53092673d2e3a97cb509467e896f56efc137fb582a8075147b73f6d9e8ce
```

Extracted `struct_ai.exe` SHA-256, computed by the CI smoke runner:

```text
e124eb527fba8901d26265145ffc09d974d8f46ca414a2f10f9ef6eaee42a0e3
```

From PowerShell in the extracted folder:

```powershell
Get-FileHash .\struct_ai.exe -Algorithm SHA256
```

Stop and report any mismatch. These hashes identify this manual build, not earlier
CI builds, whose EXE timestamps/hashes may differ. The complete recorded metadata is in
[the handoff evidence](evidence/m0b/windows-test-download-2026-11-27.json). The archive was
not downloaded into the Linux sandbox; its archive digest comes from GitHub, while the
EXE and runtime-file hashes were computed during the real Windows build.

## Acceptance is still pending

This exact build uses source revision `a6c8d8c01a006c0b2540621fa8f5f977b466032f`. Its Windows
job passed **206 tests in 8.00 s**, Ruff/format, pip consistency, the real PyInstaller build,
source selftest, and both frozen selftests using Qt's native `windows` plugin. Source and
both frozen modes produced the same diagnostic result hash.

The CI host was Windows Server 2025 with development tools installed. The mandatory
**separate clean Windows 11 x64 / no installed Python, Qt, OpenSees or Ollama** run has not
yet been observed. Follow [the complete acceptance checklist](packaging-spike.md#clean-windows-acceptance--must-actually-be-performed)
and retain the actual selftest JSON reports, tester/OS identity, screenshots and hashes.
A screenshot alone does not complete that checklist. No M1 engineering functionality or
MSI/installer is included. This download is not a commercial release or licence grant.
