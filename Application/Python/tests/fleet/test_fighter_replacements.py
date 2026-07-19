from pathlib import Path

from dfs.domain.fleet.replacements import (
    replacement_map, replacement_patrol_choices, with_replacement_cost, with_replacement_map,
)
from dfs.infrastructure.sqlite.connection import SQLiteConnectionFactory
from dfs.infrastructure.sqlite.platform_repository import SQLitePlatformRepository
from dfs.services.platform_catalog_service import PlatformCatalogService
from dfs.services.platform_detail_service import PlatformDetailService
from dfs.services.fleet.b5_fighter_replacements import B5FighterReplacementService


def _service():
    db = Path("/mnt/data/dfs(1).db")
    if not db.exists():
        import pytest
        pytest.skip("Local DFS database not available")
    repo = SQLitePlatformRepository(SQLiteConnectionFactory(db))
    return B5FighterReplacementService(PlatformCatalogService(repo), PlatformDetailService(repo)), PlatformDetailService(repo)


def test_narn_frazi_can_be_replaced_by_gorith_and_breaching_pods():
    service, details = _service()
    profile = details.get_profile(6310)  # G'Quan
    opportunities = service.opportunities(profile, 2259)
    assert len(opportunities) == 1
    names = {target.platform_name for target in opportunities[0].targets}
    assert "Gorith Flight" in names
    assert any("Breaching Pod" in name for name in names)


def test_minbari_tishat_is_filtered_before_2231():
    service, details = _service()
    profile = details.get_profile(6386)  # Morshin
    names_2230 = {target.platform_name for o in service.opportunities(profile, 2230) for target in o.targets}
    names_2231 = {target.platform_name for o in service.opportunities(profile, 2231) for target in o.targets}
    assert "Tishat Medium Fighter Flight" not in names_2230
    assert "Tishat Medium Fighter Flight" in names_2231


def test_replacement_options_round_trip_and_cost():
    options = with_replacement_map({}, {"4 Sentri flights": {6434: 3}})
    options = with_replacement_cost(options, "4 Sentri flights", 1)
    assert replacement_map(options) == {"4 Sentri flights": {"6434": 3}}
    assert replacement_patrol_choices(options) == 1
