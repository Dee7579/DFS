@echo off
setlocal EnableExtensions EnableDelayedExpansion
cd /d "%~dp0"

echo ============================================================
echo DFS FULL PLATFORM REIMPORT
echo ============================================================
echo.
echo Close the DFS application before continuing.
echo This script will:
echo   1. Back up the current database
echo   2. Preserve the current output folder
echo   3. Reimport every platform_data module
echo   4. Regenerate all PDFs
echo   5. Run the database validator
echo   6. Count the generated PDFs
echo.
pause

if not exist "add_ship.py" (
    echo ERROR: add_ship.py was not found.
    echo Put this file in DFS\Application\Python and run it there.
    goto :failed
)

if not exist "platform_data" (
    echo ERROR: platform_data folder was not found.
    goto :failed
)

if not exist "..\..\Database\Data\dfs.db" (
    echo ERROR: Database not found at ..\..\Database\Data\dfs.db
    goto :failed
)

python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python was not found on PATH.
    goto :failed
)

for /f %%I in ('python -c "import datetime; print(datetime.datetime.now().strftime('%%Y%%m%%d_%%H%%M%%S'))"') do set "STAMP=%%I"

echo.
echo Backing up database...
copy /Y "..\..\Database\Data\dfs.db" "..\..\Database\Data\dfs_before_reimport_!STAMP!.db" >nul
if errorlevel 1 (
    echo ERROR: Database backup failed.
    goto :failed
)
echo Database backup created:
echo ..\..\Database\Data\dfs_before_reimport_!STAMP!.db

if exist "output" (
    echo.
    echo Preserving current output folder...
    move "output" "output_before_reimport_!STAMP!" >nul
    if errorlevel 1 (
        echo ERROR: Could not preserve the current output folder.
        goto :failed
    )
    echo Previous PDFs moved to:
    echo output_before_reimport_!STAMP!
)

mkdir "output" >nul 2>&1

echo.
echo Reimporting all platform modules...
set /a COUNT=0

for %%F in ("platform_data\*.py") do (
    set "STEM=%%~nF"
    if /I not "!STEM!"=="__init__" (
        set /a COUNT+=1
        echo [!COUNT!] Importing !STEM!...
        python "add_ship.py" "!STEM!"
        if errorlevel 1 (
            echo.
            echo ERROR: Import failed for %%~nxF
            goto :failed
        )
    )
)

echo.
echo Imported !COUNT! platform modules successfully.

echo.
echo Regenerating all PDFs...
python "generate_all.py"
if errorlevel 1 (
    echo ERROR: PDF generation failed.
    goto :failed
)

echo.
echo Running database validator...
python "validate_database.py"
set "VALIDATOR_EXIT=!errorlevel!"

for /f %%I in ('python -c "from pathlib import Path; print(sum(1 for _ in Path('output').rglob('*.pdf')))"') do set "PDFCOUNT=%%I"

echo.
echo ============================================================
echo REIMPORT COMPLETE
echo ============================================================
echo Platform modules imported: !COUNT!
echo Generated PDF count:       !PDFCOUNT!
echo Validator exit code:       !VALIDATOR_EXIT!
echo.

if "!PDFCOUNT!"=="304" (
    echo PDF inventory target reached: 304
) else (
    echo WARNING: Expected 304 PDFs, but found !PDFCOUNT!.
)

if not "!VALIDATOR_EXIT!"=="0" (
    echo NOTE: The validator reported one or more findings.
    echo Save or photograph the final validator results for review.
)

echo.
pause
exit /b 0

:failed
echo.
echo Reimport stopped before completion.
echo The timestamped database backup was preserved if it had already been created.
echo.
pause
exit /b 1
