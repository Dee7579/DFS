@echo off
setlocal
cd /d "%~dp0.."

where py >nul 2>nul
if %errorlevel% equ 0 (
    set "DFS_PYTHON=py -3"
) else (
    set "DFS_PYTHON=python"
)

if not exist ".venv-release\Scripts\python.exe" (
    %DFS_PYTHON% -m venv .venv-release
    if errorlevel 1 goto :failed
)

call ".venv-release\Scripts\activate.bat"
if errorlevel 1 goto :failed

python -m pip install --upgrade pip
if errorlevel 1 goto :failed

python -m pip install -r requirements-release.txt
if errorlevel 1 goto :failed

python packaging\build_portable.py
if errorlevel 1 goto :failed

echo.
echo DFS Windows portable release created under:
echo %CD%\release
exit /b 0

:failed
echo.
echo DFS Windows portable build failed.
exit /b 1
