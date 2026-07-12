"""Filesystem path discovery for the DFS desktop application."""

from __future__ import annotations

import os
from pathlib import Path


class DatabaseNotFoundError(FileNotFoundError):
    """Raised when the DFS SQLite database cannot be located."""


def _search_roots(start: str | Path | None = None) -> tuple[Path, ...]:
    origin = Path(start or __file__).resolve()
    here = origin if origin.is_dir() else origin.parent
    return (here, *here.parents)


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
