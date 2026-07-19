from dataclasses import dataclass

from dfs.domain.fleet import Fleet, FleetEntry
from dfs.services.fleet.print_planner import FleetPrintPlanner


@dataclass(frozen=True)
class Profile:
    profile_id: int
    fleet_list_id: int
    fleet_name: str
    traits: tuple[str, ...]
    craft: str = ""


@dataclass(frozen=True)
class Detail:
    ship_id: int
    name: str
    file_name: str
    faction_name: str
    profiles: tuple[Profile, ...]


class Details:
    def __init__(self, profiles, detail_by_profile):
        self.profiles = profiles
        self.detail_by_profile = detail_by_profile
    def get_profile(self, profile_id):
        return self.profiles.get(profile_id)
    def get(self, ship_id):
        return next((d for d in self.detail_by_profile.values() if d.ship_id == ship_id), None)


class Summary:
    def __init__(self, ship_id, name):
        self.ship_id = ship_id
        self.name = name


class Catalog:
    def __init__(self, details):
        self.details = details
    def search(self, filters):
        seen = set()
        result = []
        for detail in self.details.values():
            if detail.ship_id not in seen:
                seen.add(detail.ship_id)
                result.append(Summary(detail.ship_id, detail.name))
        return result


def test_fighter_sheets_are_deduplicated_across_purchased_and_included_craft():
    ship = Profile(1, 9, "Fleet", (), "2 Aurora Fighter Flights")
    fighter = Profile(2, 9, "Fleet", ("Fighter",), "")
    ship_detail = Detail(10, "Carrier", "Carrier", "Faction", (ship,))
    fighter_detail = Detail(20, "Aurora Fighter Flight", "Aurora", "Faction", (fighter,))
    details = {1: ship_detail, 2: fighter_detail}
    planner = FleetPrintPlanner(Catalog(details), Details({1: ship, 2: fighter}, details))
    fleet = Fleet.create("Test", "b5_acta", "none", faction_id=1, fleet_list_id=9)
    fleet = fleet.replace_entries((FleetEntry.create(1, 2), FleetEntry.create(2, 3)))

    items = planner.plan(fleet)
    craft = [item for item in items if item.kind == "craft"]

    assert len(craft) == 1
    assert craft[0].profile_id == 2
    assert craft[0].quantity_represented == 7
    assert craft[0].copies == 1


def test_ship_entries_remain_individual_print_items():
    ship = Profile(1, 9, "Fleet", (), "")
    detail = Detail(10, "Cruiser", "Cruiser", "Faction", (ship,))
    details = {1: detail}
    planner = FleetPrintPlanner(Catalog(details), Details({1: ship}, details))
    fleet = Fleet.create("Test", "b5_acta", "none", faction_id=1, fleet_list_id=9)
    fleet = fleet.replace_entries((FleetEntry.create(1, 1, vessel_name="Alpha"), FleetEntry.create(1, 1, vessel_name="Beta")))

    ships = [item for item in planner.plan(fleet) if item.kind == "ship"]
    assert [item.vessel_name for item in ships] == ["Alpha", "Beta"]
