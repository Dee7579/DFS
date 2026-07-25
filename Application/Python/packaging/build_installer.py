"""Build and verify the DFS per-user Windows installer."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from build_portable import (
    PYINSTALLER_OUTPUT,
    RELEASE_ROOT,
    SOURCE_DATABASE,
    _application_version,
    _sha256,
)
from verify_portable_layout import validate_bundle


APP_ROOT = Path(__file__).resolve().parent.parent
INSTALLER_SCRIPT = APP_ROOT / "packaging" / "dfs_installer.iss"


def _find_iscc() -> Path:
    for executable in ("ISCC.exe", "ISCC"):
        resolved = shutil.which(executable)
        if resolved:
            return Path(resolved)

    candidates = []
    for variable in ("ProgramFiles(x86)", "ProgramFiles"):
        base = os.environ.get(variable)
        if base:
            candidates.append(Path(base) / "Inno Setup 6" / "ISCC.exe")
    candidates.append(Path("C:/Program Files (x86)/Inno Setup 6/ISCC.exe"))

    for candidate in candidates:
        if candidate.is_file():
            return candidate

    raise RuntimeError(
        "Inno Setup 6 was not found. Install it, then rerun the installer build."
    )


def _installer_basename(version: str) -> str:
    return f"Dees-Fighting-Ships-{version}-Windows-x64-Setup"


def _verify_installed_payload(installer_path: Path) -> None:
    with tempfile.TemporaryDirectory(prefix="dfs-installer-smoke-") as temp:
        install_root = Path(temp) / "DeesFightingShips"
        install_log = Path(temp) / "install.log"
        uninstall_log = Path(temp) / "uninstall.log"

        subprocess.run(
            [
                str(installer_path),
                "/VERYSILENT",
                "/SUPPRESSMSGBOXES",
                "/NORESTART",
                "/SP-",
                f"/DIR={install_root}",
                f"/LOG={install_log}",
            ],
            check=True,
            timeout=300,
        )

        errors = validate_bundle(install_root, SOURCE_DATABASE)
        if errors:
            raise RuntimeError("\n".join(errors))

        smoke_test = subprocess.run(
            [str(install_root / "DFS.exe"), "--release-smoke-test"],
            cwd=install_root,
            check=False,
            timeout=120,
        )
        if smoke_test.returncode != 0:
            raise RuntimeError(
                "Installed DFS smoke test failed with exit code "
                f"{smoke_test.returncode}."
            )

        uninstaller = install_root / "unins000.exe"
        if not uninstaller.is_file():
            raise RuntimeError("The installer did not create an uninstaller.")
        subprocess.run(
            [
                str(uninstaller),
                "/VERYSILENT",
                "/SUPPRESSMSGBOXES",
                "/NORESTART",
                f"/LOG={uninstall_log}",
            ],
            check=True,
            timeout=300,
        )
        if (install_root / "DFS.exe").exists():
            raise RuntimeError("The DFS uninstaller did not remove the application.")


def main() -> int:
    if sys.platform != "win32":
        raise SystemExit("The DFS Windows installer must be built on Windows.")

    version = _application_version()
    staged_release = RELEASE_ROOT / f"Dees-Fighting-Ships-{version}-Windows-x64"
    if not staged_release.is_dir():
        raise SystemExit(
            "The verified portable release is missing. Run build_portable.py first."
        )

    errors = validate_bundle(staged_release, SOURCE_DATABASE)
    if errors:
        raise SystemExit("\n".join(errors))

    installer_basename = _installer_basename(version)
    installer_path = RELEASE_ROOT / f"{installer_basename}.exe"
    checksum_path = RELEASE_ROOT / f"{installer_basename}.sha256"
    for path in (installer_path, checksum_path):
        if path.exists():
            path.unlink()

    subprocess.run(
        [
            str(_find_iscc()),
            f"/DMyAppVersion={version}",
            f"/DMySourceDir={staged_release.resolve()}",
            f"/DMyOutputDir={RELEASE_ROOT.resolve()}",
            str(INSTALLER_SCRIPT),
        ],
        cwd=APP_ROOT,
        check=True,
        timeout=600,
    )
    if not installer_path.is_file():
        raise SystemExit(f"Inno Setup did not create {installer_path}.")

    _verify_installed_payload(installer_path)
    checksum_path.write_text(
        f"{_sha256(installer_path)}  {installer_path.name}\n",
        encoding="ascii",
    )

    print(f"Created and verified {installer_path}")
    print(f"Created {checksum_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
