from __future__ import annotations

import hashlib
from pathlib import Path

from dfs.infrastructure.sqlite.connection import SQLiteConnectionFactory
from dfs.infrastructure.sqlite.platform_repository import SQLitePlatformRepository
from dfs.runtime_database import prepare_runtime_database
from dfs.services.platform_catalog_service import PlatformCatalogService


PROJECT_ROOT = Path(__file__).resolve().parents[3]
DB_PATH = PROJECT_ROOT / "Database" / "Data" / "dfs.db"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_runtime_profiles_do_not_mutate_the_canonical_database():
    before = _sha256(DB_PATH)
    runtime_path = prepare_runtime_database(DB_PATH)
    after = _sha256(DB_PATH)

    catalog = PlatformCatalogService(
        SQLitePlatformRepository(SQLiteConnectionFactory(runtime_path))
    )

    assert after == before
    assert catalog.count_profiles() == 304
    assert catalog.count_profiles(include_generated=True) == 427
