from __future__ import annotations

from pathlib import Path

from dfs.domain.tactical import (
    TacticalGameState,
    TacticalUnitState,
    TrackState,
    TraitState,
    UnitKind,
    WeaponState,
    apply_critical_rule,
)
from dfs.infrastructure.tactical import JSONTacticalGameStore


def test_sprint_003_state_round_trips_without_changing_schema(tmp_path: Path) -> None:
    unit = TacticalUnitState(
        unit_id="ship-1",
        source_entry_id="entry-1",
        profile_id=1,
        parent_unit_id=None,
        kind=UnitKind.PLATFORM,
        platform_name="Test Ship",
        speed="10",
        turn="2/45o",
        damage=TrackState.create(20, threshold=5),
        crew=TrackState.create(24, threshold=6),
        traits=(TraitState("trait-1", "Scout", destroyed=True),),
        weapons=(WeaponState("weapon-1", "Laser", "F", "20", "4", "Beam", disabled=True),),
    ).set_damage_current(5)
    unit = apply_critical_rule(unit, "engines-thrusters", damage_loss=1, crew_loss=0)
    game = TacticalGameState.create(
        name="Persistence Battle",
        game_system_id="b5_acta",
        source_fleet_id="fleet-1",
        source_fleet_name="Test Fleet",
        units=(unit,),
    )

    path = tmp_path / "combat.dfs-game.json"
    store = JSONTacticalGameStore()
    store.save(game, path)
    loaded = store.load(path)
    restored = loaded.units[0]

    assert loaded.schema_version == 1
    assert restored.crippled is True
    assert restored.effective_speed == "3"
    assert restored.traits[0].destroyed is True
    assert restored.weapons[0].disabled is True
    assert restored.critical_hits[0].rule_key == "engines-thrusters"


def test_temporary_critical_effect_fields_round_trip(tmp_path: Path) -> None:
    unit = TacticalUnitState(
        unit_id="ship-2",
        source_entry_id="entry-2",
        profile_id=2,
        parent_unit_id=None,
        kind=UnitKind.PLATFORM,
        platform_name="Crew Test Ship",
        troops="4",
        damage=TrackState.create(30, threshold=8),
        crew=TrackState.create(40, threshold=10),
    )
    unit = apply_critical_rule(
        unit,
        "crew-hull-breach",
        damage_loss=2,
        crew_loss=4,
        applied_turn=5,
    )
    game = TacticalGameState.create(
        name="Crew Critical Battle",
        game_system_id="b5_acta",
        source_fleet_id="fleet-2",
        source_fleet_name="Test Fleet",
        units=(unit,),
    )
    path = tmp_path / "crew-critical.dfs-game.json"
    store = JSONTacticalGameStore()
    store.save(game, path)
    restored = store.load(path).units[0]

    critical = restored.critical_hits[0]
    assert critical.no_damage_control_this_turn is True
    assert critical.troop_penalty == 2
    assert restored.damage_control_blocked_on_turn(5) is True
    assert restored.damage_control_blocked_on_turn(6) is False
