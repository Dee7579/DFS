@echo off
setlocal EnableExtensions
cd /d "%~dp0"

set "REPORT=%~dp0logs\tactical_sprint_005d_report.txt"
if not exist "%~dp0logs" mkdir "%~dp0logs"

call :run_checks > "%REPORT%" 2>&1
set "RESULT=%ERRORLEVEL%"
type "%REPORT%"

if not "%RESULT%"=="0" goto :failed

echo.
echo ============================================================
echo TACTICAL ASSISTANT SPRINT 005D VERIFIED
echo ============================================================
echo.
echo Report written to:
echo %REPORT%
echo.
pause
exit /b 0

:run_checks
echo Verifying certified sources before Tactical Assistant map and stricken tests...
python verify_certified_sources.py
if errorlevel 1 exit /b 1

echo.
echo Compiling Tactical Assistant Sprint 005D modules...
python -m compileall -q dfs\domain\tactical dfs\infrastructure\tactical dfs\ui\tactical_assistant
if errorlevel 1 exit /b 1

echo.
echo Verifying scenario map assets...
python -c "from pathlib import Path; from dfs.domain.tactical import SCENARIO_MAP_FILES; root=Path('resources/scenario_maps'); missing=[k for k,v in SCENARIO_MAP_FILES.items() if not (root/v).is_file()]; assert not missing, 'Missing scenario maps: '+', '.join(missing); print(f'{len(SCENARIO_MAP_FILES)} scenario maps present')"
if errorlevel 1 exit /b 1

echo.
echo Running Tactical Assistant regression and Sprint 005D tests...
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
echo TACTICAL ASSISTANT SPRINT 005D FAILED
echo ============================================================
echo.
echo Certified sources were not recertified or overwritten.
echo Review or upload:
echo %REPORT%
echo.
pause
exit /b 1
