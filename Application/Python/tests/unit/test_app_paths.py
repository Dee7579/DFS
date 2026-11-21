from __future__ import annotations

import sys
from pathlib import Path

from dfs.app_paths import (
    APPLICATION_FOLDER_NAME,
    build_application_paths,
    ensure_writable_folder,
    find_application_root,
    find_database_path,
)


def _runtime_tree(tmp_path: Path) -> Path:
    root = tmp_path / "DFS Runtime"
    (root / "resources").mkdir(parents=True)
    (root / "output").mkdir()
    (root / "Database" / "Data").mkdir(parents=True)
    (root / "Database" / "Data" / "dfs.db").write_bytes(b"certified")
    return root


def test_development_assets_remain_read_only_and_user_files_are_isolated(
    tmp_path,
    monkeypatch,
):
    application_root = _runtime_tree(tmp_path)
    local_app_data = tmp_path / "LocalAppData"
    user_documents = tmp_path / "User Documents" / APPLICATION_FOLDER_NAME
    monkeypatch.setattr(sys, "platform", "win32")
    monkeypatch.setenv("LOCALAPPDATA", str(local_app_data))
    monkeypatch.setenv("DFS_USER_DOCUMENTS_PATH", str(user_documents))
    monkeypatch.delenv("DFS_APPLICATION_PATH", raising=False)
    monkeypatch.delenv("DFS_USER_DATA_PATH", raising=False)
    monkeypatch.delenv("DFS_OUTPUT_PATH", raising=False)
    monkeypatch.delattr(sys, "_MEIPASS", raising=False)
    monkeypatch.delattr(sys, "frozen", raising=False)

    paths = build_application_paths(application_root / "dfs" / "app_paths.py")

    assert paths.application_root == application_root
    assert paths.resources_root == application_root / "resources"
    assert paths.reference_sheets_root == application_root / "output"
    assert paths.user_data_root == local_app_data / APPLICATION_FOLDER_NAME
    assert paths.log_file == local_app_data / APPLICATION_FOLDER_NAME / "logs" / "dfs.log"
    assert paths.fleets_root == user_documents / "Fleets"
    assert paths.games_root == user_documents / "Games"
    assert paths.generated_sheets_root == user_documents / "Generated Sheets"

    paths.ensure_user_directories()

    assert paths.logs_root.is_dir()
    assert paths.fleets_root.is_dir()
    assert paths.games_root.is_dir()
    assert paths.generated_sheets_root.is_dir()
    assert not (application_root / "logs").exists()
    assert not (application_root / "fleets").exists()
    assert not (application_root / "games").exists()


def test_packaged_root_is_discovered_from_pyinstaller_bundle(tmp_path, monkeypatch):
    application_root = _runtime_tree(tmp_path)
    monkeypatch.setattr(sys, "_MEIPASS", str(application_root), raising=False)
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.delenv("DFS_APPLICATION_PATH", raising=False)
    monkeypatch.delenv("DFS_DATABASE_PATH", raising=False)

    assert find_application_root(tmp_path / "unrelated" / "dfs_desktop.py") == application_root
    assert find_database_path(tmp_path / "unrelated" / "dfs_desktop.py") == (
        application_root / "Database" / "Data" / "dfs.db"
    )


def test_application_tree_cannot_be_used_as_a_writable_default(tmp_path, monkeypatch):
    application_root = _runtime_tree(tmp_path)
    fallback = tmp_path / "Documents" / APPLICATION_FOLDER_NAME / "Fleets"
    monkeypatch.setenv("DFS_USER_DATA_PATH", str(tmp_path / "data"))
    monkeypatch.setenv(
        "DFS_USER_DOCUMENTS_PATH",
        str(tmp_path / "Documents" / APPLICATION_FOLDER_NAME),
    )
    paths = build_application_paths(application_root)

    selected = ensure_writable_folder(
        str(application_root / "fleets"),
        fallback,
        paths.application_root,
    )

    assert selected == fallback
    assert selected.is_dir()
    assert not (application_root / "fleets").exists()


def test_explicit_environment_overrides_are_respected(tmp_path, monkeypatch):
    application_root = _runtime_tree(tmp_path)
    user_data = tmp_path / "custom-data"
    documents = tmp_path / "custom-documents"
    monkeypatch.setenv("DFS_APPLICATION_PATH", str(application_root))
    monkeypatch.setenv("DFS_USER_DATA_PATH", str(user_data))
    monkeypatch.setenv("DFS_USER_DOCUMENTS_PATH", str(documents))

    paths = build_application_paths(tmp_path / "elsewhere")

    assert paths.application_root == application_root
    assert paths.user_data_root == user_data
    assert paths.documents_root == documents
