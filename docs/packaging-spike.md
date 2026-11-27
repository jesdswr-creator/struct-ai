# M0b packaging spike — acceptance is pending

This is a **diagnostic-only** distribution, not a building-design application or a
commercial installer. Its real OpenSeesPy two-node elastic cantilever is independently
checked against PL³/(3EI), rotation and global equilibrium. No Indian Standard values
are used. No beam design, DOCX, DXF or schedules are claimed by this selftest.

## Target and pinned components

- Proposed primary target: Windows 11 x64, CPython **3.12.10** at build time.
- `openseespy==3.7.1.2`, `openseespywin==3.7.1.2`.
- PySide6 **Essentials** / Shiboken **6.8.3**; no QtWebEngine or PyQt.
- PyInstaller **6.14.2**, hooks **2025.5**, onedir, windowed, UPX disabled.
- Complete exact runtime/build/test dependency pins: `requirements.lock`.

The Windows wheel has a misleadingly broad `py3-none-any` filename. Its package metadata
requires Python `~=3.12.0`, and its loader explicitly refuses other Python minors and
32-bit systems. Inspection of the actual wheel's PE x86-64 `opensees.pyd` shows imports
from `python312.dll`, `KERNEL32.dll`, `imagehlp.dll` and `WSOCK32.dll`. This inspection is
NOT a substitute for running the built executable on Windows.

## Build on Windows

From a Windows checkout with CPython 3.12 x64 available to the `py` launcher:

```bat
packaging\build_windows.bat
```

The script validates the interpreter/venv, installs pinned dependencies, runs pytest
and ruff, builds `packaging/struct_ai.spec`, and uses `tools/smoke_frozen.py` to run both
real frozen selftests. Output: `dist\struct_ai\struct_ai.exe` **plus the entire onedir
folder**. Do not copy just the EXE. Do not run a Linux-built artifact on Windows.

The Windows workflow builds and tests automatically when it can be pushed. It always
uploads available test evidence, but the **binary upload is opt-in**: use Run workflow
with `publish_diagnostic_binary=true` only after reviewing distribution permissions.
An artifact named "diagnostic" or "internal-use" is not private by virtue of its name;
this repository is public. No binary is uploaded on ordinary pushes or pull requests.
This guard does not itself grant a commercial redistribution licence.

Manual equivalent after installation:

```bat
python tools\check.py
python -m PyInstaller --noconfirm --clean packaging\struct_ai.spec
python tools\smoke_frozen.py dist\struct_ai\struct_ai.exe --output .artifacts\windows-selftest
```

The spec explicitly collects OpenSees wrapper/native modules and binary files, versioned
Linux shared libraries where applicable, package metadata, every code JSON, fonts, SVG,
ICO and licences. Qt's official PyInstaller hooks collect the required native plugins.
A Windows runtime hook keeps DLL-directory handles alive. Multiprocessing freeze support
runs before argument parsing, including in windowed child processes. Resources resolve
under `sys._MEIPASS/struct_ai` when frozen and under the package in development.

`--selftest` loads/parses all catalogues, opens required resources, runs the real solver,
checks all five numerical checks and verifies exact repeated canonical payloads.
`--gui-selftest` shows the actual Qt window and runs its real spawned service worker.
Both write explicit JSON evidence and exit nonzero on failure. The frozen smoke runner
removes external Python/library/plugin path overrides, uses an unrelated working
directory, strips Python from Windows PATH and compares headless/GUI result hashes.
On Windows it clears the offscreen override to exercise the real Windows Qt platform
plugin; Linux smoke is explicitly offscreen. This is stronger than an import check,
but it is still not a Python-free-VM test.

## Clean Windows acceptance — must actually be performed

1. Prepare a fresh Windows 11 x64 VM with **no Python, Qt, OpenSees or Ollama installed**.
   Record OS build/architecture and VM image identity. Preserve a baseline snapshot.
