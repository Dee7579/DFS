"""Build and checksum a DFS tablet APK with Qt's official Android tool."""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
import re
import shutil
import struct
import subprocess
import sys
import zipfile

try:
    from .stage_android import BUILD_ROOT, PYTHON_ROOT, stage_android
except ImportError:  # Direct script execution from the android directory.
    from stage_android import BUILD_ROOT, PYTHON_ROOT, stage_android


PRODUCT_VERSION = "0.1.0-alpha3"
DELIVERY_ROOT = PYTHON_ROOT / "release" / "android"
ANDROID_API = "34"
ANDROID_MIN_API = "28"
ANDROID_PYTHON = "3.11.15"
ANDROID_ARCH = "arm64-v8a"
ANDROID_PAGE_SIZE = 16 * 1024
P4A_BRANCH = "develop"
P4A_COMMIT = "0382d27de2f7315ed98e74884bafb30365decdee"
DEPLOY_ARCHES = {
    "arm64-v8a": "aarch64",
    "x86_64": "x86_64",
}

# Qt's official 6.10.3 Shiboken ARM64 wheel still ships this one prebuilt at
# 4 KB alignment. Android 16 detects it and enables its 16 KB compatibility
# mode. Everything compiled by DFS's NDK 28 lane must be natively 16 KB aligned.
PAGE_ALIGNMENT_COMPAT_LIBRARIES = {
    f"lib/{ANDROID_ARCH}/libshiboken6.abi3.so",
}

# python-for-android stores its compressed Python payload in a file named like
# a shared library so Android extracts it next to the real native libraries.
# It is a tar payload, not an ELF object, and must not be parsed as one.
NON_ELF_NATIVE_PAYLOADS = {
    f"lib/{ANDROID_ARCH}/libpybundle.so",
}

# pyside6-android-deploy 6.10 copies Qt module libraries into the APK, but its
# generated recipe does not promote QML plug-ins out of the extracted Python
# bundle. Promote the plug-ins into Android's native library directory, while
# leaving their initialization to QML instead of forcing Java to load every
# plug-in before Python starts.
QML_PLUGIN_PATHS = {
    "qml_QtQml_qmlplugin": "QtQml",
    "qml_QtQml_Models_modelsplugin": "QtQml/Models",
    "qml_QtQml_WorkerScript_workerscriptplugin": "QtQml/WorkerScript",
    "qml_QtQuick_qtquick2plugin": "QtQuick",
    "qml_QtQuick_Window_quickwindowplugin": "QtQuick/Window",
    "qml_QtQuick_Layouts_qquicklayoutsplugin": "QtQuick/Layouts",
    "qml_QtQuick_Templates_qtquicktemplates2plugin": "QtQuick/Templates",
    "qml_QtQuick_Controls_qtquickcontrols2plugin": "QtQuick/Controls",
    "qml_QtQuick_Controls_impl_qtquickcontrols2implplugin": "QtQuick/Controls/impl",
    "qml_QtQuick_Controls_Basic_qtquickcontrols2basicstyleplugin": (
        "QtQuick/Controls/Basic"
    ),
    "qml_QtQuick_Controls_Basic_impl_qtquickcontrols2basicstyleimplplugin": (
        "QtQuick/Controls/Basic/impl"
    ),
}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _elf_load_alignments(header: bytes) -> tuple[int, ...]:
    """Return PT_LOAD alignment values from a little-endian ELF header."""

    if len(header) < 64 or header[:4] != b"\x7fELF":
        raise ValueError("Native library has no valid ELF header.")
    elf_class = header[4]
    byte_order = header[5]
    if byte_order != 1:
        raise ValueError("Only little-endian Android ELF libraries are supported.")
    if elf_class == 2:  # ELF64
        program_offset = struct.unpack_from("<Q", header, 32)[0]
        entry_size = struct.unpack_from("<H", header, 54)[0]
        entry_count = struct.unpack_from("<H", header, 56)[0]
        alignment_offset = 48
        alignment_format = "<Q"
    elif elf_class == 1:  # ELF32
        program_offset = struct.unpack_from("<I", header, 28)[0]
        entry_size = struct.unpack_from("<H", header, 42)[0]
        entry_count = struct.unpack_from("<H", header, 44)[0]
        alignment_offset = 28
        alignment_format = "<I"
    else:
        raise ValueError(f"Unsupported ELF class: {elf_class}")

    required = program_offset + (entry_size * entry_count)
    if required > len(header):
        raise ValueError("ELF program headers are truncated.")
    alignments: list[int] = []
    for index in range(entry_count):
        entry = program_offset + (index * entry_size)
        segment_type = struct.unpack_from("<I", header, entry)[0]
        if segment_type == 1:  # PT_LOAD
            alignments.append(
                struct.unpack_from(alignment_format, header, entry + alignment_offset)[0]
            )
    if not alignments:
        raise ValueError("Native library contains no PT_LOAD segments.")
    return tuple(alignments)


