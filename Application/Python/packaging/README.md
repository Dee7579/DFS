# DFS Windows Portable Release

This folder builds the unsigned, one-folder Windows release candidate for DFS.

## Automated build

The `Windows Portable Release Candidate` GitHub Actions workflow builds and
uploads a ZIP plus its SHA-256 checksum whenever the release branch changes.
It can also be started manually from the Actions tab.

## Local Windows build

Run `packaging\build_windows_portable.cmd` from Command Prompt. The script:

1. creates an isolated `.venv-release` environment;
2. installs the pinned desktop and release dependencies;
3. builds the PyInstaller one-folder application;
4. verifies the database, scenario maps, and master reference sheets;
5. rejects development and certified platform-data source files;
6. launches the packaged executable in release smoke-test mode; and
7. creates the portable ZIP and SHA-256 checksum under `release\`.

The release is intentionally unsigned during Sprint 001, so Windows may show a
SmartScreen warning on an unrecognized machine. Code signing belongs to the
later installer/release-signing phase.
