from __future__ import annotations

import pytest

from dfs.domain.tactical import (
    TacticalUnitState,
    TrackState,
    TraitState,
    UnitKind,
    WeaponState,
    apply_critical_rule,
    special_action_availability,
)


def _ship() -> TacticalUnitState:
    return TacticalUnitState(
        unit_id="ship-1",
        source_entry_id="entry-1",
        profile_id=101,
        parent_unit_id=None,
        kind=UnitKind.PLATFORM,
        platform_name="Test Cruiser",
        faction_name="Earth Alliance",
        speed="12",
        turn="2/90o",
        troops="4",
        damage=TrackState.create(32, threshold=8),
        crew=TrackState.create(40, threshold=10),
        shields=TrackState.create(6, recovery="2"),
        traits=(
            TraitState("trait-1", "Jump Engine"),
            TraitState("trait-2", "Shields 6/2"),
        ),
        weapons=(
            WeaponState("weapon-1", "Heavy Laser Cannon", "F", "30", "6", "Beam"),
            WeaponState("weapon-2", "Pulse Cannon", "P", "12", "4", "Twin-Linked"),
        ),
    )


def test_track_arithmetic_supports_relative_and_absolute_values() -> None:
    track = TrackState.create(32)
    assert track.apply_expression("-8").current == 24
    assert track.apply_expression("+4").current == 32
    assert track.apply_expression("17").current == 17
    with pytest.raises(ValueError):
        track.apply_expression("eight")


def test_crippled_threshold_latches_and_modifies_speed_turn_and_shields() -> None:
    ship = _ship().set_damage_current(8)
    assert ship.is_crippled is True
    assert ship.effective_speed == "6"
    assert ship.effective_turn == "1/45°"
    assert ship.speed_is_modified is True
    assert ship.turn_is_modified is True
    assert ship.shields_online is False

    repaired = ship.restore_damage(10)
    assert repaired.damage.current == 18
    assert repaired.is_crippled is True
    assert repaired.effective_speed == "6"


def test_skeleton_crew_blocks_special_actions_and_limits_firing() -> None:
    ship = _ship().set_crew_current(10)
    assert ship.is_skeleton_crew is True
    assert ship.special_actions_blocked is True
    assert any("one weapon system" in item for item in ship.firing_restrictions)


def test_engine_critical_applies_fixed_losses_and_highest_speed_penalty() -> None:
    ship = apply_critical_rule(_ship(), "engines-thrusters", damage_loss=1, crew_loss=0)
    assert ship.damage.current == 31
    assert ship.effective_speed == "10"
    ship = apply_critical_rule(ship, "engines-fuel-systems", damage_loss=2, crew_loss=1)
    assert ship.damage.current == 29
    assert ship.crew.current == 39
    assert ship.effective_speed == "8"

    fuel = ship.critical_hits[-1]
    repaired = ship.set_critical_repaired(fuel.critical_id)
    assert repaired.effective_speed == "10"


def test_weapon_ad_penalties_stack() -> None:
    ship = apply_critical_rule(_ship(), "reactor-capacitors", damage_loss=0, crew_loss=1)
    ship = apply_critical_rule(ship, "weapons-targeting", damage_loss=0, crew_loss=1)
    assert ship.weapon_ad_penalty == 2
    assert ship.effective_attack_dice(ship.weapons[0]) == "4"
    assert ship.effective_attack_dice(ship.weapons[1]) == "2"


def test_targeted_critical_grays_trait_until_repaired() -> None:
    ship = apply_critical_rule(
        _ship(),
        "reactor-power-feedback",
        damage_loss=1,
        crew_loss=1,
        target_keys=("trait-1",),
        target_labels=("Jump Engine",),
    )
    assert ship.trait_is_inactive("trait-1") is True
    critical = ship.critical_hits[-1]
    ship = ship.set_critical_repaired(critical.critical_id)
    assert ship.trait_is_inactive("trait-1") is False


def test_targeted_arc_critical_disables_every_weapon_in_arc() -> None:
    ship = apply_critical_rule(
        _ship(),
        "vital-weapons-control",
        damage_loss=4,
        crew_loss=4,
        target_keys=("F",),
        target_labels=("F",),
    )
    assert ship.weapon_is_inactive("weapon-1") is True
    assert ship.weapon_is_inactive("weapon-2") is False
    with pytest.raises(ValueError, match="cannot be repaired"):
        ship.set_critical_repaired(ship.critical_hits[-1].critical_id)


def test_special_action_inventory_is_populated_and_requirements_are_enforced() -> None:
    actions = {item.action.name: item for item in special_action_availability(_ship())}
    assert actions["All Power to Engines!"].allowed is True
    assert actions["Initiate Jump Point!"].allowed is True
    assert actions["Give Me Ramming Speed!"].allowed is False

    crippled = _ship().set_damage_current(8)
    actions = {item.action.name: item for item in special_action_availability(crippled)}
    assert actions["Give Me Ramming Speed!"].allowed is True


def test_no_special_action_critical_clears_current_action() -> None:
    ship = _ship().set_special_action("All Power to Engines!")
    ship = apply_critical_rule(ship, "reactor-gas-leak", damage_loss=0, crew_loss=3)
    assert ship.special_action == ""
    assert ship.special_actions_blocked is True


def test_manual_weapon_and_trait_status_are_independent_of_source_data() -> None:
    ship = _ship().set_weapon_destroyed("weapon-1").set_trait_destroyed("trait-1")
    assert ship.weapon_status("weapon-1") == "Destroyed"
    assert ship.trait_status("trait-1") == "Destroyed"
    assert _ship().weapon_status("weapon-1") == "Operational"
    assert _ship().trait_status("trait-1") == "Operational"


def test_destroyed_system_traits_stop_providing_their_rules() -> None:
    ship = _ship().set_trait_destroyed("trait-1")
    actions = {item.action.name: item for item in special_action_availability(ship)}
    assert actions["Initiate Jump Point!"].allowed is False

    shieldless = _ship().set_trait_destroyed("trait-2")
    assert shieldless.shields_online is False


def test_crew_criticals_and_skeleton_threshold_modify_troops_and_current_turn_damage_control() -> None:
    ship = apply_critical_rule(
        _ship(),
        "crew-hull-breach",
        damage_loss=2,
        crew_loss=4,
        applied_turn=3,
    )
    assert ship.effective_troops == "2"
    assert ship.damage_control_blocked_on_turn(3) is True
    assert ship.damage_control_blocked_on_turn(4) is False

    skeleton = ship.set_crew_current(10)
    assert skeleton.effective_troops == "0"