2. Copy the entire built onedir folder, preferably into a path containing spaces.
3. Open PowerShell and run (use a writable evidence path):

   ```powershell
   $app = (Resolve-Path '.\struct_ai\struct_ai.exe').Path
   $evidence = Join-Path $env:TEMP 'struct_ai acceptance'
   New-Item -ItemType Directory -Force $evidence | Out-Null
   $report = Join-Path $evidence 'selftest.json'
   $p = Start-Process -FilePath $app -ArgumentList @('--selftest', '--output', "`"$report`"") -Wait -PassThru
   if ($p.ExitCode -ne 0) { throw "Frozen selftest failed: $($p.ExitCode)" }
   Get-Content $report
   $guiReport = Join-Path $evidence 'gui-selftest.json'
   $p = Start-Process -FilePath $app -ArgumentList @('--gui-selftest', '--output', "`"$guiReport`"") -Wait -PassThru
   if ($p.ExitCode -ne 0) { throw "Frozen GUI selftest failed: $($p.ExitCode)" }
   Get-Content $guiReport
   ```

4. Launch the app normally, click Run diagnostic, confirm five checks, then run/cancel,
   change theme, enter an invalid length and inspect/copy the error. Confirm initial
   result fields are empty and Building design is disabled.
5. Check at 100%, 125% and 150% Windows display scaling; record actual monitor pixels
   and effective logical workspace. Take native screenshots. Offscreen Linux screenshots
   are supplementary evidence, not these acceptance screenshots.
6. Repeat using the **CI-produced artifact**, not only a developer-local build.
7. Save both JSON files, native screenshots, exit codes, artifact SHA-256, OS identity,
   tester and date in the acceptance record below. Only then mark M0b accepted.

### Acceptance record (not filled with invented evidence)

| Item | Status / evidence |
|---|---|
| Windows local PyInstaller build | PENDING — no Windows execution in this sandbox |
| Windows CI artifact | BLOCKED — GitHub connection lacks workflow-write permission |
| Clean Windows with no Python: headless selftest | PENDING |
| Clean Windows with no Python: real window/worker | PENDING |
| CI artifact tested on clean Windows | PENDING |
| Native Windows DPI / AV / cold-start / idle-RAM measurements | PENDING |
| Commercial redistribution permission | REQUIRED before a commercial release |

## Supplementary Linux test environment

The sandbox runs Linux x86_64 / Python 3.11.2, supported by the pinned Linux wheel.
On a normal Debian/Ubuntu development host install `libgl1`, `libegl1`, `libxkbcommon0`,
`libdbus-1-3`, `libblas3` and `liblapack3`, then use the same Python lock file. CI defines
these prerequisites explicitly rather than skipping Qt/OpenSees tests.

This restricted sandbox could not fetch OS packages. For local offscreen validation it
used locally built libglvnd 1.7.0 and DBus 1.16.2, a native libxkbcommon from an OpenCV
wheel, and the OpenSees wheel's own BLAS library directory. It also lacked libpython,
so a shared runtime was built from the official CPython v3.11.2 source with the actual
Debian host's builtin-module set (including `_struct`) in `Modules/Setup.local`.
The final frozen smoke ran without those development-library path overrides. A normal
Linux build should install its matching Python development/shared-runtime package rather
than depend on this host-specific bootstrap.

These are scratch development prerequisites under ignored `.cache/`, **not Python
runtime dependencies or Windows redistribution payloads**. No OpenCV, Open3D or LLM
Python package is imported by the app. The spec explicitly collects the Linux graphics
libraries needed for its supplementary offscreen test because PyInstaller normally
excludes system graphics libraries. Optional XCB/GTK plugin dependencies still produce
warnings: a Linux graphical desktop distribution is not claimed. The complete source
and frozen smoke evidence remains explicitly labelled Linux. Native binaries, source
build trees and onedir build products are kept out of Git.

### Observed supplementary result (2026-11-27)

The final actual Linux onedir build and **both frozen selftests passed**, after the
QThread worker implementation was included. The smoke runner used an unrelated temporary
working directory, removed external Python/library/plugin paths and required the
`offscreen` Qt platform. Headless and GUI-worker result hashes were identical:

```text
33431478a4aa16c5d5c11c4fcbe09c69dfd57c00c00823b6bce440893fb9c1b0
```

The bundle occupies approximately 337 MiB on disk; this is not a memory-usage result.
The initial shared-Python build failed to include host builtins (first failing import:
`_struct`). Matching the host builtin set fixed that. The next actual GUI smoke found
`libGL.so.1` missing; explicit collection of GL/EGL/GLX/GLdispatch/xkbcommon/D-Bus fixed
that. These failures were repaired, not skipped. The recorded build log is from the
successful final build and still includes the unsupported XCB/GTK warnings described
above; it is not an archive of the earlier failures.

See [saved evidence and environment](evidence/m0b/environment.json) and
[the milestone report](../MILESTONE_REPORT.md). These results do **not** satisfy any
Windows or clean-OS acceptance item. The ignored `dist/` output is not a persistent
Windows deliverable or a committed release archive; retain a separately authorised
artifact when running the eventual Windows acceptance procedure.

## Distribution, antivirus and code signing

The actual OpenSeesPy licence notice says commercial redistribution requires a separate
licence. PySide6 is used under its LGPL alternative with replaceable dynamic libraries;
Inter is OFL. See bundled `NOTICES.md`. Obtain a full dependency/licensing review before
release; a passing selftest is not redistribution permission.

The spike is unsigned. Windows SmartScreen or antivirus may flag an unfamiliar executable.
Do not disable security protections; verify build provenance and hashes, and submit a
false-positive report to the vendor if appropriate. UPX is disabled and the build uses
onedir to avoid unnecessary self-extraction. At M14, sign the EXE and installer using a
trusted code-signing certificate and a timestamp service (preferably in an audited CI/HSM
process), then rerun artifact verification. Signing is not implemented here.

Logs: `%APPDATA%\struct_ai\logs`; Copy diagnostics reveals package versions and the log
folder, not environment secrets. Linux uses XDG state storage. No LLM weights are bundled.
No Inno Setup installer is supplied at M0b; that belongs to M14 after engineering and
clean-Windows acceptance gates are satisfied.
