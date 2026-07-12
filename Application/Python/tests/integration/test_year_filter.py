import os
from pathlib import Path

import pytest

from dfs.bootstrap import build_application_services
from dfs.domain.catalog import PlatformFilter

DB = Path(os.environ.get("DFS_TEST_DATABASE_PATH", Path(__file__).resolve().parents[2] / "dfs.db"))
pytestmark = pytest.mark.skipif(not DB.is_file(), reason="DFS test database not available")


def _services():
    return build_application_services(DB)


def test_until_2261_profiles_appear_before_cutoff():
    services = _services()
    names = {item.name for item in services.catalog.search(PlatformFilter(available_year=2258, limit=1000))}
    assert "Shadow Ship (Ancient)" in names
    assert any("Vorlon" in name for name in names)


def test_until_2261_profiles_disappear_after_cutoff():
    services = _services()
    names = {item.name for item in services.catalog.search(PlatformFilter(available_year=2262, limit=1000))}
    assert "Shadow Ship (Ancient)" not in names
