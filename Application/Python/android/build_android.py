"""Build and checksum the DFS ARM64 tablet APK with Qt's official tool."""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
import re
import shutil
import subprocess
import sys
import zipfile

try:
    from .stage_android import BUILD_ROOT, PYTHON_ROOT, stage_android
except ImportError:  # Direct script execution from the android directory.
    from stage_android import BUILD_ROOT, PYTHON_ROOT, stage_android


PRODUCT_NAME = "Dees-Fighting-Ships-Android-Tablet-0.1.0-alpha1-arm64-v8a"
DELIVERY_ROOT = PYTHON_ROOT / "release" / "android"
ANDROID_API = "34"
ANDROID_MIN_API = "26"
ANDROID_PYTHON = "3.11.15"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _verify_apk(path: Path) -> None:
    if path.stat().st_size < 1_000_000:
        raise RuntimeError(f"Android package is unexpectedly small: {path}")
    with zipfile.ZipFile(path) as archive:
        names = set(archive.namelist())
    if "AndroidManifest.xml" not in names or "classes.dex" not in names:
        raise RuntimeError("Android package is missing its manifest or Java bytecode.")
    if not any(name.startswith("lib/arm64-v8a/") for name in names):
        raise RuntimeError("Android package does not contain an ARM64 native payload.")


def _set_buildozer_value(text: str, key: str, value: str) -> str:
    pattern = re.compile(
        rf"(?m)^(?P<indent>[ \t]*)#?[ \t]*{re.escape(key)}[ \t]*=.*$"
    )
    replacement = rf"\g<indent>{key} = {value}"
    updated, count = pattern.subn(replacement, text, count=1)
    if count:
        return updated
    marker = "[app]"
    if marker not in text:
        raise RuntimeError("Generated buildozer.spec has no [app] section.")
    return text.replace(marker, f"{marker}\n{key} = {value}", 1)


def configure_buildozer(path: Path) -> None:
    """Pin tablet orientation and API levels after Qt creates Buildozer's file."""

    text = path.read_text(encoding="utf-8")
    for key, value in (
        (
            "requirements",
            f"python3=={ANDROID_PYTHON},hostpython3=={ANDROID_PYTHON},shiboken6,PySide6",
        ),
        ("orientation", "landscape"),
        ("android.api", ANDROID_API),
        ("android.minapi", ANDROID_MIN_API),
        ("android.accept_sdk_license", "True"),
    ):
        text = _set_buildozer_value(text, key, value)
    path.write_text(text, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--wheel-pyside", type=Path, required=True)
    parser.add_argument("--wheel-shiboken", type=Path, required=True)
    parser.add_argument("--ndk-path", type=Path, required=True)
    parser.add_argument("--sdk-path", type=Path, required=True)
    args = parser.parse_args()

    stage = stage_android()
    deploy = shutil.which("pyside6-android-deploy")
    if not deploy:
        raise SystemExit("pyside6-android-deploy is not installed in this environment.")
    deploy_command = [
        deploy,
        "--config-file",
        str(stage / "pysidedeploy.spec"),
        "--wheel-pyside",
        str(args.wheel_pyside.resolve()),
        "--wheel-shiboken",
        str(args.wheel_shiboken.resolve()),
        "--ndk-path",
        str(args.ndk_path.resolve()),
        "--sdk-path",
        str(args.sdk_path.resolve()),
        "--init",
        "--keep-deployment-files",
        "--force",
        "--verbose",
    ]
    subprocess.run(
        deploy_command,
        cwd=stage,
        check=True,
    )
    buildozer_spec = stage / "buildozer.spec"
    if not buildozer_spec.is_file():
        raise RuntimeError("Qt Android deployment did not create buildozer.spec.")
    configure_buildozer(buildozer_spec)
    subprocess.run(
        [
            sys.executable,
            "-m",
            "buildozer",
            "android",
            "debug",
        ],
        cwd=stage,
        check=True,
    )

    generated_root = BUILD_ROOT / "release"
    candidates = sorted(generated_root.glob("*.apk"), key=lambda path: path.stat().st_mtime)
    if not candidates:
        candidates = sorted(stage.rglob("*.apk"), key=lambda path: path.stat().st_mtime)
    if not candidates:
        raise SystemExit("PySide6 Android deployment completed without producing an APK.")

    source = candidates[-1]
    DELIVERY_ROOT.mkdir(parents=True, exist_ok=True)
    destination = DELIVERY_ROOT / f"{PRODUCT_NAME}.apk"
    checksum = DELIVERY_ROOT / f"{PRODUCT_NAME}.sha256"
    shutil.copy2(source, destination)
    _verify_apk(destination)
    checksum.write_text(f"{_sha256(destination)}  {destination.name}\n", encoding="ascii")
    print(f"Created {destination}")
    print(f"Created {checksum}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
