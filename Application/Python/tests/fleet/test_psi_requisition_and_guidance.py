from dfs.domain.catalog import PlatformProfile
from dfs.domain.fleet.models import Fleet, FleetEntry
from dfs.domain.fleet.priority import format_unaffordable_choice
from dfs.domain.fleet.rules import RuleContext
from dfs.services.fleet.b5_allied_contingents import AlliedContingentRule, definition_for


def profile(profile_id: int, fleet_list_id: int, fleet_name: str, priority: str) -> PlatformProfile:
    return PlatformProfile(
        profile_id=profile_id,
        fleet_list_id=fleet_list_id,
        fleet_name=fleet_name,
        initiative="+0",
        priority_level=priority,
        speed="8",
        turn="2/45°",
        hull="5",
        damage="20/5",
        crew="20/5",
        troops="2",
        craft="None",
        in_service="2250+",
        source_book="Fleet Lists",
    )


def test_psi_definition_allows_one_ea_era_and_two_fap():
    fleet = Fleet.create("Psi", "b5-acta-2e", "official", faction_id=18, fleet_list_id=21)
    definition = definition_for(fleet)
    assert definition is not None
    assert definition.allowed_fleet_list_ids == (1, 3, 4)
    assert definition.max_allied_source_lists == 1
    assert definition.max_scenario_fap == 2


def test_psi_two_raid_fap_are_legal_but_three_are_not():
    entries = [FleetEntry.create(i) for i in (101, 102)]
    fleet = Fleet.create("Psi", "b5-acta-2e", "official", faction_id=18, fleet_list_id=21)
    fleet = fleet.replace_entries(tuple(entries))
    fleet = type(fleet)(
        **{field: getattr(fleet, field) for field in fleet.__dataclass_fields__ if field != "metadata"},
        metadata={"scenario_priority": "Raid"},
    )
    profiles = {
        entries[0].entry_id: profile(101, 3, "Earth Alliance - Third Age", "Raid"),
        entries[1].entry_id: profile(102, 3, "Earth Alliance - Third Age", "Raid"),
    }
    context = RuleContext(fleet, profiles)
    assert AlliedContingentRule().evaluate(context) == ()

    third = FleetEntry.create(103)
    fleet3 = fleet.replace_entries((*fleet.entries, third))
    profiles3 = {**profiles, third.entry_id: profile(103, 3, "Earth Alliance - Third Age", "Raid")}
    messages = AlliedContingentRule().evaluate(RuleContext(fleet3, profiles3))
    assert len(messages) == 1
    assert "exceeds 2 Raid Fleet Allocation Points" in messages[0].message


def test_psi_cannot_mix_earth_alliance_eras():
    a = FleetEntry.create(101)
    b = FleetEntry.create(102)
    fleet = Fleet.create("Psi", "b5-acta-2e", "official", faction_id=18, fleet_list_id=21)
    fleet = fleet.replace_entries((a, b))
    profiles = {
        a.entry_id: profile(101, 3, "Earth Alliance - Third Age", "Raid"),
        b.entry_id: profile(102, 4, "Earth Alliance - Crusade Era", "Raid"),
    }
    messages = AlliedContingentRule().evaluate(RuleContext(fleet, profiles))
    assert any("more than one allied fleet list" in message.message for message in messages)


def test_unaffordable_wording_names_required_and_remaining_fap():
    text = format_unaffordable_choice("Raid", 5, {"Battle": 2}, "War")
    assert "requires 4 Raid Fleet Allocation Points" in text
    assert "Remaining fleet budget: 1 Raid Fleet Allocation Point" in text
