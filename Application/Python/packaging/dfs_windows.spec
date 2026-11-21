"""PyInstaller one-folder specification for the DFS Windows portable release."""

from pathlib import Path


APP_ROOT = Path(SPECPATH).resolve().parent
REPOSITORY_ROOT = APP_ROOT.parents[1]
DATABASE_PATH = REPOSITORY_ROOT / "Database" / "Data" / "dfs.db"

required_paths = (
    DATABASE_PATH,
    APP_ROOT / "resources",
    APP_ROOT / "output",
)
missing = [str(path) for path in required_paths if not path.exists()]
if missing:
    raise SystemExit("Missing required DFS release payloads:\n" + "\n".join(missing))

analysis = Analysis(
    [str(APP_ROOT / "dfs_desktop.py")],
    pathex=[str(APP_ROOT)],
    binaries=[],
    datas=[
        (str(DATABASE_PATH), "Database/Data"),
        (str(APP_ROOT / "resources"), "resources"),
        (str(APP_ROOT / "output"), "output"),
    ],
    hiddenimports=[
        "PySide6.QtPdf",
        "PySide6.QtPdfWidgets",
        "PySide6.QtSvg",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "platform_data",
        "pytest",
    ],
    noarchive=False,
)

python_archive = PYZ(analysis.pure)

executable = EXE(
    python_archive,
    analysis.scripts,
    [],
    exclude_binaries=True,
    name="DFS",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    contents_directory="_internal",
)

bundle = COLLECT(
    executable,
    analysis.binaries,
    analysis.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="DeesFightingShips",
)
