from dfs.domain.fleet import Fleet, FleetEntry
from dfs.services.fleet import FleetConstructionService


class _UnusedRepository:
    pass


def _fleet_with_three_entries():
    fleet = Fleet.create("Order Test", "b5_acta", "b5_acta_priority_standard")
    first = FleetEntry.create(101)
    second = FleetEntry.create(102)
    third = FleetEntry.create(103)
    return fleet.replace_entries((first, second, third)), first, second, third


def test_move_entry_before_another_entry():
    service = FleetConstructionService(_UnusedRepository())
    fleet, first, second, third = _fleet_with_three_entries()

    moved = service.move_entry(fleet, third.entry_id, first.entry_id, before=True)

    assert [entry.profile_id for entry in moved.entries] == [103, 101, 102]


def test_move_entry_to_end():
    service = FleetConstructionService(_UnusedRepository())
    fleet, first, second, third = _fleet_with_three_entries()

    moved = service.move_entry(fleet, first.entry_id)

    assert [entry.profile_id for entry in moved.entries] == [102, 103, 101]


def test_reorder_entries_requires_complete_unique_order():
    service = FleetConstructionService(_UnusedRepository())
    fleet, first, second, third = _fleet_with_three_entries()

    reordered = service.reorder_entries(
        fleet, (second.entry_id, first.entry_id, third.entry_id)
    )
    assert [entry.profile_id for entry in reordered.entries] == [102, 101, 103]

    try:
        service.reorder_entries(fleet, (first.entry_id, second.entry_id))
    except ValueError:
        pass
    else:
        raise AssertionError("Incomplete ordering should be rejected")
