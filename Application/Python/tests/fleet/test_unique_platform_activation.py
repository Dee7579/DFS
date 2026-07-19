from dataclasses import replace

from dfs.domain.catalog import PlatformProfile
from dfs.domain.fleet import Fleet, FleetEntry
from dfs.services.fleet.b5_acta_profile import (
    B5ACTAAdvisoryPriorityProfile,
    B5ACTASandboxProfile,
    B5ACTAStandardPriorityProfile,
)


def ancient(profile_id: int, name: str = "Ancient Vessel") -> PlatformProfile:
    profile = PlatformProfile(
        profile_id=profile_id,
        fleet_list_id=19,
        fleet_name="The Ancients",
        initiative="+4",
        priority_level="Ancient",
        speed="10",
        turn="1/45",
        hull="6",
        damage="100/20",
        crew="100/20",
        troops="0",
        craft="",
        in_service="-2261",
        source_book="Fleet Lists",
    )
    return profile


def fleet_with(quantity: int, profile_id: str = "b5_acta_priority_standard"):
    fleet = Fleet.create(
        "Ancient Test",
        "b5_acta",
        profile_id,
        faction_id=16,
        fleet_list_id=19,
    )
    entry = FleetEntry.create(1001, quantity)
    fleet = replace(
        fleet,
        entries=(entry,),
        metadata={"scenario_priority": "Armageddon", "fleet_allocation_points": 10},
    )
    return fleet, {entry.entry_id: ancient(1001)}


def test_standard_profile_rejects_duplicate_ancient_platform():
    fleet, resolved = fleet_with(2)
    messages = B5ACTAStandardPriorityProfile().rule_engine.evaluate(fleet, resolved)
    unique = [m for m in messages if m.rule_id == "B5-ANCIENT-UNQ-001"]
    assert len(unique) == 1
    assert "2 copies" in unique[0].message
    assert "one copy" in unique[0].remedy


def test_different_ancient_platforms_are_each_allowed_once():
    fleet, resolved = fleet_with(1)
    second = FleetEntry.create(1002, 1)
    fleet = replace(fleet, entries=(*fleet.entries, second))
    resolved[second.entry_id] = ancient(1002, "Second Ancient")
    messages = B5ACTAStandardPriorityProfile().rule_engine.evaluate(fleet, resolved)
    assert not [m for m in messages if m.rule_id == "B5-ANCIENT-UNQ-001"]


def test_advisory_demotes_unique_failure_and_sandbox_ignores_it():
    advisory_fleet, resolved = fleet_with(2, "b5_acta_priority_advisory")
    advisory = B5ACTAAdvisoryPriorityProfile().validate(advisory_fleet, resolved)
    assert any(m.code == "B5-ANCIENT-UNQ-001" for m in advisory.warnings)
    sandbox_fleet, resolved = fleet_with(2, "b5_acta_sandbox")
    assert B5ACTASandboxProfile().validate(sandbox_fleet, resolved).is_valid


def unique_trait_profile(profile_id: int = 2001) -> PlatformProfile:
    return PlatformProfile(
        profile_id=profile_id,
        fleet_list_id=10,
        fleet_name="Interstellar Alliance",
        initiative="+2",
        priority_level="Skirmish",
        speed="10",
        turn="2/45",
        hull="4",
        damage="26/5",
        crew="22/4",
        troops="-",
        craft="1 Flyer Flight",
        in_service="2248+",
        source_book="Fleet Lists",
        traits=("Scout", "Unique"),
    )


def test_unique_trait_rejects_second_copy():
    profile = unique_trait_profile()
    fleet = Fleet.create(
        "ISA Unique Test", "b5_acta", "b5_acta_priority_standard",
        faction_id=7, fleet_list_id=10,
    )
    entry = FleetEntry.create(profile.profile_id, 2)
    fleet = replace(
        fleet, entries=(entry,),
        metadata={"scenario_priority": "Skirmish", "fleet_allocation_points": 2},
    )
    messages = B5ACTAStandardPriorityProfile().rule_engine.evaluate(
        fleet, {entry.entry_id: profile}
    )
    unique = [m for m in messages if m.rule_id == "B5-UNIQUE-TRAIT-001"]
    assert len(unique) == 1
    assert "2 copies" in unique[0].message
