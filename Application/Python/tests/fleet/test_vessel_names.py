from dfs.domain.fleet import Fleet, FleetEntry
from dfs.services.fleet import FleetConstructionService


class _UnusedRepository:
    pass


def test_naming_grouped_entry_splits_one_vessel_from_group():
    service = FleetConstructionService(_UnusedRepository())
    fleet = Fleet.create("Test", "b5_acta", "b5_acta_priority_standard")
    entry = FleetEntry.create(12, quantity=3)
    fleet = fleet.add_entry(entry)

    updated = service.set_vessel_name(fleet, entry.entry_id, "Excalibur")

    assert len(updated.entries) == 2
    assert updated.entries[0].quantity == 1
    assert updated.entries[0].vessel_name == "Excalibur"
    assert updated.entries[1].quantity == 2
    assert updated.entries[1].vessel_name == ""


def test_clearing_name_keeps_single_entry():
    service = FleetConstructionService(_UnusedRepository())
    fleet = Fleet.create("Test", "b5_acta", "b5_acta_priority_standard")
    entry = FleetEntry.create(12, vessel_name="Excalibur")
    fleet = fleet.add_entry(entry)

    updated = service.set_vessel_name(fleet, entry.entry_id, "")

    assert len(updated.entries) == 1
    assert updated.entries[0].vessel_name == ""
