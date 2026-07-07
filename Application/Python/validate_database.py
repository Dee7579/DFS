from pathlib import Path
import sqlite3


BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR.parent.parent / "Database" / "Data" / "dfs.db"


def count(cursor, table):
    cursor.execute(f"SELECT COUNT(*) FROM {table};")
    return cursor.fetchone()[0]


def check(cursor, label, sql):
    cursor.execute(sql)
    problems = cursor.fetchall()

    if problems:
        print(f"FAIL  {label}: {len(problems)} problem(s)")
        return False

    print(f"PASS  {label}")
    return True


def main():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    print("=====================================")
    print("DFS DATABASE VALIDATION")
    print("=====================================")
    print()
    print(f"Ships.........................{count(cursor, 'ships')}")
    print(f"Profiles......................{count(cursor, 'acta_profiles')}")
    print(f"Weapons.......................{count(cursor, 'weapons')}")
    print(f"Traits........................{count(cursor, 'traits')}")
    print(f"Fleet memberships.............{count(cursor, 'profile_fleet_lists')}")
    print()

    checks = [
        (
            "Every ship has at least one profile",
            """
            SELECT s.ship_id
            FROM ships s
            LEFT JOIN acta_profiles ap ON s.ship_id = ap.ship_id
            WHERE ap.profile_id IS NULL;
            """,
        ),
        (
            "Every profile has at least one weapon",
            """
            SELECT ap.profile_id
            FROM acta_profiles ap
            LEFT JOIN weapons w ON ap.profile_id = w.profile_id
            WHERE w.weapon_id IS NULL;
            """,
        ),
        (
            "Every profile belongs to at least one fleet list",
            """
            SELECT ap.profile_id
            FROM acta_profiles ap
            LEFT JOIN profile_fleet_lists pfl ON ap.profile_id = pfl.profile_id
            WHERE pfl.profile_fleet_list_id IS NULL;
            """,
        ),
        (
            "No orphan weapons",
            """
            SELECT w.weapon_id
            FROM weapons w
            LEFT JOIN acta_profiles ap ON w.profile_id = ap.profile_id
            WHERE ap.profile_id IS NULL;
            """,
        ),
        (
            "No orphan traits",
            """
            SELECT t.trait_id
            FROM traits t
            LEFT JOIN acta_profiles ap ON t.profile_id = ap.profile_id
            WHERE ap.profile_id IS NULL;
            """,
        ),
        (
            "No orphan fleet memberships",
            """
            SELECT pfl.profile_fleet_list_id
            FROM profile_fleet_lists pfl
            LEFT JOIN acta_profiles ap ON pfl.profile_id = ap.profile_id
            LEFT JOIN fleet_lists fl ON pfl.fleet_list_id = fl.fleet_list_id
            WHERE ap.profile_id IS NULL
               OR fl.fleet_list_id IS NULL;
            """,
        ),
        (
            "No duplicate profile/fleet memberships",
            """
            SELECT profile_id, fleet_list_id
            FROM profile_fleet_lists
            GROUP BY profile_id, fleet_list_id
            HAVING COUNT(*) > 1;
            """,
        ),
    ]

    print("Checks")
    print("-------------------------------------")

    passed = True

    for label, sql in checks:
        if not check(cursor, label, sql):
            passed = False

    print()
    print("=====================================")

    if passed:
        print("Validation PASSED")
    else:
        print("Validation FAILED")

    print("=====================================")

    conn.close()


if __name__ == "__main__":
    main()