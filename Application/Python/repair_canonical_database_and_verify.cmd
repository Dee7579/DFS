@echo off
setlocal EnableExtensions
cd /d "%~dp0"

set "PYTHON_DIR=%~dp0"
for %%I in ("%~dp0..\..") do set "REPO_ROOT=%%~fI"
set "REPORT=%~dp0logs\canonical_database_repair_report.txt"

if not exist "%~dp0logs" mkdir "%~dp0logs"

echo ============================================================
echo DFS CANONICAL DATABASE REPAIR AND HARDENING
echo ============================================================
echo.
echo This will:
echo   1. Install a hard guard against composite data writing to dfs.db
echo   2. Restore Database\Data\dfs.db from the current Git commit
echo   3. Verify the certified source manifest
echo   4. Run the composite/runtime regression tests
echo   5. Run the full DFS test suite
echo   6. Verify the certified sources again after all tests
echo.
echo It does not commit or push anything.
echo.
pause

call :run_repair > "%REPORT%" 2>&1
set "RESULT=%ERRORLEVEL%"
type "%REPORT%"

if not "%RESULT%"=="0" goto :failed

echo.
echo ============================================================
echo CANONICAL DATABASE REPAIR VERIFIED
echo ============================================================
echo.
echo Report written to:
echo %REPORT%
echo.
pause
exit /b 0

:run_repair
echo Installing canonical database write guard...
python tools\apply_composite_database_guard.py
if errorlevel 1 exit /b 1

echo.
echo Restoring the canonical database from the current Git commit...
cd /d "%REPO_ROOT%"
git rev-parse --is-inside-work-tree
if errorlevel 1 exit /b 1

git status --short -- "Database/Data/dfs.db"
git restore --source=HEAD -- "Database/Data/dfs.db"
if errorlevel 1 exit /b 1

cd /d "%PYTHON_DIR%"

echo.
echo Verifying restored certified sources...
python verify_certified_sources.py
if errorlevel 1 exit /b 1

echo.
echo Running canonical/runtime database regression tests...
python -m pytest -q tests\fleet\test_composite_database_guard.py tests\test_runtime_database.py
if errorlevel 1 exit /b 1

echo.
echo Running full DFS automated test suite...
python -m pytest -q
if errorlevel 1 exit /b 1

echo.
echo Verifying certified sources after all tests...
python verify_certified_sources.py
if errorlevel 1 exit /b 1

echo.
echo Running final database validator...
python validate_database.py
if errorlevel 1 exit /b 1

exit /b 0

:failed
echo.
echo ============================================================
echo CANONICAL DATABASE REPAIR FAILED
echo ============================================================
echo.
echo No commit or push was performed.
echo Review or upload this report:
echo %REPORT%
echo.
pause
exit /b 1
