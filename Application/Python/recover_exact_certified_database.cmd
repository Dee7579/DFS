@echo off
setlocal EnableExtensions
cd /d "%~dp0"

set "PYTHON_DIR=%~dp0"
set "REPORT=%~dp0logs\exact_certified_database_recovery_report.txt"

if not exist "%~dp0logs" mkdir "%~dp0logs"

echo ============================================================
echo DFS EXACT CERTIFIED DATABASE RECOVERY
echo ============================================================
echo.
echo IMPORTANT: Close DFS before continuing.
echo.
echo This recovery will:
echo   1. Read the exact database SHA-256 from the certification manifest
echo   2. Search Git history, reflogs, local clean clones, backups, and DFS.zip
echo   3. Restore only a byte-for-byte match to the certified database
echo   4. Preserve the contaminated database as an ignored backup
echo   5. Verify the certification, validator, guard tests, and full suite
echo.
echo It will never recertify a different database.
echo It does not commit or push anything.
echo.
pause

call :run_recovery > "%REPORT%" 2>&1
set "RESULT=%ERRORLEVEL%"
type "%REPORT%"

if not "%RESULT%"=="0" goto :failed

echo.
echo ============================================================
echo EXACT CERTIFIED DATABASE RECOVERY VERIFIED
echo ============================================================
echo.
echo Report written to:
echo %REPORT%
echo.
pause
exit /b 0

:run_recovery
python tools\restore_certified_database.py
if errorlevel 1 exit /b 1

echo.
echo Verifying certified source hashes...
python verify_certified_sources.py
if errorlevel 1 exit /b 1

echo.
echo Running canonical database validator...
python validate_database.py
if errorlevel 1 exit /b 1

echo.
echo Running canonical/runtime database guard tests...
python -m pytest -q tests\fleet\test_composite_database_guard.py tests\test_runtime_database.py
if errorlevel 1 exit /b 1

echo.
echo Running complete DFS test suite...
python -m pytest -q
if errorlevel 1 exit /b 1

echo.
echo Final certified-source verification...
python verify_certified_sources.py
if errorlevel 1 exit /b 1

exit /b 0

:failed
echo.
echo ============================================================
echo EXACT CERTIFIED DATABASE RECOVERY FAILED
echo ============================================================
echo.
echo No certification manifest was changed.
echo Review or upload:
echo %REPORT%
echo.
pause
exit /b 1
