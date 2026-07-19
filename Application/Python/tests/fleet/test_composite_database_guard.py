from __future__ import annotations

import hashlib
from pathlib import Path
import shutil
import sqlite3

import pytest

from dfs.services.fleet.b5_composite_fleets import (
    CanonicalDatabaseWriteError,
    canonical_database_path,
    ensure_b5_composite_fleets,
)


CANONICAL_DB = canonical_database_path()


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _profile_count(path: Path) -> int:
    connection = sqlite3.connect(path)
    try:
        return int(connection.execute("SELECT COUNT(*) FROM acta_profiles").fetchone()[0])
    finally:
        connection.close()


def test_composite_generation_refuses_the_canonical_database() -> None:
    before = _sha256(CANONICAL_DB)

    with pytest.raises(CanonicalDatabaseWriteError):
        ensure_b5_composite_fleets(CANONICAL_DB)

    assert _sha256(CANONICAL_DB) == before


def test_composite_generation_uses_a_disposable_copy(tmp_path: Path) -> None:
    before = _sha256(CANONICAL_DB)
    runtime_db = tmp_path / "dfs.db"
    shutil.copy2(CANONICAL_DB, runtime_db)
    starting_profiles = _profile_count(runtime_db)

    ensure_b5_composite_fleets(runtime_db)

    assert _profile_count(runtime_db) > starting_profiles
    assert _sha256(CANONICAL_DB) == before
