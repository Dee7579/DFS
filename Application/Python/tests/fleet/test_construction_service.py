from pathlib import Path

import pytest

from dfs.infrastructure.sqlite.connection import SQLiteConnectionFactory
from dfs.infrastructure.sqlite.platform_repository import SQLitePlatformRepository
from dfs.services.fleet import FleetConstructionService


DB = Path(__file__).resolve().parents[3] / "dfs(1).db"


@pytest.mark.skipif(not DB.exists(), reason="Integration database not mounted")
def test_b5_fleet_resolves_profiles_and_validates():
    repository = SQLitePlatformRepository(SQLiteConnectionFactory(DB))
    service = FleetConstructionService(repository)
    fleet = service.create_fleet(
        "Third Age Raid",
        faction_id=1,
        fleet_list_id=3,
        selected_year=2259,
        scenario_priority="Raid",
        fleet_allocation_points=3,
    )
    fleet = service.add_profile(fleet, 6325, quantity=1)  # Raid Hyperion
    fleet = service.add_profile(fleet, 6405, quantity=1)  # Battle Omega
    summary = service.summarize(fleet)
    assert summary.validation.is_valid
    assert summary.priority_counts == {"Raid": 1, "Battle": 1}
