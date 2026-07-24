from __future__ import annotations

import pytest

from dfs.domain.tactical import GamePhase, TacticalGameState, TacticalUnitState, TrackState, UnitKind


def _ship() -> TacticalUnitState:
    return TacticalUnitState(
        unit_id="ship-1",
        source_entry_id="entry-1",
        profile_id=101,
        parent_unit_id=None,
        kind=UnitKind.PLATFORM,
        platform_name="Test Cruiser",
        vessel_name="Resolute",
        damage=TrackState.create(30, threshold=8),
        crew=TrackState.create(40, threshold=10),
        shields=TrackState.create(6, recovery="2"),
        crew_quality="4",
    )


def test_direct_track_editing_and_game_metadata_methods() -> None:
    unit = (
        _ship()
        .set_damage_current(24)
        .set_crew_current(31)
        .set_shields_current(3)
        .set_crew_quality("5")
        .set_special_action("Close Blast Doors!")
        .set_notes("Turned to port.")
    )
    game = TacticalGameState.create(
        name="First Battle",
        game_system_id="b5_acta_2e",
        source_fleet_id="fleet-1",
        source_fleet_name="Test Fleet",
        units=(unit,),
    )
    game = game.rename("Second Battle").set_turn_number(4).set_phase(GamePhase.ATTACK)

    assert unit.damage.current == 24
    assert unit.crew.current == 31
    assert unit.shields.current == 3
    assert unit.crew_quality == "5"
    assert unit.special_action == "Close Blast Doors!"
    assert unit.notes == "Turned to port."
    assert game.name == "Second Battle"
    assert game.turn_number == 4
    assert game.phase is GamePhase.ATTACK


def test_blank_game_name_and_invalid_turn_are_rejected() -> None:
    game = TacticalGameState.create(
        name="Test Battle",
        game_system_id="b5_acta_2e",
        source_fleet_id="fleet-1",
        source_fleet_name="Test Fleet",
    )

    with pytest.raises(ValueError, match="blank"):
        game.rename("   ")
    with pytest.raises(ValueError, match="at least 1"):
        game.set_turn_number(0)
