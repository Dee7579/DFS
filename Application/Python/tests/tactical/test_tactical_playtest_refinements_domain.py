from __future__ import annotations

import pytest

from dfs.domain.tactical import (
    CriticalHitState,
    TacticalGameState,
    TacticalUnitState,
    TrackState,
    TraitState,
    UnitDisposition,
    UnitKind,
    apply_critical_rule,
)
from dfs.infrastructure.tactical import JSONTacticalGameStore


def _ship(**changes) -> TacticalUnitState:
    values = dict(
        unit_id="ship-1",
        source_entry_id="entry-1",
        profile_id=1,
        parent_unit_id=None,
        kind=UnitKind.PLATFORM,
        platform_name="Omega-class Destroyer",
        speed="12",
        damage=TrackState.create(30, threshold=8),
        crew=TrackState.create(40, threshold=10),
        crew_quality="4",
    )
    values.update(changes)
    return TacticalUnitState(**values)


def test_complete_critical_hit_and_multiplier_apply_every_loss() -> None:
    ship = apply_critical_rule(
        _ship(),
        "engines-fuel-systems",
        damage_loss=2,
        crew_loss=1,
        damage_multiplier=2,
        include_solid_hit=True,
        applied_turn=3,
    )
    critical = ship.critical_hits[-1]
    assert critical.damage_loss == 6
    assert critical.crew_loss == 4
    assert critical.damage_multiplier == 2
    assert ship.damage.current == 24
    assert ship.crew.current == 36


def test_critical_is_new_until_the_following_turn() -> None:
    critical = CriticalHitState.create(
        "Thrusters Damaged",
        repairable=True,
        applied_turn=3,
    )
    ship = _ship(critical_hits=(critical,))

    assert critical.repair_status(3) == "New"
    assert critical.repair_status(4) == "Repairable"
    with pytest.raises(ValueError, match="same turn"):
        ship.set_critical_repaired(
            critical.critical_id,
            current_turn=3,
        )
    repaired = ship.set_critical_repaired(
        critical.critical_id,
        current_turn=4,
    )
    assert repaired.critical_hits[0].repair_status(4) == "Repaired"


def test_adrift_keeps_current_speed_and_exposes_compulsory_movement() -> None:
    crippled = _ship().set_damage_current(8).set_disposition(UnitDisposition.ADRIFT)
    assert crippled.effective_speed == "6"
    assert crippled.adrift_movement == "3"


def test_damage_control_equation_lists_every_live_modifier() -> None:
    multiple_fires = CriticalHitState.create(
        "Multiple Fires",
        rule_key="crew-multiple-fires",
        applied_turn=1,
    )
    ship = _ship(
        traits=(TraitState("self-repairing", "Self-Repairing 2"),),
        critical_hits=(multiple_fires,),
        special_action="All Hands on Deck!",
    ).set_crew_current(10)
    equation = ship.damage_control_equation(2)
    assert "1D6 + CQ 4" in equation
    assert "- 2 Skeleton Crew" in equation
    assert "- 1 Multiple Fires" in equation
    assert "+ 1 Self-Repairing" in equation
    assert "+ 2 All Hands on Deck!" in equation
    assert "9+ repairs" in equation


def test_tactical_ship_name_remains_separate_from_platform_name() -> None:
    named = _ship().set_vessel_name("Agamemnon")
    assert named.vessel_name == "Agamemnon"
    assert named.platform_name == "Omega-class Destroyer"


def test_name_turn_and_multiplier_round_trip_without_schema_break(tmp_path) -> None:
    named = _ship().set_vessel_name("Agamemnon")
    damaged = apply_critical_rule(
        named,
        "engines-thrusters",
        damage_loss=1,
        crew_loss=0,
        include_solid_hit=True,
        damage_multiplier=3,
        applied_turn=2,
    )
    game = TacticalGameState.create(
        name="Round Trip",
        game_system_id="b5_acta_2e",
        source_fleet_id="fleet",
        source_fleet_name="Fleet",
        units=(damaged,),
    ).set_turn_number(2)
    path = tmp_path / "round-trip.dfs-game.json"
    store = JSONTacticalGameStore()
    store.save(game, path)
    restored = store.load(path).get_unit("ship-1")
    assert restored.vessel_name == "Agamemnon"
    assert restored.critical_hits[0].applied_turn == 2
    assert restored.critical_hits[0].damage_multiplier == 3
    assert restored.critical_hits[0].repair_status(2) == "New"
