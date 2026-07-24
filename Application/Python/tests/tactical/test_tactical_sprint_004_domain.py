from __future__ import annotations

from pathlib import Path

from dfs.domain.fleet import Fleet, FleetEntry
from dfs.domain.fleet.included_craft import IncludedCraft
from dfs.domain.tactical import (
    CRITICAL_SYSTEMS_TABLE_HELP,
    TacticalGameState,
    TacticalUnitState,
    TrackState,
    TraitState,
    UnitKind,
    WeaponState,
    apply_critical_rule,
    roll_loss_expression,
)
from dfs.infrastructure.tactical import JSONTacticalGameStore
from dfs.services.tactical import TacticalGameBuilder, TacticalProfileTemplate, TacticalWeaponTemplate


class _FixedDice:
    def __init__(self, values: list[int]) -> None:
        self.values = iter(values)

    def randint(self, _minimum: int, _maximum: int) -> int:
        return next(self.values)


def _ship() -> TacticalUnitState:
    return TacticalUnitState(
        unit_id="ship-1",
        source_entry_id="entry-1",
        profile_id=10,
        parent_unit_id=None,
        kind=UnitKind.PLATFORM,
        platform_name="Test Cruiser",
        damage=TrackState.create(32, threshold=8),
        crew=TrackState.create(40, threshold=10),
        speed="12",
        turn="2/45o",
        traits=(TraitState("trait-1", "Advanced Jump Engine"),),
        weapons=(WeaponState("weapon-1", "Laser", "F", "18", "4", "Beam"),),
        special_action="All Power to Engines!",
    )


def test_dice_expression_rolls_and_systems_chart_are_source_backed() -> None:
    assert roll_loss_expression("4D6", _FixedDice([1, 2, 3, 4])) == 10
    assert roll_loss_expression("2d6", _FixedDice([6, 5])) == 11
    assert roll_loss_expression("4", _FixedDice([])) == 4
    assert "1-2  Engines" in CRITICAL_SYSTEMS_TABLE_HELP
    assert "6     Vital Systems" in CRITICAL_SYSTEMS_TABLE_HELP


def test_undo_last_critical_restores_exact_pre_application_state() -> None:
    ship = _ship().set_damage_current(10).set_crew_current(12)
    damaged = apply_critical_rule(
        ship,
        "vital-reactor-implosion",
        damage_loss=8,
        crew_loss=4,
        target_keys=("trait-1",),
        target_labels=("Advanced Jump Engine",),
    )
    assert damaged.damage.current == 2
    assert damaged.crew.current == 8
    assert damaged.is_crippled is True
    assert damaged.is_skeleton_crew is True
    assert damaged.special_action == "All Power to Engines!"

    restored = damaged.undo_last_critical()
    assert restored.damage.current == 10
    assert restored.crew.current == 12
    assert restored.crippled is False
    assert restored.skeleton_crew is False
    assert restored.special_action == "All Power to Engines!"
    assert restored.critical_hits == ()


def test_craft_ready_launched_status_and_battle_report_round_trip(tmp_path: Path) -> None:
    craft = TacticalUnitState(
        unit_id="fighter-1",
        source_entry_id="entry-1",
        profile_id=20,
        parent_unit_id="ship-1",
        kind=UnitKind.CRAFT,
        platform_name="Test Fighter",
    ).set_craft_status("launched")
    game = TacticalGameState.create(
        name="Report Battle",
        game_system_id="b5_acta_2e",
        source_fleet_id="fleet-1",
        source_fleet_name="Test Fleet",
        units=(_ship(), craft),
    ).end_game(victory_points=12, opponent_victory_points=8, notes="Held the field")

    path = tmp_path / "report.dfs-game.json"
    JSONTacticalGameStore().save(game, path)
    restored = JSONTacticalGameStore().load(path)

    assert restored.get_unit("fighter-1").effective_craft_status == "launched"
    assert restored.victory_points == 12
    assert restored.opponent_victory_points == 8
    assert restored.battle_result == "Victory"
    assert restored.battle_report_notes == "Held the field"
    assert restored.ended_at


class _Resolver:
    def __init__(self) -> None:
        self.ship = TacticalProfileTemplate(
            profile_id=1,
            platform_name="Carrier",
            faction_name="Test Faction",
            fleet_name="Test Fleet",
            priority_level="Raid",
            damage_maximum=30,
            crippled_threshold=8,
            crew_maximum=35,
            skeleton_threshold=9,
            shield_maximum=None,
            shield_recovery="",
            crew_quality="4",
            notes=(),
            traits=("Carrier 2",),
            weapons=(TacticalWeaponTemplate("Pulse Cannon", "F", "10", "4", "Twin-Linked"),),
            included_craft=(IncludedCraft(2, "Test Fighter flights"),),
            kind=UnitKind.PLATFORM,
        )
        self.fighter = TacticalProfileTemplate(
            profile_id=2,
            platform_name="Test Fighter",
            faction_name="Test Faction",
            fleet_name="Test Fleet",
            priority_level="Patrol",
            damage_maximum=None,
            crippled_threshold=None,
            crew_maximum=None,
            skeleton_threshold=None,
            shield_maximum=None,
            shield_recovery="",
            crew_quality="",
            notes=("Dogfight +1",),
            traits=("Dodge 2+", "Fighter"),
            weapons=(TacticalWeaponTemplate("Light Cannon", "T", "2", "2", "Anti-Fighter"),),
            included_craft=(),
            kind=UnitKind.CRAFT,
        )

    def resolve(self, profile_id: int) -> TacticalProfileTemplate:
        return self.ship if profile_id == 1 else self.fighter

    def resolve_included_craft(self, _name: str, **_kwargs) -> TacticalProfileTemplate:
        return self.fighter


def test_carried_fighter_uses_resolved_profile_weapons_and_traits() -> None:
    fleet = Fleet.create("Carrier Fleet", "b5_acta_2e", "b5_acta_priority_standard")
    fleet = fleet.add_entry(FleetEntry.create(1))
    game = TacticalGameBuilder(_Resolver()).build(fleet)

    craft = [unit for unit in game.units if unit.kind is UnitKind.CRAFT]
    assert len(craft) == 2
    assert all(unit.profile_id == 2 for unit in craft)
    assert all(unit.weapons[0].name == "Light Cannon" for unit in craft)
    assert all(unit.traits[0].name == "Dodge 2+" for unit in craft)


def test_legacy_blank_carried_fighter_snapshot_is_hydrated() -> None:
    legacy = TacticalUnitState(
        unit_id="legacy-fighter",
        source_entry_id="entry-1",
        profile_id=None,
        parent_unit_id="ship-1",
        kind=UnitKind.CRAFT,
        platform_name="Test Fighter flights",
        faction_name="Test Faction",
        fleet_name="Test Fleet",
        metadata={"included_craft_source": "Test Fighter flights"},
    )
    game = TacticalGameState.create(
        name="Legacy Battle",
        game_system_id="b5_acta_2e",
        source_fleet_id="fleet-1",
        source_fleet_name="Test Fleet",
        units=(_ship(), legacy),
    )

    hydrated = TacticalGameBuilder(_Resolver()).hydrate_missing_craft(game)
    fighter = hydrated.get_unit("legacy-fighter")
    assert fighter.profile_id == 2
    assert fighter.platform_name == "Test Fighter"
    assert fighter.weapons[0].name == "Light Cannon"
    assert fighter.traits[0].name == "Dodge 2+"
    assert fighter.metadata["legacy_snapshot_hydrated"] is True
