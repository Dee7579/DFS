"""Filesystem path discovery for the DFS desktop application."""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from pathlib import Path


APPLICATION_FOLDER_NAME = "Dee's Fighting Ships"


class DatabaseNotFoundError(FileNotFoundError):
    """Raised when the DFS SQLite database cannot be located."""


@dataclass(frozen=True, slots=True)
class ApplicationPaths:
    """Read-only application assets and writable per-user DFS locations."""

    application_root: Path
    resources_root: Path
    reference_sheets_root: Path
    user_data_root: Path
    logs_root: Path
    documents_root: Path
    fleets_root: Path
    games_root: Path
    generated_sheets_root: Path

    @property
    def log_file(self) -> Path:
        return self.logs_root / "dfs.log"

    def ensure_user_directories(self) -> None:
        for folder in (
            self.user_data_root,
            self.logs_root,
            self.documents_root,
            self.fleets_root,
            self.games_root,
            self.generated_sheets_root,
        ):
            folder.mkdir(parents=True, exist_ok=True)


def _search_roots(start: str | Path | None = None) -> tuple[Path, ...]:
    origin = Path(start or __file__).resolve()
    here = origin if origin.is_dir() else origin.parent
    roots: list[Path] = []

    configured = os.environ.get("DFS_APPLICATION_PATH", "").strip()
    if configured:
        roots.append(Path(configured).expanduser().resolve())

    bundled_root = getattr(sys, "_MEIPASS", "")
    if bundled_root:
        roots.append(Path(bundled_root).resolve())

    if getattr(sys, "frozen", False):
        roots.append(Path(sys.executable).resolve().parent)

    roots.extend((here, *here.parents))
    return tuple(dict.fromkeys(roots))


def find_application_root(start: str | Path | None = None) -> Path:
    """Locate the root containing packaged DFS runtime assets."""

    for candidate in _search_roots(start):
        if (candidate / "resources").is_dir() or (candidate / "output").is_dir():
            return candidate

    roots = _search_roots(start)
    for candidate in roots:
        if candidate.name.casefold() == "python":
            return candidate
    return roots[0]


def _default_user_data_root() -> Path:
    if sys.platform == "win32":
        base = os.environ.get("LOCALAPPDATA", "").strip()
        if base:
            return Path(base).expanduser().resolve() / APPLICATION_FOLDER_NAME
        return Path.home() / "AppData" / "Local" / APPLICATION_FOLDER_NAME
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / APPLICATION_FOLDER_NAME
    base = os.environ.get("XDG_DATA_HOME", "").strip()
    if base:
        return Path(base).expanduser().resolve() / "dfs"
    return Path.home() / ".local" / "share" / "dfs"


def _default_documents_root() -> Path:
    configured = os.environ.get("DFS_USER_DOCUMENTS_PATH", "").strip()
    if configured:
        return Path(configured).expanduser().resolve()
    return Path.home() / "Documents" / APPLICATION_FOLDER_NAME


def build_application_paths(start: str | Path | None = None) -> ApplicationPaths:
    """Build the complete DFS filesystem map without writing any files."""

    application_root = find_application_root(start).resolve()
    configured_data = os.environ.get("DFS_USER_DATA_PATH", "").strip()
    user_data_root = (
        Path(configured_data).expanduser().resolve()
        if configured_data
        else _default_user_data_root().resolve()
    )
    documents_root = _default_documents_root().resolve()
    return ApplicationPaths(
        application_root=application_root,
        resources_root=(application_root / "resources").resolve(),
        reference_sheets_root=find_output_path(application_root),
        user_data_root=user_data_root,
        logs_root=user_data_root / "logs",
        documents_root=documents_root,
        fleets_root=documents_root / "Fleets",
        games_root=documents_root / "Games",
        generated_sheets_root=documents_root / "Generated Sheets",
    )


def ensure_writable_folder(
    configured: str,
    fallback: str | Path,
    application_root: str | Path,
) -> Path:
    """Create a user folder, rejecting paths inside read-only app assets."""

    default = Path(fallback).expanduser().resolve()
    folder = Path(configured).expanduser().resolve() if configured.strip() else default
    read_only_root = Path(application_root).resolve()
    if folder == read_only_root or read_only_root in folder.parents:
        folder = default
    folder.mkdir(parents=True, exist_ok=True)
    return folder


def find_database_path(start: str | Path | None = None) -> Path:
    configured = os.environ.get("DFS_DATABASE_PATH", "").strip()
    if configured:
        candidate = Path(configured).expanduser().resolve()
        if candidate.is_file():
            return candidate
        raise DatabaseNotFoundError(f"DFS_DATABASE_PATH points to a missing file: {candidate}")

    for parent in _search_roots(start):
        for candidate in (
            parent / "dfs.db",
            parent / "Database" / "Data" / "dfs.db",
            parent / "Database" / "dfs.db",
            parent / "Data" / "dfs.db",
        ):
            if candidate.is_file():
                return candidate.resolve()
    raise DatabaseNotFoundError(
        "DFS could not locate dfs.db. Put it in Database/Data/dfs.db or set DFS_DATABASE_PATH."
    )


def find_output_path(start: str | Path | None = None) -> Path:
    """Locate the packaged, read-only library of master reference sheets."""

    configured = os.environ.get("DFS_OUTPUT_PATH", "").strip()
    if configured:
        return Path(configured).expanduser().resolve()
    for parent in _search_roots(start):
        candidate = parent / "output"
        if candidate.is_dir():
            return candidate.resolve()
    # Return the conventional Python/output path even if it has not been generated yet.
    roots = _search_roots(start)
    for parent in roots:
        if parent.name.casefold() == "python":
            return (parent / "output").resolve()
    return (roots[0] / "output").resolve()
