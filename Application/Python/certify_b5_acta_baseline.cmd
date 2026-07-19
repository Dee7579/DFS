@echo off
setlocal EnableExtensions
cd /d "%~dp0"

set "REPORT=%~dp0logs\certified_source_guard_report.txt"
set "MANIFEST=%~dp0data\certification\b5_acta_certified_sources.json"

if not exist "%~dp0logs" mkdir "%~dp0logs"

echo ============================================================
echo DFS B5 ACTA CERTIFIED-SOURCE GUARD
echo ============================================================
echo.
echo This will:
echo   1. Validate the canonical database
echo   2. Create the certification manifest only when it is absent
echo   3. Verify all certified source hashes
echo   4. Run the full automated test suite
echo.
echo Existing certification manifests are never overwritten.
echo It will not commit or push anything.
echo.
pause

call :run_checks > "%REPORT%" 2>&1
set "RESULT=%ERRORLEVEL%"
type "%REPORT%"

if not "%RESULT%"=="0" goto :failed

echo.
echo ============================================================
echo CERTIFIED-SOURCE GUARD VERIFIED
echo ============================================================
echo.
echo Report written to:
echo %REPORT%
echo.
pause
exit /b 0

:run_checks
if exist "%MANIFEST%" (
    echo Existing certification manifest found.
    echo Verifying the certified baseline without replacing it...
    echo.

    python validate_database.py
    if errorlevel 1 exit /b 1
) else (
    echo No certification manifest found.
    echo Creating the initial certified baseline...
    echo.

    python certify_sources.py
    if errorlevel 1 exit /b 1
)

echo.
python verify_certified_sources.py
if errorlevel 1 exit /b 1

echo.
echo Running full automated test suite...
python -m pytest -q
if errorlevel 1 exit /b 1

exit /b 0

:failed
echo.
echo ============================================================
echo CERTIFIED-SOURCE GUARD FAILED
echo ============================================================
echo.
echo No manifest was overwritten.
echo Review or upload this report:
echo %REPORT%
echo.
pause
exit /b 1
