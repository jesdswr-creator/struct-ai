@echo off
setlocal
cd /d "%~dp0"
echo struct_ai - EXPLICIT SAMPLE ONLY, NOT A PROJECT DESIGN
echo All code data is UNVERIFIED. This does not design or approve a building.
echo This runs one M1 flexure sample and one M2 torsion sample, with JSON and text reports.
echo No input, section dimensions or existing result files will be changed.
echo.
choice /c YN /n /m "Run these synthetic SAMPLE calculations? [Y/N] "
if errorlevel 2 exit /b 2
set "OUT=%TEMP%\struct_ai_SAMPLE_%RANDOM%_%RANDOM%"
if exist "%OUT%" goto failure
mkdir "%OUT%"
if errorlevel 1 goto failure
start "" /wait "%~dp0struct_ai.exe" --beam-flexure "%~dp0examples\SAMPLE_beam_rectangular.json" --output "%OUT%\flexure.json" --report "%OUT%\flexure.md" --error-output "%OUT%\flexure-error.json"
if errorlevel 1 goto failure
start "" /wait "%~dp0struct_ai.exe" --beam-checks "%~dp0examples\SAMPLE_beam_torsion.json" --output "%OUT%\torsion.json" --report "%OUT%\torsion.md" --error-output "%OUT%\torsion-error.json"
if errorlevel 1 goto failure
echo.
echo Requested SAMPLE checks passed, NOT code-compliance approval.
echo Reports and JSON are saved in: "%OUT%"
echo DRAFT: must be reviewed and sealed by a licensed structural engineer.
start "" notepad.exe "%OUT%\flexure.md"
start "" notepad.exe "%OUT%\torsion.md"
pause
exit /b 0
:failure
echo.
echo SAMPLE did not complete successfully. No successful design is claimed.
echo Inspect error JSON and any partial files in "%OUT%".
echo Application logs: %%APPDATA%%\struct_ai\logs
pause
exit /b 2
