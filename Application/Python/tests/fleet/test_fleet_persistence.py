from dfs.domain.fleet import FleetEntry
from dfs.infrastructure.fleet import JSONFleetStore


def test_fleet_json_round_trip(tmp_path):
    from dfs.domain.fleet import Fleet

    fleet = Fleet.create(
        "Third Age Test",
        "b5_acta",
        "b5_acta_priority_standard",
        faction_id=1,
        fleet_list_id=3,
        selected_year=2259,
    ).add_entry(FleetEntry.create(6325, quantity=2))

    store = JSONFleetStore()
    path = store.save(fleet, tmp_path / "third_age.dfs-fleet.json")
    loaded = store.load(path)

    assert loaded == fleet


def test_fleet_json_round_trip_preserves_vessel_name(tmp_path):
    from dfs.domain.fleet import Fleet

    fleet = Fleet.create(
        "Named Fleet",
        "b5_acta",
        "b5_acta_priority_standard",
    ).add_entry(FleetEntry.create(42, vessel_name="Excalibur"))

    store = JSONFleetStore()
    path = store.save(fleet, tmp_path / "named.dfs-fleet.json")
    loaded = store.load(path)

    assert loaded.entries[0].vessel_name == "Excalibur"
