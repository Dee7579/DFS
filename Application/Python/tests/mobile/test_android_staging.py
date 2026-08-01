from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

from android.stage_android import (
    BUILD_ROOT,
    CANONICAL_DATABASE,
    stage_android,
    validate_stage,
)
from android.build_android import configure_buildozer


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


def test_buildozer_configuration_is_landscape_and_pinned(tmp_path: Path) -> None:
    spec = tmp_path / "buildozer.spec"
    spec.write_text(
        """[app]
orientation = portrait
#android.api = 31
#android.minapi = 21
# android.accept_sdk_license = False

[buildozer]
log_level = 2
""",
        encoding="utf-8",
    )

    configure_buildozer(spec)

    configured = spec.read_text(encoding="utf-8")
    assert "orientation = landscape" in configured
    assert "android.api = 34" in configured
    assert "android.minapi = 26" in configured
    assert "android.accept_sdk_license = True" in configured
