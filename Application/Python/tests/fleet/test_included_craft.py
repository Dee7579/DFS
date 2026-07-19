from dfs.domain.fleet.included_craft import normalize_craft_name, parse_included_craft


def test_parses_single_included_craft_group():
    assert parse_included_craft("8 White Star Fighters")[0].quantity == 8
    assert parse_included_craft("8 White Star Fighters")[0].printed_name == "White Star Fighters"


def test_parses_multiple_groups():
    groups = parse_included_craft("2 Aurora Starfury Flights, 1 Breaching Pod")
    assert [(group.quantity, group.printed_name) for group in groups] == [
        (2, "Aurora Starfury Flights"),
        (1, "Breaching Pod"),
    ]


def test_ignores_empty_craft_fields():
    assert parse_included_craft("None") == ()
    assert parse_included_craft("-") == ()


def test_normalizes_fighter_plural_and_flight_suffix():
    assert normalize_craft_name("White Star Fighters") == "white star fighter"
    assert normalize_craft_name("White Star Fighter Flight") == "white star fighter"
