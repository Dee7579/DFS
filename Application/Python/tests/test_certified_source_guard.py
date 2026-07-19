from __future__ import annotations

import json
from pathlib import Path
import sqlite3

from dfs.integrity.certified_sources import verify_manifest, write_manifest


def _create_database(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path)
    try:
        for table in (
            "ships",
            "acta_profiles",
            "weapons",
            "traits",
            "profile_fleet_lists",
        ):
            connection.execute(f'CREATE TABLE "{table}" (id INTEGER PRIMARY KEY)')
            connection.execute(f'INSERT INTO "{table}" DEFAULT VALUES')
        connection.commit()
    finally:
        connection.close()


def _create_repository(tmp_path: Path) -> Path:
    platform_data = tmp_path / "Application" / "Python" / "platform_data"
    platform_data.mkdir(parents=True)
    (platform_data / "sample.py").write_text("SHIP_NAME = 'Sample'\n", encoding="utf-8")
    _create_database(tmp_path / "Database" / "Data" / "dfs.db")
    return tmp_path


def test_guard_passes_for_unchanged_sources(tmp_path: Path):
    root = _create_repository(tmp_path)
    write_manifest(root, certification_id="test-baseline")

    result = verify_manifest(root)

    assert result.ok
    assert result.checked_file_count == 2


def test_guard_detects_changed_missing_and_unexpected_platform_files(tmp_path: Path):
    root = _create_repository(tmp_path)
    write_manifest(root, certification_id="test-baseline")
    platform_data = root / "Application" / "Python" / "platform_data"
    (platform_data / "sample.py").write_text("SHIP_NAME = 'Changed'\n", encoding="utf-8")
    (platform_data / "new_ship.py").write_text("SHIP_NAME = 'New'\n", encoding="utf-8")

    result = verify_manifest(root)

    assert not result.ok
    assert {issue.kind for issue in result.issues} == {"changed", "unexpected"}


def test_guard_detects_database_change(tmp_path: Path):
    root = _create_repository(tmp_path)
    write_manifest(root, certification_id="test-baseline")
    database = root / "Database" / "Data" / "dfs.db"
    connection = sqlite3.connect(database)
    try:
        connection.execute("INSERT INTO ships DEFAULT VALUES")
        connection.commit()
    finally:
        connection.close()

    result = verify_manifest(root)

    assert not result.ok
    kinds = {issue.kind for issue in result.issues}
    assert "changed" in kinds
    assert "database_count" in kinds


def test_manifest_refuses_silent_replacement(tmp_path: Path):
    root = _create_repository(tmp_path)
    manifest_path = write_manifest(root, certification_id="test-baseline")

    try:
        write_manifest(root, certification_id="replacement")
    except FileExistsError:
        pass
    else:
        raise AssertionError("Manifest replacement should require overwrite=True")

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["certification_id"] == "test-baseline"
