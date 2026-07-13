from dfs.domain.catalog import WeaponDetail
from dfs.domain.weapon_order import order_weapons


def weapon(name: str, arc: str, sort_order: int) -> WeaponDetail:
    return WeaponDetail(name, "", arc, "", "", sort_order)


def test_canonical_arc_order_and_source_order_inside_arc() -> None:
    unordered = (
        weapon("A second", "A", 7),
        weapon("F second", "F", 3),
        weapon("Boresight aft", "B(a)", 9),
        weapon("Port", "P", 4),
        weapon("F first", "F", 1),
        weapon("Boresight", "B", 2),
        weapon("Starboard", "S", 5),
        weapon("A first", "A", 6),
        weapon("Turret", "T", 10),
    )

    assert [item.name for item in order_weapons(unordered)] == [
        "Boresight",
        "F first",
        "F second",
        "Port",
        "Starboard",
        "A first",
        "A second",
        "Boresight aft",
        "Turret",
    ]


def test_boresight_aft_spacing_is_normalized() -> None:
    unordered = (weapon("Aft bore", "B (a)", 1), weapon("Turret", "T", 1))
    assert [item.name for item in order_weapons(unordered)] == ["Aft bore", "Turret"]
