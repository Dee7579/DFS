@echo off
setlocal EnableExtensions
cd /d "%~dp0"

set "REPORT=%~dp0logs\tactical_sprint_001_report.txt"
if not exist "%~dp0logs" mkdir "%~dp0logs"

echo ============================================================
echo DFS TACTICAL ASSISTANT SPRINT 001 VERIFICATION
echo ============================================================
echo.
echo This verifies the certified sources before and after the tests.
echo It does not modify platform_data or dfs.db.
echo.
pause

call :run_checks > "%REPORT%" 2>&1
set "RESULT=%ERRORLEVEL%"
type "%REPORT%"

if not "%RESULT%"=="0" goto :failed

echo.
echo ============================================================
echo TACTICAL ASSISTANT SPRINT 001 VERIFIED
echo ============================================================
echo.
echo Report written to:
echo %REPORT%
echo.
pause
exit /b 0

:run_checks
echo Verifying certified sources before Tactical Assistant tests...
python verify_certified_sources.py
if errorlevel 1 exit /b 1

echo.
echo Running Tactical Assistant Sprint 001 tests...
python -m pytest -q tests\tactical
if errorlevel 1 exit /b 1

echo.
echo Running full DFS automated test suite...
python -m pytest -q
if errorlevel 1 exit /b 1

echo.
echo Verifying certified sources after all tests...
python verify_certified_sources.py
if errorlevel 1 exit /b 1

exit /b 0

:failed
echo.
echo ============================================================
echo TACTICAL ASSISTANT SPRINT 001 VERIFICATION FAILED
echo ============================================================
echo.
echo Review or upload this report:
echo %REPORT%
echo.
pause
exit /b 1
