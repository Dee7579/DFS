from pathlib import Path
import re
import sys


APP_ROOT = Path(__file__).resolve().parents[2]
PACKAGING_ROOT = APP_ROOT / "packaging"
sys.path.insert(0, str(PACKAGING_ROOT))

from verify_portable_layout import validate_bundle  # noqa: E402


def test_release_version_is_consistent_across_desktop_surfaces():
    expected = "2.4.0-alpha27"
    sources = (
        APP_ROOT / "dfs_desktop.py",
        APP_ROOT / "dfs" / "__init__.py",
        APP_ROOT / "dfs" / "ui" / "about_dialog.py",
    )

    for source in sources:
        match = re.search(
            r'(?:APP_VERSION|__version__)\s*=\s*"([^"]+)"',
            source.read_text(encoding="utf-8"),
        )
        assert match is not None, source
        assert match.group(1) == expected, source


def test_release_dependencies_are_declared():
    desktop = (APP_ROOT / "requirements-desktop.txt").read_text(encoding="utf-8")
    release = (APP_ROOT / "requirements-release.txt").read_text(encoding="utf-8")

    assert "reportlab" in desktop.casefold()
    assert "pyinstaller" in release.casefold()
    assert "-r requirements-desktop.txt" in release


def test_spec_bundles_only_approved_runtime_payload_roots():
    spec = (PACKAGING_ROOT / "dfs_windows.spec").read_text(encoding="utf-8")

    assert '"Database/Data"' in spec
    assert '"resources"' in spec
    assert '"output"' in spec
    assert '"platform_data"' in spec
    assert "excludes=" in spec
    assert "tests" not in spec
    assert "project_sources" not in spec


def test_windows_workflow_builds_both_release_formats_for_pull_request():
    workflow = (
        APP_ROOT.parents[1] / ".github" / "workflows" / "windows-portable.yml"
    ).read_text(encoding="utf-8")

    assert "windows-latest" in workflow
    assert "pull_request:" in workflow
    assert "- main" in workflow
    assert "packaging/build_portable.py" in workflow
    assert "choco install innosetup" in workflow
    assert "packaging/build_installer.py" in workflow
    assert "dfs-windows-installer-" in workflow
    assert "actions/upload-artifact@" in workflow


def test_installer_is_per_user_and_creates_requested_shortcuts():
    installer = (PACKAGING_ROOT / "dfs_installer.iss").read_text(encoding="utf-8")

    assert "PrivilegesRequired=lowest" in installer
    assert r"DefaultDirName={localappdata}\Programs" in installer
    assert r'Name: "{autoprograms}\{#MyAppName}"' in installer
    assert r'Name: "{autodesktop}\{#MyAppName}"' in installer
    assert "UninstallDisplayIcon=" in installer
    assert "postinstall skipifsilent" in installer


def test_installer_builder_verifies_installed_payload_and_uninstaller():
    builder = (PACKAGING_ROOT / "build_installer.py").read_text(encoding="utf-8")

    assert "validate_bundle(install_root, SOURCE_DATABASE)" in builder
    assert '"--release-smoke-test"' in builder
    assert '"unins000.exe"' in builder
    assert "The DFS uninstaller did not remove the application." in builder


def test_layout_verifier_accepts_runtime_payload_and_rejects_source(tmp_path):
    bundle = tmp_path / "DeesFightingShips"
    payload = bundle / "_internal"
    (bundle / "DFS.exe").parent.mkdir(parents=True)
    (bundle / "DFS.exe").write_bytes(b"exe")
    database = payload / "Database" / "Data" / "dfs.db"
    database.parent.mkdir(parents=True)
    database.write_bytes(b"database")
    maps = payload / "resources" / "scenario_maps"
    maps.mkdir(parents=True)
    (maps / "ambush.png").write_bytes(b"png")
    sheets = payload / "output"
    sheets.mkdir(parents=True)
    (sheets / "ship.pdf").write_bytes(b"pdf")

    assert validate_bundle(bundle, database) == []

    forbidden = payload / "platform_data" / "sample.py"
    forbidden.parent.mkdir(parents=True)
    forbidden.write_text("SHIP_NAME = 'Nope'\n", encoding="utf-8")
    errors = validate_bundle(bundle, database)
    assert any("Forbidden development path" in error for error in errors)
