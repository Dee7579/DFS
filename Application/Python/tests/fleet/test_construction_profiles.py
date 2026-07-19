from dfs.domain.catalog import PlatformProfile
from dataclasses import replace

from dfs.domain.fleet.models import Fleet, FleetEntry, ValidationSeverity
from dfs.services.fleet.b5_acta_profile import (
    B5ACTAAdvisoryPriorityProfile,
    B5ACTASandboxProfile,
    B5ACTAStandardPriorityProfile,
)


def profile(priority: str = "War", fleet_list_id: int = 10) -> PlatformProfile:
    return PlatformProfile(
        profile_id=1,
        fleet_list_id=fleet_list_id,
        fleet_name="Test Fleet",
        initiative="+0",
        priority_level=priority,
        speed="8",
        turn="1/45",
        hull="5",
        damage="20/5",
        crew="20/5",
        troops="1",
        craft="",
        in_service="2250+",
        source_book="Fleet Lists",
    )


def fleet(profile_id: str) -> Fleet:
    value = Fleet.create(
        "Test",
        "b5_acta",
        profile_id,
        faction_id=1,
        fleet_list_id=10,
        selected_year=2259,
    )
    return value.add_entry(FleetEntry.create(1))


def test_advisory_demotes_official_errors_to_warnings():
    value = fleet("b5_acta_priority_advisory")
    value = replace(value, metadata={"scenario_priority": "Patrol", "fleet_allocation_points": 1})
    resolved = {value.entries[0].entry_id: profile("War")}
    official = B5ACTAStandardPriorityProfile().validate(value, resolved)
    advisory = B5ACTAAdvisoryPriorityProfile().validate(value, resolved)
    assert official.errors
    assert not advisory.errors
    assert advisory.warnings
    assert all(message.severity is not ValidationSeverity.ERROR for message in advisory.messages)


def test_sandbox_never_invalidates_and_reports_rules_disabled():
    value = fleet("b5_acta_sandbox")
    resolved = {value.entries[0].entry_id: profile("Ancient", fleet_list_id=999)}
    summary = B5ACTASandboxProfile().summarize(value, resolved)
    assert summary.validation.is_valid
    assert summary.budget_label == "Rules disabled"
    assert "Any platform combination" in summary.remaining_label
