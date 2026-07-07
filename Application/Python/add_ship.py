from pathlib import Path
import sqlite3
import sys
import importlib


BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR.parent.parent / "Database" / "Data" / "dfs.db"


def get_id(cursor, table, id_column, name_column, name):
    cursor.execute(
        f"SELECT {id_column} FROM {table} WHERE {name_column} = ?;",
        (name,),
    )

    row = cursor.fetchone()

    if row is None:
        raise ValueError(f"Could not find {table}.{name_column}: {name}")

    return row[0]


def delete_existing_ship(cursor, ship_name):
    cursor.execute(
        "SELECT ship_id FROM ships WHERE ship_name = ?;",
        (ship_name,),
    )

    row = cursor.fetchone()

    if row is None:
        return

    ship_id = row[0]

    cursor.execute(
        "SELECT profile_id FROM acta_profiles WHERE ship_id = ?;",
        (ship_id,),
    )

    profile_ids = [r[0] for r in cursor.fetchall()]

    for profile_id in profile_ids:
        cursor.execute(
            "DELETE FROM weapons WHERE profile_id = ?;",
            (profile_id,),
        )

        cursor.execute(
            "DELETE FROM traits WHERE profile_id = ?;",
            (profile_id,),
        )

        cursor.execute(
            "DELETE FROM profile_fleet_lists WHERE profile_id = ?;",
            (profile_id,),
        )

    cursor.execute(
        "DELETE FROM acta_profiles WHERE ship_id = ?;",
        (ship_id,),
    )

    cursor.execute(
        "DELETE FROM ships WHERE ship_id = ?;",
        (ship_id,),
    )


def main():

    if len(sys.argv) != 2:
        print()
        print("Usage:")
        print("    python add_ship.py olympus")
        print("    python add_ship.py nova")
        print("    python add_ship.py marathon")
        print()
        return

    module_name = sys.argv[1].lower()

    try:
        ship_module = importlib.import_module(f"platform_data.{module_name}")
    except ModuleNotFoundError:
        print(f"Could not find platform_data/{module_name}.py")
        return

    SHIP_NAME = ship_module.SHIP_NAME
    SHIP_CLASS = ship_module.SHIP_CLASS
    FACTION_NAME = ship_module.FACTION_NAME
    PROFILES = ship_module.PROFILES

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    faction_id = get_id(
        cursor,
        "factions",
        "faction_id",
        "name",
        FACTION_NAME,
    )

    delete_existing_ship(cursor, SHIP_NAME)

    cursor.execute(
        """
        INSERT INTO ships (
            faction_id,
            ship_name,
            ship_class
        )
        VALUES (?, ?, ?);
        """,
        (
            faction_id,
            SHIP_NAME,
            SHIP_CLASS,
        ),
    )

    ship_id = cursor.lastrowid

    for profile in PROFILES:

        fleet_id = get_id(
            cursor,
            "fleet_lists",
            "fleet_list_id",
            "name",
            profile["fleet"],
        )

        cursor.execute(
            """
            INSERT INTO acta_profiles (
                ship_id,
                fleet_list_id,
                priority_level,
                speed,
                turn,
                hull,
                damage,
                crew,
                troops,
                craft,
                in_service
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """,
            (
                ship_id,
                fleet_id,
                profile["priority"],
                profile["speed"],
                profile["turn"],
                profile["hull"],
                profile["damage"],
                profile["crew"],
                profile["troops"],
                profile["craft"],
                profile["in_service"],
            ),
        )

        profile_id = cursor.lastrowid

        cursor.execute(
            """
            INSERT INTO profile_fleet_lists (
                profile_id,
                fleet_list_id,
                notes
            )
            VALUES (?, ?, ?);
            """,
            (
                profile_id,
                fleet_id,
                f"{SHIP_NAME} available in {profile['fleet']}",
            ),
        )

        for sort_order, trait in enumerate(profile["traits"], start=1):

            cursor.execute(
                """
                INSERT INTO traits (
                    profile_id,
                    trait,
                    sort_order
                )
                VALUES (?, ?, ?);
                """,
                (
                    profile_id,
                    trait,
                    sort_order,
                ),
            )

        for sort_order, weapon in enumerate(profile["weapons"], start=1):

            name, range_value, arc, attack_dice, traits = weapon

            cursor.execute(
                """
                INSERT INTO weapons (
                    profile_id,
                    name,
                    range_value,
                    arc,
                    attack_dice,
                    traits,
                    sort_order
                )
                VALUES (?, ?, ?, ?, ?, ?, ?);
                """,
                (
                    profile_id,
                    name,
                    range_value,
                    arc,
                    attack_dice,
                    traits,
                    sort_order,
                ),
            )

    conn.commit()
    conn.close()

    print()
    print(f"Added {SHIP_NAME}")
    print(f"Profiles imported: {len(PROFILES)}")
    print()


if __name__ == "__main__":
    main()