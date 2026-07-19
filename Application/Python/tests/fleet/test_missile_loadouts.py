from pathlib import Path

from dfs.domain.fleet.ordnance import missile_loadout_map, with_missile_loadouts
from dfs.infrastructure.sqlite.connection import SQLiteConnectionFactory
from dfs.infrastructure.sqlite.platform_repository import SQLitePlatformRepository
from dfs.services.platform_detail_service import PlatformDetailService
from dfs.services.fleet.b5_missile_loadouts import B5MissileLoadoutService


def _details():
    db = Path('/mnt/data/dfs(1).db')
    if not db.exists():
        import pytest
        pytest.skip('Local DFS database not available')
    repo = SQLitePlatformRepository(SQLiteConnectionFactory(db))
    return PlatformDetailService(repo)


def test_omega_has_configurable_missile_racks_and_year_filtering():
    profile = _details().get_profile(6436)
    service = B5MissileLoadoutService()
    early = service.opportunities('Sagittarius-class Cruiser', profile, 2230)
    late = service.opportunities('Sagittarius-class Cruiser', profile, 2259)
    assert early
    assert all(any(v.variant_id == 'flash' for v in rack.variants) for rack in early)
    assert all(not any(v.variant_id == 'harm' for v in rack.variants) for rack in early)
    assert all(any(v.variant_id == 'harm' for v in rack.variants) for rack in late)


def test_hermes_and_tethys_missile_boat_are_excluded():
    details = _details()
    service = B5MissileLoadoutService()
    assert service.opportunities('Hermes-class Transport', details.get_profile(6319), None) == ()
    assert service.opportunities('Tethys-class Missile Boat (Variant)', details.get_profile(6483), None) == ()


def test_missile_options_round_trip():
    options = with_missile_loadouts({}, {'weapon:0': 'flash', 'weapon:1': 'standard'})
    assert missile_loadout_map(options) == {'weapon:0': 'flash'}


def test_advanced_missile_racks_accept_variants():
    profile = _details().get_profile(6238)
    service = B5MissileLoadoutService()
    racks = service.opportunities('Apollo-class Bombardment Cruiser', profile, 2260)
    assert len(racks) == 4
    assert all('Advanced Missile Rack' in rack.label for rack in racks)
    assert all(any(v.variant_id == 'harm' for v in rack.variants) for rack in racks)
