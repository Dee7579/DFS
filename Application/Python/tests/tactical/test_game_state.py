from __future__ import annotations

from dfs.domain.tactical import (
    CriticalHitState,
    GamePhase,
    TacticalGameState,
    TacticalUnitState,
    TrackState,
    TraitState,
    UnitKind,
    WeaponState,
)


def _unit() -> TacticalUnitState:
    return TacticalUnitState(
        unit_id="unit-1",
        source_entry_id="entry-1",
        profile_id=7,
        parent_unit_id=None,
        kind=UnitKind.PLATFORM,
        platform_name="Test Ship",
        damage=TrackState.create(30, threshold=8),
        crew=TrackState.create(40, threshold=10),
        shields=TrackState.create(6, recovery="2"),
        crew_quality="4",
        traits=(TraitState("trait-1", "Jump Engine"),),
        weapons=(WeaponState("weapon-1", "Laser", "F"),),
    )


def test_live_state_tracks_required_tactical_changes() -> None:
    unit = _unit()
    critical = CriticalHitState.create("Engines damaged", "Speed -2")
    unit = (
        unit.lose_damage(5)
        .lose_crew(6)
        .lose_shields(4)
        .set_trait_disabled("trait-1")
        .set_weapon_disabled("weapon-1")
        .set_special_action("All Stop!")
        .add_critical(critical)
        .set_critical_repaired(critical.critical_id)
    )

    assert unit.damage.current == 25
    assert unit.crew.current == 34
    assert unit.shields.current == 2
    assert unit.traits[0].disabled is True
    assert unit.weapons[0].disabled is True
    assert unit.special_action == "All Stop!"
    assert unit.critical_hits[0].repaired is True


def test_turn_phase_and_fighter_losses_are_derived_from_game_state() -> None:
    ship = _unit()
    fighter = TacticalUnitState(
        unit_id="fighter-1",
        source_entry_id="entry-2",
        profile_id=8,
        parent_unit_id=None,
        kind=UnitKind.CRAFT,
        platform_name="Fighter flight",
        destroyed=True,
    )
    game = TacticalGameState.create(
        name="Test Battle",
        game_system_id="b5_acta",
        source_fleet_id="fleet-1",
        source_fleet_name="Test Fleet",
        units=(ship, fighter),
    )

    game = game.set_phase(GamePhase.ATTACK).advance_turn()

    assert game.turn_number == 2
    assert game.phase is GamePhase.INITIATIVE
    assert game.craft_losses == 1
