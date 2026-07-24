@echo off
setlocal EnableExtensions
cd /d "%~dp0"

set "REPORT=%~dp0logs\tactical_sprint_005b_report.txt"
if not exist "%~dp0logs" mkdir "%~dp0logs"

call :run_checks > "%REPORT%" 2>&1
set "RESULT=%ERRORLEVEL%"
type "%REPORT%"

if not "%RESULT%"=="0" goto :failed

echo.
echo ============================================================
echo TACTICAL ASSISTANT SPRINT 005B VERIFIED
echo ============================================================
echo.
echo Report written to:
echo %REPORT%
echo.
pause
exit /b 0

:run_checks
echo Verifying certified sources before Tactical Assistant scenario-help tests...
python verify_certified_sources.py
if errorlevel 1 exit /b 1

echo.
echo Compiling Tactical Assistant Sprint 005B modules...
python -m compileall -q dfs\domain\tactical dfs\services\tactical dfs\infrastructure\tactical dfs\ui\tactical_assistant
if errorlevel 1 exit /b 1

echo.
echo Running Tactical Assistant regression and Sprint 005B tests...
set "QT_QPA_PLATFORM=offscreen"
python -m pytest -q tests\tactical
if errorlevel 1 exit /b 1

echo.
echo Running complete DFS test suite...
python -m pytest -q
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
echo TACTICAL ASSISTANT SPRINT 005B FAILED
echo ============================================================
echo.
echo Certified sources were not recertified or overwritten.
echo Review or upload:
echo %REPORT%
echo.
pause
exit /b 1
