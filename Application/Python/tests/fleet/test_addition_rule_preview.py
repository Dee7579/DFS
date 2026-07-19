from dataclasses import replace

from dfs.domain.catalog import PlatformProfile
from dfs.domain.fleet import Fleet, FleetEntry
from dfs.services.fleet.construction_service import FleetConstructionService


class Repo:
    def __init__(self, profile): self.profile = profile
    def get_profile_by_id(self, profile_id): return self.profile if profile_id == self.profile.profile_id else None


def test_preview_reports_new_unique_platform_failure_only():
    profile = PlatformProfile(7, 19, "The Ancients", "+4", "Ancient", "10", "1/45", "6", "100/20", "100/20", "0", "", "-2261", "Fleet Lists")
    service = FleetConstructionService(Repo(profile))
    fleet = Fleet.create("Test", "b5_acta", "b5_acta_priority_standard", fleet_list_id=19)
    fleet = replace(fleet, entries=(FleetEntry.create(7),), metadata={"scenario_priority":"Armageddon","fleet_allocation_points":10})
    messages = service.preview_add_profile_rules(fleet, 7)
    assert [message.rule_id for message in messages] == ["B5-ANCIENT-UNQ-001"]
