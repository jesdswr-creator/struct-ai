@echo off
setlocal EnableExtensions
pushd "%~dp0.."
set "PYTHONUTF8=1"
set "QT_QPA_PLATFORM=offscreen"
set "PYTEST_QT_API=pyside6"

echo struct_ai M0b diagnostic ONLY. Not building design. No installer is produced.
py -3.12 -c "import sys,struct; assert sys.version_info[:2]==(3,12) and struct.calcsize('P')==8, 'CPython 3.12 x64 required'"
if errorlevel 1 goto fail
if not exist .venv\Scripts\python.exe (
  py -3.12 -m venv .venv
  if errorlevel 1 goto fail
)
.venv\Scripts\python.exe -c "import sys,struct; assert sys.version_info[:2]==(3,12) and struct.calcsize('P')==8, 'Existing venv is not CPython 3.12 x64; create a new supported environment'"
if errorlevel 1 goto fail
.venv\Scripts\python.exe -m pip install -r requirements.lock
if errorlevel 1 goto fail
.venv\Scripts\python.exe -m pip install --no-deps --no-build-isolation -e .
if errorlevel 1 goto fail
.venv\Scripts\python.exe -m pip check
if errorlevel 1 goto fail
.venv\Scripts\python.exe tools\check.py
if errorlevel 1 goto fail
.venv\Scripts\python.exe -m struct_ai --selftest --output .artifacts\source-selftest.json
if errorlevel 1 goto fail
.venv\Scripts\python.exe -m PyInstaller --noconfirm --clean packaging\struct_ai.spec
if errorlevel 1 goto fail
.venv\Scripts\python.exe tools\smoke_frozen.py dist\struct_ai\struct_ai.exe --output .artifacts\windows-selftest --source-report .artifacts\source-selftest.json
if errorlevel 1 goto fail

echo Build and local frozen smoke tests passed. Clean Windows VM acceptance is still required.
echo Do not commercially redistribute without resolving the OpenSeesPy licence.
popd
exit /b 0
:fail
echo FAILED. No packaging acceptance claim is made.
popd
exit /b 1
