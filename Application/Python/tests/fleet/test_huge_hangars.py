from dfs.domain.fleet.huge_hangars import (
    capacity_from_traits, embarked_profile_ids, with_embarked_profile_ids,
)


def test_capacity_is_read_from_trait():
    assert capacity_from_traits(("Carrier 4", "Huge Hangars 12", "Lumbering")) == 12
    assert capacity_from_traits(("Carrier 2",)) == 0


def test_embarked_ships_are_persisted_as_individual_instances():
    options = with_embarked_profile_ids({}, (11, 11, 22))
    assert embarked_profile_ids(options) == (11, 11, 22)
    assert options["huge_hangars"]["profile_ids"] == [11, 11, 22]
