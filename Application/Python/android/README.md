# DFS Android Tablet Companion

This directory contains the first touch-first Android feasibility build for Dee's
Fighting Ships. It is a separate presentation layer over the certified DFS
SQLite catalog, fleet rules, save formats, Tactical Assistant domain model, and
Codex.

## Alpha 2 scope

- Native searchable ship and fighter viewer (no PDF dependency)
- B5 ACTA fleet/list selection and Priority Level budget checks
- Add/remove roster entries and app-private fleet saves
- Start a tactical game from the active fleet
- Track damage, crew, shields, destroyed status, and turns
- Native weapon, trait, note, and Codex rule views
- Offline ARM64 tablet package
- Android 9+, including Android 16's 16 KB memory-page compatibility mode
- On-screen startup diagnostics if data or QML initialization fails

This feasibility alpha intentionally omits PDF viewing/printing, master-sheet
files, platform importing, certification tools, campaign management, and the
desktop widget tree. Advanced Fleet Builder editors (allied contingents,
fighter substitutions, missile choices, Huge Hangars, and vessel naming) and
the remaining Tactical Assistant controls are follow-up tablet work after the
vertical slice is proven on hardware.

## Local desktop smoke test

From `Application/Python` in a Python environment containing PySide6:

```bash
python -m pytest -q tests/mobile
QT_QPA_PLATFORM=offscreen QT_QUICK_BACKEND=software \
  python android/main.py --mobile-smoke-test
```

## Android build

The supported build is the `Android Tablet Feasibility` GitHub Actions workflow.
It uses Python 3.11, Qt for Python 6.10.3 ARM64 wheels, Android SDK platform 34,
build-tools 35.0.0, and NDK 28.2.13676358. The workflow:

1. Runs the focused mobile tests and QML smoke check.
2. Creates a minimal staging tree.
3. Converts the protected canonical database into a generated, checksummed
   Python payload.
4. Builds an ARM64 debug APK through `pyside6-android-deploy`.
5. Promotes the required Qt Quick QML plug-ins into Android's native library
   directory.
6. Verifies the APK structure and QML plug-ins, requires native 16 KB ELF
   alignment for the NDK-built payload, and records the one official Shiboken
   prebuilt that Android 16 runs in page-size compatibility mode.
7. Uploads the APK plus SHA-256 checksum.

The staging guard rejects raw databases, platform-data source files, desktop UI,
PDF code, ReportLab, pypdf, and Qt Print Support.

To invoke the build locally on Linux, first install the PySide Android deployment
requirements and Android SDK/NDK, then run:

```bash
python android/build_android.py \
  --wheel-pyside android/wheels/PySide6-6.10.3-6.10.3-cp311-cp311-android_aarch64.whl \
  --wheel-shiboken android/wheels/shiboken6-6.10.3-6.10.3-cp311-cp311-android_aarch64.whl \
  --sdk-path "$ANDROID_SDK_ROOT" \
  --ndk-path "$ANDROID_SDK_ROOT/ndk/28.2.13676358"
```
