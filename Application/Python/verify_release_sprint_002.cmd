@echo off
setlocal EnableExtensions
cd /d "%~dp0"

set "REPORT=%~dp0logs\release_sprint_002_report.txt"
if not exist "%~dp0logs" mkdir "%~dp0logs"

call :run_checks > "%REPORT%" 2>&1
set "RESULT=%ERRORLEVEL%"
type "%REPORT%"

if not "%RESULT%"=="0" goto :failed

echo.
echo ============================================================
echo RELEASE SPRINT 002 VERIFIED
echo ============================================================
echo.
echo Report written to:
echo %REPORT%
echo.
pause
exit /b 0

:run_checks
echo Verifying certified sources before Release Sprint 002 tests...
python verify_certified_sources.py
if errorlevel 1 exit /b 1

echo.
echo Compiling Release Sprint 002 modules...
python -m compileall -q dfs
if errorlevel 1 exit /b 1

echo.
echo Running Release Sprint 002 focused tests...
set "QT_QPA_PLATFORM=offscreen"
python -m pytest -q tests\tactical\test_tactical_playtest_refinements_domain.py tests\tactical\test_tactical_playtest_refinements_ui.py tests\unit\test_collapsible_sidebar.py
if errorlevel 1 exit /b 1

echo.
echo Running Tactical Assistant regression tests...
python -m pytest -q tests\tactical
if errorlevel 1 exit /b 1

echo.
echo Running complete DFS test suite...
python -m pytest -q tests
if errorlevel 1 exit /b 1

echo.
echo Verifying certified sources after all tests...
python verify_certified_sources.py
if errorlevel 1 exit /b 1

echo.
echo Running final canonical database validator...
python validate_database.py
if errorlevel 1 exit /b 1

exit /b 0

:failed
echo.
echo ============================================================
echo RELEASE SPRINT 002 FAILED
echo ============================================================
echo.
echo Certified sources were not recertified or overwritten.
echo Review or upload:
echo %REPORT%
echo.
pause
exit /b 1
