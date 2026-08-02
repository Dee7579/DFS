# DFS Windows Release

This folder builds both unsigned Windows release formats for DFS:

- a portable one-folder ZIP; and
- a per-user installer with Start Menu and Desktop shortcuts plus an uninstaller.

Both formats use the same verified PyInstaller payload.

## Automated build

The `Windows Release Candidate` GitHub Actions workflow builds and uploads the
portable ZIP and installer, each with a SHA-256 checksum, whenever the draft
release pull request changes. The workflow also silently installs the installer,
validates its payload, runs the packaged smoke test, and uninstalls it.

## Local Windows build

Run `packaging\build_windows_portable.cmd` from Command Prompt to create only
the portable release.

Run `packaging\build_windows_installer.cmd` to create both formats. Inno Setup 6
must already be installed. The installer build:

1. creates an isolated `.venv-release` environment;
2. installs the pinned desktop and release dependencies;
3. builds the PyInstaller one-folder application;
4. verifies the database, scenario maps, and master reference sheets;
5. rejects development and certified platform-data source files;
6. launches the packaged executable in release smoke-test mode;
7. creates the portable ZIP and its SHA-256 checksum;
8. creates a per-user installer under `release\`;
9. silently installs and smoke-tests that installer; and
10. verifies its uninstaller before writing the installer checksum.

The release is intentionally unsigned during Sprint 001, so Windows may show a
SmartScreen warning on an unrecognized machine. Code signing remains a later
release step.
