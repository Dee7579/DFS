"""Build, verify, and archive the DFS Windows portable release."""

from __future__ import annotations

import hashlib
import re
import shutil
import subprocess
import sys
from pathlib import Path

from verify_portable_layout import validate_bundle


APP_ROOT = Path(__file__).resolve().parent.parent
REPOSITORY_ROOT = APP_ROOT.parents[1]
SPEC_PATH = APP_ROOT / "packaging" / "dfs_windows.spec"
SOURCE_DATABASE = REPOSITORY_ROOT / "Database" / "Data" / "dfs.db"
PYINSTALLER_OUTPUT = APP_ROOT / "dist" / "DeesFightingShips"
RELEASE_ROOT = APP_ROOT / "release"


def _application_version() -> str:
    source = (APP_ROOT / "dfs_desktop.py").read_text(encoding="utf-8")
    match = re.search(r'^APP_VERSION\s*=\s*"([^"]+)"', source, re.MULTILINE)
    if match is None:
        raise RuntimeError("Could not determine APP_VERSION from dfs_desktop.py.")
    return match.group(1)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    if sys.platform != "win32":
        raise SystemExit("The Windows portable release must be built on Windows.")

    subprocess.run(
        [
            sys.executable,
            "-m",
            "PyInstaller",
            "--noconfirm",
            "--clean",
            str(SPEC_PATH),
        ],
        cwd=APP_ROOT,
        check=True,
    )

    errors = validate_bundle(PYINSTALLER_OUTPUT, SOURCE_DATABASE)
    if errors:
        raise SystemExit("\n".join(errors))

    smoke_test = subprocess.run(
        [str(PYINSTALLER_OUTPUT / "DFS.exe"), "--release-smoke-test"],
        cwd=PYINSTALLER_OUTPUT,
        check=False,
        timeout=120,
    )
    if smoke_test.returncode != 0:
        raise SystemExit(
            f"Packaged DFS smoke test failed with exit code {smoke_test.returncode}."
        )

    version = _application_version()
    release_name = f"Dees-Fighting-Ships-{version}-Windows-x64"
    staged_release = RELEASE_ROOT / release_name
    archive_path = RELEASE_ROOT / f"{release_name}.zip"
    checksum_path = RELEASE_ROOT / f"{release_name}.sha256"

    if staged_release.exists():
        shutil.rmtree(staged_release)
    staged_release.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(PYINSTALLER_OUTPUT, staged_release)
    if archive_path.exists():
        archive_path.unlink()
    shutil.make_archive(str(archive_path.with_suffix("")), "zip", RELEASE_ROOT, release_name)
    checksum_path.write_text(
        f"{_sha256(archive_path)}  {archive_path.name}\n",
        encoding="ascii",
    )

    print(f"Created {archive_path}")
    print(f"Created {checksum_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
