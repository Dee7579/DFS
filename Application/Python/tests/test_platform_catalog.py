from __future__ import annotations

import os
import unittest
from pathlib import Path

from dfs.bootstrap import build_application_services
from dfs.domain.catalog import PlatformFilter
from dfs.services.platform_detail_service import PlatformNotFoundError


DB_PATH = Path(os.environ.get("DFS_TEST_DB", ""))


@unittest.skipUnless(DB_PATH.is_file(), "Set DFS_TEST_DB to a populated DFS SQLite database")
class PlatformCatalogIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.services = build_application_services(DB_PATH)

    def test_catalog_returns_platforms(self):
        self.assertGreater(self.services.catalog.count(), 0)
        self.assertTrue(self.services.catalog.search(PlatformFilter(limit=5)))

    def test_name_search_finds_hyperion(self):
        rows = self.services.catalog.search(PlatformFilter(search_text="Hyperion", limit=100))
        self.assertTrue(any("Hyperion" in row.name for row in rows))

    def test_trait_filter_uses_exact_trait(self):
        rows = self.services.catalog.search(PlatformFilter(traits=("Jump Engine",), limit=1000))
        self.assertTrue(rows)

    def test_detail_loads_profiles_traits_and_weapons(self):
        summary = self.services.catalog.search(PlatformFilter(search_text="Hyperion-class Cruiser", limit=10))[0]
        detail = self.services.platform_details.get(summary.ship_id)
        self.assertTrue(detail.profiles)
        self.assertTrue(any(profile.weapons for profile in detail.profiles))

    def test_missing_platform_raises_domain_error(self):
        with self.assertRaises(PlatformNotFoundError):
            self.services.platform_details.get(-1)


if __name__ == "__main__":
    unittest.main()
