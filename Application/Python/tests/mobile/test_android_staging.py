from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import struct
import subprocess
import sys

from android.stage_android import (
    BUILD_ROOT,
    CANONICAL_DATABASE,
    _write_deploy_spec,
    stage_android,
    validate_stage,
)
from android.build_android import (
    ANDROID_ARCH,
    ANDROID_PAGE_SIZE,
    NON_ELF_NATIVE_PAYLOADS,
    P4A_BRANCH,
    P4A_COMMIT,
    PAGE_ALIGNMENT_COMPAT_LIBRARIES,
    QML_PLUGIN_PATHS,
    _elf_load_alignments,
    _patch_pyside_recipe,
    configure_buildozer,
)
from android.main import _write_startup_status
from android.verify_emulator_startup import _badging_identity


def _run_python(source: str, *, python_path: Path) -> subprocess.CompletedProcess[str]:
    environment = os.environ.copy()
    environment["PYTHONPATH"] = str(python_path)
    return subprocess.run(
        [sys.executable, "-c", source],
        check=True,
        capture_output=True,
        text=True,
        env=environment,
        cwd=python_path,
    )


def test_mobile_composition_does_not_import_desktop_or_pdf_modules() -> None:
    python_root = Path(__file__).resolve().parents[2]
    result = _run_python(
        """
import json
import sys
import dfs.mobile.application
blocked = [
    name for name in sys.modules
    if name == 'pypdf' or name.startswith('pypdf.')
    or name == 'reportlab' or name.startswith('reportlab.')
    or name.startswith('dfs.pdf') or name.startswith('dfs.ui')
]
print(json.dumps(sorted(blocked)))
""",
        python_path=python_root,
    )
    assert json.loads(result.stdout) == []


def test_android_stage_is_minimal_and_materializes_exact_database(tmp_path: Path) -> None:
    stage = stage_android(BUILD_ROOT / "pytest-stage")

    assert validate_stage(stage) == []
    assert not (stage / "dfs" / "pdf").exists()
    assert not (stage / "dfs" / "ui").exists()
    assert not (stage / "platform_data").exists()
    assert not list(stage.rglob("*.db"))

    destination = tmp_path / "materialized" / "dfs.db"
    result = _run_python(
        f"""
import hashlib
from pathlib import Path
from dfs.mobile.bundled_database import materialize_bundled_database
path = materialize_bundled_database(Path({str(destination)!r}))
print(hashlib.sha256(path.read_bytes()).hexdigest())
""",
        python_path=stage,
    )
    assert result.stdout.strip() == hashlib.sha256(CANONICAL_DATABASE.read_bytes()).hexdigest()
    assert destination.read_bytes() == CANONICAL_DATABASE.read_bytes()
    assert "arch = aarch64" in (stage / "pysidedeploy.spec").read_text(
        encoding="utf-8"
    )


def test_buildozer_configuration_is_landscape_and_pinned(tmp_path: Path) -> None:
    spec = tmp_path / "buildozer.spec"
    spec.write_text(
        """[app]
orientation = portrait
#android.api = 31
#android.minapi = 21
# android.accept_sdk_license = False
p4a.extra_args = --qt-libs=Core --load-local-libs=plugins_platforms_qtforandroid --init-classes=

[buildozer]
log_level = 2
""",
        encoding="utf-8",
    )

    configure_buildozer(spec)

    configured = spec.read_text(encoding="utf-8")
    assert "orientation = landscape" in configured
    assert "requirements = python3==3.11.15,hostpython3==3.11.15,shiboken6,PySide6" in configured
    assert "android.api = 34" in configured
    assert "android.minapi = 28" in configured
    assert "android.accept_sdk_license = True" in configured
    assert f"p4a.branch = {P4A_BRANCH}" in configured
    assert f"p4a.commit = {P4A_COMMIT}" in configured
    extra_args = next(
        line for line in configured.splitlines() if line.startswith("p4a.extra_args")
    )
    for plugin in QML_PLUGIN_PATHS:
        assert plugin not in extra_args


def test_buildozer_does_not_rely_on_unsupported_x86_add_libs(tmp_path: Path) -> None:
    spec = tmp_path / "buildozer.spec"
    spec.write_text(
        """[app]
p4a.extra_args = --qt-libs=Core --load-local-libs=plugins_platforms_qtforandroid --init-classes=

[buildozer]
""",
        encoding="utf-8",
    )

    configure_buildozer(spec)

    configured = spec.read_text(encoding="utf-8")
    assert "--load-local-libs=plugins_platforms_qtforandroid" in configured
    assert "android.add_libs_x86_64" not in configured


def test_android_deploy_spec_supports_x86_emulator(tmp_path: Path) -> None:
    _write_deploy_spec(tmp_path, "x86_64")

    assert "arch = x86_64" in (tmp_path / "pysidedeploy.spec").read_text(
        encoding="utf-8"
    )


def test_qml_plugins_are_added_to_cross_architecture_pyside_recipe(
    tmp_path: Path,
) -> None:
    recipe = tmp_path / "__init__.py"
    recipe.write_text(
        """from pathlib import Path
import shutil

class PySideRecipe:
    def build_arch(self, arch):
        pass


recipe = PySideRecipe()
""",
        encoding="utf-8",
    )

    _patch_pyside_recipe(recipe)

    patched = recipe.read_text(encoding="utf-8")
    compile(patched, str(recipe), "exec")
    assert "_dfs_build_arch_with_qml_plugins" in patched
    assert "arch.arch" in patched
    for plugin, qml_path in QML_PLUGIN_PATHS.items():
        assert repr(plugin) in patched
        assert repr(qml_path) in patched


def test_elf_alignment_reader_enforces_16_kb_load_segments() -> None:
    header = bytearray(128)
    header[:6] = b"\x7fELF\x02\x01"
    struct.pack_into("<Q", header, 32, 64)
    struct.pack_into("<H", header, 54, 56)
    struct.pack_into("<H", header, 56, 1)
    struct.pack_into("<I", header, 64, 1)
    struct.pack_into("<Q", header, 64 + 48, ANDROID_PAGE_SIZE)

    assert _elf_load_alignments(bytes(header)) == (ANDROID_PAGE_SIZE,)


def test_alignment_exceptions_are_narrow_and_explicit() -> None:
    assert PAGE_ALIGNMENT_COMPAT_LIBRARIES == {
        f"lib/{ANDROID_ARCH}/libshiboken6.abi3.so"
    }
    assert NON_ELF_NATIVE_PAYLOADS == {f"lib/{ANDROID_ARCH}/libpybundle.so"}


def test_emulator_badging_identity_parser() -> None:
    output = """package: name='org.example.dfscompanion' versionCode='1'
launchable-activity: name='org.kivy.android.PythonActivity' label='DFSCompanion'
"""

    assert _badging_identity(output) == (
        "org.example.dfscompanion",
        "org.kivy.android.PythonActivity",
    )


def test_android_startup_status_is_persisted(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("ANDROID_PRIVATE", str(tmp_path))

    _write_startup_status("error", "example traceback")

    assert (tmp_path / "dfs-startup-status.txt").read_text(encoding="utf-8") == (
        "error\nexample traceback"
    )
