import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parents[2] / "Database" / "Data" / "dfs.db"


def get_ship(cur, ship_name):
    cur.execute("""
        SELECT
            ap.profile_id,
            s.ship_name,
            s.ship_class,
            f.name AS faction,
            fl.name AS fleet,
            ap.priority_level,
            ap.speed,
            ap.turn,
            ap.hull,
            ap.damage,
            ap.crew,
            ap.troops,
            ap.craft,
            ap.initiative,
            ap.in_service
        FROM ships s
        JOIN factions f ON s.faction_id = f.faction_id
        JOIN acta_profiles ap ON s.ship_id = ap.ship_id
        JOIN fleet_lists fl ON ap.fleet_list_id = fl.fleet_list_id
        WHERE s.ship_name = ?;
    """, (ship_name,))
    return cur.fetchone()


def get_traits(cur, profile_id):
    cur.execute("""
        SELECT trait
        FROM traits
        WHERE profile_id = ?
        ORDER BY sort_order;
    """, (profile_id,))
    return cur.fetchall()


def get_weapons(cur, profile_id):
    cur.execute("""
        SELECT name, range_value, arc, attack_dice, traits
        FROM weapons
        WHERE profile_id = ?
        ORDER BY sort_order;
    """, (profile_id,))
    return cur.fetchall()


def print_ship_card(ship, traits, weapons):
    print("=" * 72)
    print(f"{ship['ship_name']} ({ship['ship_class']})".upper())
    print(f"Priority: {ship['priority_level']}")
    print("=" * 72)

    print(f"Faction: {ship['faction']}")
    print(f"Fleet: {ship['fleet']}")
    print()
    print(f"Speed: {ship['speed']}     Turn: {ship['turn']}     Hull: {ship['hull']}")
    print(f"Damage: {ship['damage']}   Crew: {ship['crew']}   Troops: {ship['troops']}")
    print(f"Craft: {ship['craft']}")
    print(f"Initiative: {ship['initiative']}   In Service: {ship['in_service']}")
    print()

    print("Traits:")
    print(", ".join(row["trait"] for row in traits))
    print()

    print("Weapons:")
    print(f"{'Weapon':<24} {'Range':<6} {'Arc':<6} {'AD':<4} Special")
    print("-" * 72)

    for w in weapons:
        print(
            f"{w['name']:<24} "
            f"{w['range_value']:<6} "
            f"{w['arc']:<6} "
            f"{w['attack_dice']:<4} "
            f"{w['traits']}"
        )


def main():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    ship = get_ship(cur, "Omega Destroyer")

    if ship is None:
        print("Ship not found.")
        return

    traits = get_traits(cur, ship["profile_id"])
    weapons = get_weapons(cur, ship["profile_id"])

    print_ship_card(ship, traits, weapons)

    conn.close()


if __name__ == "__main__":
    main()