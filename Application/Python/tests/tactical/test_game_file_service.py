from __future__ import annotations

from pathlib import Path

from dfs.domain.fleet import Fleet, FleetEntry
from dfs.domain.fleet.included_craft import IncludedCraft
from dfs.domain.tactical import UnitKind
from dfs.infrastructure.fleet import JSONFleetStore
from dfs.services.tactical import (
    TacticalGameBuilder,
    TacticalGameService,
    TacticalProfileTemplate,
    TacticalWeaponTemplate,
)


class Resolver:
    def resolve(self, profile_id: int) -> TacticalProfileTemplate:
        assert profile_id == 12
        return TacticalProfileTemplate(
            profile_id=12,
            platform_name="File Test Ship",
            faction_name="Test Faction",
            fleet_name="Test Fleet",
            priority_level="Raid",
            damage_maximum=20,
            crippled_threshold=5,
            crew_maximum=24,
            skeleton_threshold=6,
            shield_maximum=None,
            shield_recovery="",
            crew_quality="4",
            notes=(),
            traits=(),
            weapons=(TacticalWeaponTemplate("Test Gun", "F"),),
            included_craft=(IncludedCraft(1, "Test Fighter flight"),),
            kind=UnitKind.PLATFORM,
        )


def test_service_loads_fleet_builder_file_and_writes_separate_game_file(tmp_path: Path) -> None:
    fleet = Fleet.create("Saved Fleet", "b5_acta", "b5_acta_priority_standard")
    fleet = fleet.add_entry(FleetEntry.create(12, vessel_name="Resolute"))
    fleet_path = tmp_path / "saved.dfs-fleet.json"
    game_path = tmp_path / "battle.dfs-game.json"
    JSONFleetStore().save(fleet, fleet_path)

    service = TacticalGameService(TacticalGameBuilder(Resolver()))
    created = service.create_and_save(fleet_path, game_path)
    loaded = service.load(game_path)

    assert created == loaded
    assert created.source_fleet_id == fleet.fleet_id
    assert created.units[0].vessel_name == "Resolute"
    assert len(created.units) == 2
    assert fleet_path.exists()
    assert game_path.exists()
