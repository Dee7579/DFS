"""SQLite connection factory shared by application repositories."""

from __future__ import annotations

import sqlite3
from pathlib import Path

from dfs.domain.in_service import is_available_in_year


class SQLiteConnectionFactory:
    def __init__(self, database_path: str | Path):
        self.database_path = Path(database_path)

    def connect(self) -> sqlite3.Connection:
        if not self.database_path.is_file():
            raise FileNotFoundError(f"DFS database not found: {self.database_path}")

        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA query_only = ON")
        connection.create_function(
            "dfs_year_available",
            2,
            lambda in_service, year: int(is_available_in_year(in_service, year)),
            deterministic=True,
        )
        return connection
