from __future__ import annotations

from pathlib import Path

from dfs.domain.tactical import (
    SCENARIO_MAP_FILES,
    TacticalGameState,
    TacticalUnitState,
    TrackState,
    UnitDisposition,
    UnitKind,
)
from dfs.infrastructure.tactical import JSONTacticalGameStore


def _ship() -> TacticalUnitState:
    return TacticalUnitState(
        unit_id="ship-1",
        source_entry_id="entry-1",
        profile_id=1,
        parent_unit_id=None,
        kind=UnitKind.PLATFORM,
        platform_name="Test Cruiser",
        damage=TrackState.create(10, threshold=3),
        crew=TrackState.create(8, threshold=2),
    )


def test_damage_can_continue_below_zero_for_the_disposition_modifier() -> None:
    ship = _ship().apply_damage_expression("-12")

    assert ship.damage.current == -2
    assert ship.is_crippled is True
    assert ship.is_destroyed is False

    ship = ship.lose_damage(3)
    assert ship.damage.current == -5

    ship = ship.restore_damage(4)
    assert ship.damage.current == -1


def test_destroyed_disposition_can_be_corrected_without_changing_damage() -> None:
    stricken = _ship().set_damage_current(-3)
    destroyed = stricken.set_disposition(UnitDisposition.DESTROYED)

    assert destroyed.is_destroyed is True

    corrected = destroyed.set_disposition(UnitDisposition.OPERATIONAL)
    assert corrected.is_destroyed is False
    assert corrected.destroyed is False
    assert corrected.disposition is UnitDisposition.OPERATIONAL
    assert corrected.damage.current == -3


def test_negative_damage_round_trips_through_game_json(tmp_path: Path) -> None:
    game = TacticalGameState.create(
        name="Negative Damage",
        game_system_id="b5_acta",
        source_fleet_id="fleet",
        source_fleet_name="Fleet",
        units=(_ship().set_damage_current(-7),),
    )
    store = JSONTacticalGameStore()
    path = tmp_path / "negative.dfs-game.json"

    store.save(game, path)
    restored = store.load(path)

    assert restored.get_unit("ship-1").damage.current == -7
    assert restored.get_unit("ship-1").is_destroyed is False


def test_scenario_map_catalog_uses_only_printed_deployment_maps() -> None:
    assert SCENARIO_MAP_FILES["ambush"] == "ambush.png"
    assert SCENARIO_MAP_FILES["battle-of-the-line"] == "battle-of-the-line.png"
    assert SCENARIO_MAP_FILES["initial-contact"] == "initial-contact.png"
    assert "invasion" not in SCENARIO_MAP_FILES
    assert "shadows-of-the-past" not in SCENARIO_MAP_FILES
    assert len(SCENARIO_MAP_FILES) == len(set(SCENARIO_MAP_FILES.values()))