def _verify_apk(path: Path, *, arch: str = ANDROID_ARCH) -> None:
    if path.stat().st_size < 1_000_000:
        raise RuntimeError(f"Android package is unexpectedly small: {path}")
    with zipfile.ZipFile(path) as archive:
        names = set(archive.namelist())
        if "AndroidManifest.xml" not in names or "classes.dex" not in names:
            raise RuntimeError("Android package is missing its manifest or Java bytecode.")
        native_prefix = f"lib/{arch}/"
        native_libraries = sorted(
            name
            for name in names
            if name.startswith(native_prefix) and name.endswith(".so")
        )
        if not native_libraries:
            raise RuntimeError(
                f"Android package does not contain a {arch} native payload."
            )

        missing_qml = [
            f"{native_prefix}lib{plugin}_{arch}.so"
            for plugin in QML_PLUGIN_PATHS
            if f"{native_prefix}lib{plugin}_{arch}.so" not in names
        ]
        if missing_qml:
            raise RuntimeError(
                "Android package is missing required QML plug-ins: "
                + ", ".join(missing_qml)
            )

        if arch != ANDROID_ARCH:
            return

        alignment_errors: list[str] = []
        compatibility_libraries: list[str] = []
        for name in native_libraries:
            if name in NON_ELF_NATIVE_PAYLOADS:
                continue
            with archive.open(name) as source:
                header = source.read(64 * 1024)
            try:
                alignments = _elf_load_alignments(header)
            except ValueError as exc:
                alignment_errors.append(f"{name}: {exc}")
                continue
            if any(alignment < ANDROID_PAGE_SIZE for alignment in alignments):
                if name in PAGE_ALIGNMENT_COMPAT_LIBRARIES:
                    compatibility_libraries.append(name)
                    continue
                values = ", ".join(f"0x{alignment:x}" for alignment in alignments)
                alignment_errors.append(f"{name}: PT_LOAD alignments {values}")
        if alignment_errors:
            raise RuntimeError(
                "Android package contains native libraries that are not 16 KB page aligned:\n"
                + "\n".join(alignment_errors)
            )
        if compatibility_libraries:
            print(
                "Android 16 page-size compatibility mode is required by: "
                + ", ".join(compatibility_libraries)
            )


def _patch_pyside_recipe(path: Path) -> None:
    """Copy the required QML plug-ins through PySide's cross-architecture recipe."""

    text = path.read_text(encoding="utf-8")
    sentinel = "_dfs_build_arch_with_qml_plugins"
    if sentinel in text:
        return
    marker = re.search(
        r"(?m)^[ \t]*recipe[ \t]*=[ \t]*PySideRecipe\(\)[ \t]*$",
        text,
    )
    if marker is None:
        raise RuntimeError(f"Generated PySide Android recipe has changed: {path}")
    plugin_entries = "\n".join(
        f"        ({plugin!r}, {qml_path!r}),"
        for plugin, qml_path in QML_PLUGIN_PATHS.items()
    )
    extension = f'''\n\n_dfs_original_build_arch = PySideRecipe.build_arch


def {sentinel}(self, arch):
    _dfs_original_build_arch(self, arch)
    qml_root = (
        Path(self.ctx.get_python_install_dir(arch.arch)) / "PySide6" / "Qt" / "qml"
    )
    native_root = Path(self.ctx.get_libs_dir(arch.arch))
    qml_plugins = (
{plugin_entries}
    )
    for plugin_name, qml_path in qml_plugins:
        filename = f"lib{{plugin_name}}_{{arch.arch}}.so"
        source = qml_root / qml_path / filename
        if not source.is_file():
            raise FileNotFoundError(f"Required DFS QML plug-in is missing: {{source}}")
        shutil.copyfile(source, native_root / filename)


PySideRecipe.build_arch = {sentinel}
'''
    patched = text[: marker.start()] + extension + "\n\n" + text[marker.start() :]
    path.write_text(patched, encoding="utf-8")


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
        ("p4a.branch", P4A_BRANCH),
        ("p4a.commit", P4A_COMMIT),
    ):
        text = _set_buildozer_value(text, key, value)
    path.write_text(text, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--wheel-pyside", type=Path, required=True)
    parser.add_argument("--wheel-shiboken", type=Path, required=True)
    parser.add_argument("--ndk-path", type=Path, required=True)
    parser.add_argument("--sdk-path", type=Path, required=True)
    parser.add_argument(
        "--arch",
        choices=tuple(DEPLOY_ARCHES),
        default=ANDROID_ARCH,
    )
    args = parser.parse_args()

    stage = stage_android(deploy_arch=DEPLOY_ARCHES[args.arch])
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
    _patch_pyside_recipe(
        stage / "deployment" / "recipes" / "PySide6" / "__init__.py"
    )
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
    product_name = f"Dees-Fighting-Ships-Android-Tablet-{PRODUCT_VERSION}-{args.arch}"
    destination = DELIVERY_ROOT / f"{product_name}.apk"
    checksum = DELIVERY_ROOT / f"{product_name}.sha256"
    shutil.copy2(source, destination)
    _verify_apk(destination, arch=args.arch)
    checksum.write_text(f"{_sha256(destination)}  {destination.name}\n", encoding="ascii")
    print(f"Created {destination}")
    print(f"Created {checksum}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
