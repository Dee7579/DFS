from __future__ import annotations

from dfs.domain.fleet import Fleet, FleetEntry
from dfs.domain.fleet.included_craft import IncludedCraft
from dfs.domain.tactical import UnitKind
from dfs.services.tactical import TacticalGameBuilder, TacticalProfileTemplate, TacticalWeaponTemplate


class FakeResolver:
    def __init__(self) -> None:
        self.templates = {
            101: TacticalProfileTemplate(
                profile_id=101,
                platform_name="Test Cruiser",
                faction_name="Test Faction",
                fleet_name="Test Fleet",
                priority_level="Raid",
                damage_maximum=40,
                crippled_threshold=10,
                crew_maximum=50,
                skeleton_threshold=12,
                shield_maximum=10,
                shield_recovery="2",
                crew_quality="4",
                notes=("Source note",),
                traits=("Jump Engine", "Shields 10/2"),
                weapons=(TacticalWeaponTemplate("Pulse Cannon", "F"),),
                included_craft=(IncludedCraft(2, "Test Fighter flights"),),
                kind=UnitKind.PLATFORM,
            ),
            202: TacticalProfileTemplate(
                profile_id=202,
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
                notes=("Wing of four flights",),
                traits=("Dodge 2+",),
                weapons=(TacticalWeaponTemplate("Light Cannon", "T"),),
                included_craft=(),
                kind=UnitKind.CRAFT,
            ),
        }

    def resolve(self, profile_id: int) -> TacticalProfileTemplate:
        return self.templates[profile_id]


def _fleet() -> Fleet:
    fleet = Fleet.create(
        "Test Fleet",
        "b5_acta",
        "b5_acta_priority_standard",
        faction_id=1,
        fleet_list_id=2,
        selected_year=2261,
    )
    fleet = fleet.add_entry(FleetEntry.create(101, quantity=2, vessel_name="Defiant"))
    return fleet.add_entry(FleetEntry.create(202, quantity=3))


def test_builder_expands_every_platform_and_fighter_flight() -> None:
    game = TacticalGameBuilder(FakeResolver()).build(_fleet())

    platforms = [unit for unit in game.units if unit.kind is UnitKind.PLATFORM]
    craft = [unit for unit in game.units if unit.kind is UnitKind.CRAFT]

    assert len(platforms) == 2
    assert len(craft) == 7  # 4 included flights plus 3 purchased flights
    assert platforms[0].vessel_name == "Defiant"
    assert platforms[1].vessel_name == ""
    assert platforms[0].damage.maximum == 40
    assert platforms[0].damage.threshold == 10
    assert platforms[0].crew.maximum == 50
    assert platforms[0].crew.threshold == 12
    assert platforms[0].shields.maximum == 10
    assert platforms[0].shields.recovery == "2"
    assert platforms[0].crew_quality == "4"
    assert platforms[0].traits[0].name == "Jump Engine"
    assert platforms[0].weapons[0].name == "Pulse Cannon"

    included = [unit for unit in craft if unit.profile_id is None]
    purchased = [unit for unit in craft if unit.profile_id == 202]
    assert len(included) == 4
    assert len(purchased) == 3
    assert all(unit.parent_unit_id for unit in included)
    assert all(unit.parent_unit_id is None for unit in purchased)
    assert {unit.parent_unit_id for unit in included} == {unit.unit_id for unit in platforms}


def test_game_is_independent_from_source_fleet_objects() -> None:
    fleet = _fleet()
    game = TacticalGameBuilder(FakeResolver()).build(fleet)
    first = game.units[0]

    updated = game.replace_unit(first.lose_damage(7).lose_crew(3).lose_shields(4))

    assert updated.units[0].damage.current == 33
    assert updated.units[0].crew.current == 47
    assert updated.units[0].shields.current == 6
    assert fleet.entries[0].quantity == 2
    assert fleet.entries[0].vessel_name == "Defiant"


def test_builder_applies_saved_fighter_replacements_and_huge_hangar_choices() -> None:
    resolver = FakeResolver()
    resolver.templates[303] = TacticalProfileTemplate(
        profile_id=303,
        platform_name="Replacement Fighter",
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
        notes=(),
        traits=("Dodge 2+",),
        weapons=(TacticalWeaponTemplate("Replacement Gun", "T"),),
        included_craft=(),
        kind=UnitKind.CRAFT,
    )
    resolver.templates[404] = TacticalProfileTemplate(
        profile_id=404,
        platform_name="Embarked Raider",
        faction_name="Test Faction",
        fleet_name="Test Fleet",
        priority_level="Skirmish",
        damage_maximum=12,
        crippled_threshold=3,
        crew_maximum=14,
        skeleton_threshold=4,
        shield_maximum=None,
        shield_recovery="",
        crew_quality="4",
        notes=(),
        traits=(),
        weapons=(TacticalWeaponTemplate("Raider Gun", "F"),),
        included_craft=(IncludedCraft(1, "Raider Fighter flight"),),
        kind=UnitKind.PLATFORM,
    )

    fleet = Fleet.create("Options Fleet", "b5_acta", "b5_acta_priority_standard")
    entry = FleetEntry.create(
        101,
        quantity=2,
        options={
            "craft_replacements": {"Test Fighter flights": {"303": 2}},
            "huge_hangars": {"profile_ids": [404]},
        },
    )
    game = TacticalGameBuilder(resolver).build(fleet.add_entry(entry))

    primary = [unit for unit in game.units if unit.profile_id == 101]
    replacements = [unit for unit in game.units if unit.profile_id == 303]
    originals = [unit for unit in game.units if unit.profile_id is None and unit.platform_name == "Test Fighter flights"]
    embarked = [unit for unit in game.units if unit.profile_id == 404]
    embarked_craft = [unit for unit in game.units if unit.platform_name == "Raider Fighter flight"]

    assert len(primary) == 2
    assert len(replacements) == 2
    assert len(originals) == 2
    assert len(embarked) == 1
    assert len(embarked_craft) == 1
    assert replacements[0].parent_unit_id != replacements[1].parent_unit_id
    assert embarked[0].parent_unit_id in {unit.unit_id for unit in primary}
    assert embarked_craft[0].parent_unit_id == embarked[0].unit_id
    assert all(unit.metadata["replacement_profile_id"] == 303 for unit in replacements)
