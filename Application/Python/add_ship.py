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


def delete_existing_ship(cursor, ship_name, faction_id):
    """Delete every existing copy of a platform for one faction only.

    Platform display names are not globally unique in DFS. Shared platforms
    such as Breaching Pods, Brivoki-class Advanced Warships, Halik-class
    Frigates, Sunhawk Battlecruisers, Warbird Cruisers, and Hurr Gunships may
    legitimately exist under more than one faction. Matching on both
    ship_name and faction_id prevents one faction's import from deleting
    another faction's platform.
    """
    cursor.execute(
        """
        SELECT ship_id
        FROM ships
        WHERE ship_name = ?
          AND faction_id = ?;
        """,
        (ship_name, faction_id),
    )

    ship_ids = [row[0] for row in cursor.fetchall()]

    for ship_id in ship_ids:
        cursor.execute(
            "SELECT profile_id FROM acta_profiles WHERE ship_id = ?;",
            (ship_id,),
        )

        profile_ids = [row[0] for row in cursor.fetchall()]

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


def ensure_profile_columns(cursor):
    """Add optional profile fields required by later official exceptions.

    Existing DFS databases predate the fixed Crew Quality field.  Keeping the
    migration here makes the importer safe for both existing and newly created
    databases.
    """
    cursor.execute("PRAGMA table_info(acta_profiles);")
    columns = {row[1] for row in cursor.fetchall()}

    if "initiative" not in columns:
        cursor.execute("ALTER TABLE acta_profiles ADD COLUMN initiative TEXT;")

    if "crew_quality" not in columns:
        cursor.execute("ALTER TABLE acta_profiles ADD COLUMN crew_quality TEXT;")


def format_notes(notes):
    if not notes:
        return None

    cleaned_notes = [str(note).strip() for note in notes if str(note).strip()]

    if not cleaned_notes:
        return None

    return "\n".join(cleaned_notes)


def main():
    if len(sys.argv) != 2:
        print()
        print("Usage:")
        print("    python add_ship.py hyperion")
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

    ship_name = ship_module.SHIP_NAME
    ship_class = ship_module.SHIP_CLASS
    file_name = getattr(ship_module, "FILE_NAME", ship_name)
    faction_name = ship_module.FACTION_NAME
    profiles = ship_module.PROFILES
    legacy_ship_names = getattr(ship_module, "LEGACY_SHIP_NAMES", [])

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    ensure_profile_columns(cursor)

    faction_id = get_id(
        cursor,
        "factions",
        "faction_id",
        "name",
        faction_name,
    )

    for legacy_name in legacy_ship_names:
        delete_existing_ship(cursor, legacy_name, faction_id)

    delete_existing_ship(cursor, ship_name, faction_id)

    cursor.execute(
        """
        INSERT INTO ships (
            faction_id,
            ship_name,
            ship_class,
            file_name
        )
        VALUES (?, ?, ?, ?);
        """,
        (
            faction_id,
            ship_name,
            ship_class,
            file_name,
        ),
    )

    ship_id = cursor.lastrowid

    for profile in profiles:
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
                crew_quality,
                troops,
                craft,
                initiative,
                in_service,
                notes
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
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
                profile.get("crew_quality"),
                profile["troops"],
                profile["craft"],
                profile.get("initiative"),
                profile["in_service"],
                format_notes(profile.get("notes", [])),
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
                f"{ship_name} available in {profile['fleet']}",
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
    print(f"Added {ship_name}")
    print(f"Profiles imported: {len(profiles)}")
    print()


if __name__ == "__main__":
    main()
