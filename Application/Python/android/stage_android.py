"""Create the minimal, verified source tree consumed by Android deployment."""

from __future__ import annotations

import ast
import base64
import hashlib
import json
from pathlib import Path
import shutil
import textwrap
import zlib


PYTHON_ROOT = Path(__file__).resolve().parent.parent
REPOSITORY_ROOT = PYTHON_ROOT.parents[1]
ANDROID_ROOT = PYTHON_ROOT / "android"
SOURCE_DFS = PYTHON_ROOT / "dfs"
CANONICAL_DATABASE = REPOSITORY_ROOT / "Database" / "Data" / "dfs.db"
BUILD_ROOT = PYTHON_ROOT / "build" / "android"
STAGE_ROOT = BUILD_ROOT / "staging"

ROOT_FILES = ("__init__.py", "app_paths.py", "runtime_database.py")
PACKAGE_DIRS = ("codex", "domain", "mobile", "repositories", "rules")
INFRASTRUCTURE_DIRS = ("fleet", "sqlite", "tactical")
SERVICE_FILES = (
    "__init__.py",
    "codex_service.py",
    "platform_catalog_service.py",
    "platform_detail_service.py",
)
SERVICE_DIRS = ("fleet", "tactical")
DESKTOP_FLEET_FILES = {
    "print_composer.py",
    "print_planner.py",
    "roster_generator.py",
    "sheet_generator.py",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _copy_tree(source: Path, destination: Path) -> None:
    shutil.copytree(
        source,
        destination,
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "*.pyo"),
    )


def _stage_python_sources(stage: Path) -> None:
    target = stage / "dfs"
    target.mkdir(parents=True)
    for name in ROOT_FILES:
        shutil.copy2(SOURCE_DFS / name, target / name)
    for name in PACKAGE_DIRS:
        _copy_tree(SOURCE_DFS / name, target / name)

    infrastructure = target / "infrastructure"
    infrastructure.mkdir()
    shutil.copy2(SOURCE_DFS / "infrastructure" / "__init__.py", infrastructure / "__init__.py")
    for name in INFRASTRUCTURE_DIRS:
        _copy_tree(SOURCE_DFS / "infrastructure" / name, infrastructure / name)

    services = target / "services"
    services.mkdir()
    for name in SERVICE_FILES:
        shutil.copy2(SOURCE_DFS / "services" / name, services / name)
    for name in SERVICE_DIRS:
        _copy_tree(SOURCE_DFS / "services" / name, services / name)
    for name in DESKTOP_FLEET_FILES:
        candidate = services / "fleet" / name
        if candidate.exists():
            candidate.unlink()


def _write_database_payload(stage: Path) -> None:
    payload = CANONICAL_DATABASE.read_bytes()
    encoded = base64.b85encode(zlib.compress(payload, level=9)).decode("ascii")
    chunks = textwrap.wrap(encoded, width=100)
    module = stage / "dfs" / "mobile" / "_bundled_database_payload.py"
    lines = [
        '"""Generated from the protected canonical DFS database; do not edit."""',
        "",
        f'DATABASE_SHA256 = "{hashlib.sha256(payload).hexdigest()}"',
        "DATABASE_B85 = (",
        *(f'    "{chunk}"' for chunk in chunks),
        ")",
        "",
    ]
    module.write_text("\n".join(lines), encoding="ascii")


def _write_project_file(stage: Path) -> None:
    files = sorted(
        path.relative_to(stage).as_posix()
        for path in stage.rglob("*")
        if path.is_file() and path.suffix.casefold() in {".py", ".qml"}
    )
    (stage / "DFSAndroid.pyproject").write_text(
        json.dumps({"files": files}, indent=2) + "\n",
        encoding="utf-8",
    )


def _write_deploy_spec(stage: Path, deploy_arch: str) -> None:
    (stage / "pysidedeploy.spec").write_text(
        f"""[app]
title = DFSCompanion
project_dir = .
input_file = main.py
exec_directory = ../release
project_file = DFSAndroid.pyproject
icon =

[python]
python_path =
packages =
android_packages = buildozer==1.5.0,cython==0.29.33

[qt]
qml_files = qml/Main.qml
excluded_qml_plugins =
modules = Core,Gui,Network,Qml,QmlModels,OpenGL,Quick,QuickControls2,QuickLayouts,QuickTemplates2
plugins =

[android]
wheel_pyside =
wheel_shiboken =
plugins =

[nuitka]
macos.permissions =
mode = onefile
extra_args =

[buildozer]
mode = debug
recipe_dir =
jars_dir =
ndk_path =
sdk_path =
local_libs =
arch = {deploy_arch}
""",
        encoding="utf-8",
    )


def validate_stage(stage: Path = STAGE_ROOT) -> list[str]:
    errors: list[str] = []
    required = (
        stage / "main.py",
        stage / "qml" / "Main.qml",
        stage / "dfs" / "mobile" / "_bundled_database_payload.py",
        stage / "DFSAndroid.pyproject",
        stage / "pysidedeploy.spec",
    )
    for path in required:
        if not path.is_file():
            errors.append(f"Missing Android staging file: {path}")

    forbidden_roots = (
        stage / "dfs" / "pdf",
        stage / "dfs" / "ui",
        stage / "dfs" / "presentation",
        stage / "platform_data",
    )
    for path in forbidden_roots:
        if path.exists():
            errors.append(f"Desktop/source-only path leaked into Android stage: {path}")
    if any(stage.rglob("*.db")):
        errors.append("Raw SQLite databases must be carried only as verified generated payloads.")

    forbidden_imports = ("PySide6.QtPrintSupport", "reportlab", "pypdf", "dfs.pdf", "dfs.ui")
    for path in stage.rglob("*.py"):
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except SyntaxError as exc:
            errors.append(f"Invalid staged Python source {path}: {exc}")
            continue
        imported_modules: list[str] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported_modules.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported_modules.append(node.module)
        for imported in imported_modules:
            for forbidden in forbidden_imports:
                if imported == forbidden or imported.startswith(f"{forbidden}."):
                    errors.append(
                        f"Desktop/PDF dependency {forbidden!r} imported by {path}"
                    )
    return errors


def stage_android(stage: Path = STAGE_ROOT, *, deploy_arch: str = "aarch64") -> Path:
    resolved_stage = stage.resolve()
    expected_parent = BUILD_ROOT.resolve()
    if expected_parent not in resolved_stage.parents:
        raise ValueError(f"Android stage must remain under {expected_parent}")
    if resolved_stage.exists():
        shutil.rmtree(resolved_stage)
    resolved_stage.mkdir(parents=True)

    shutil.copy2(ANDROID_ROOT / "main.py", resolved_stage / "main.py")
    _copy_tree(ANDROID_ROOT / "qml", resolved_stage / "qml")
    _stage_python_sources(resolved_stage)
    _write_database_payload(resolved_stage)
    _write_project_file(resolved_stage)
    _write_deploy_spec(resolved_stage, deploy_arch)

    errors = validate_stage(resolved_stage)
    if errors:
        raise RuntimeError("\n".join(errors))
    return resolved_stage


def main() -> int:
    stage = stage_android()
    print(f"Android stage created: {stage}")
    print(f"Certified database SHA-256: {sha256(CANONICAL_DATABASE)}")
    print(f"Staged files: {sum(1 for path in stage.rglob('*') if path.is_file())}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
