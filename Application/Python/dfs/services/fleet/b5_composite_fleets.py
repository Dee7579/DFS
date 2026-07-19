"""Idempotent database seed for the two official Babylon 5 composite fleets."""
from __future__ import annotations

import re
import sqlite3
from pathlib import Path

LEAGUE_FACTION = "League of Non-Aligned Worlds"
LEAGUE_FLEET = "Allied League of Non-Aligned Worlds"
ARMY_FACTION = "Army of Light"
ARMY_FLEET = "Army of Light"
SOURCE_MARKER = "DFS_SOURCE_FLEET_ID="

SOURCE_FLEET_NAMES = {
    3: "Earth Alliance - Third Age",
    5: "Minbari Federation",
    8: "Narn Regime",
    10: "Interstellar Alliance",
    11: "Abbai Matriarchy",
    12: "Brakiri Syndicracy",
    13: "Drazi Freehold",
    14: "Gaim Intelligence",
    15: "pak'ma'ra",
    16: "Vree Conglomerate",
    17: "Raiders",
}

LEAGUE_SOURCE_FLEETS = (11, 12, 13, 14, 15, 16, 17)
ARMY_SOURCE_FLEETS = (3, 5, 8, 10, 11, 12, 13, 14, 15, 16)

# P&P p. 10: named hulls and all variants of those hulls.
ARMY_ALLOWED_STEMS = {
    3: ("Aurora Starfury", "Hyperion-class", "Nova-class", "Olympus-class", "Omega-class", "Thunderbolt Starfury"),
    5: ("Flyer", "Nial", "Sharlin-class", "(Sharlin Variant)"),
    8: ("Frazi", "G’Quan", "G'Quan", "T’Loth", "T'Loth"),
    11: ("Bimith-class",),
    12: ("Avioki-class", "(Avioki Variant)"),
    13: ("Breaching Pod", "Sky Serpent", "Sunhawk-class", "(Sunhawk Variant)", "Warbird-class", "(Warbird Variant)"),
    14: ("Sataaka-class",),
    15: ("Halik-class", "(Halik Variant)", "(Halik variant)"),
    16: ("Xill-class", "(Xill Variant)", "Xorr-class", "(Xorr Variant)"),
}

ARMY_EXACT_NAMES = {
    10: {
        "Aurora Starfury Flight", "Flyer Flight", "Nial Heavy Fighter Flight",
        "Thunderbolt Starfury Flight", "White Star", "White Star II",
    },
    14: {"Klikkita Light Fighter"},
}


def _army_name_allowed(source_fleet: int, ship_name: str) -> bool:
    if ship_name in ARMY_EXACT_NAMES.get(source_fleet, set()):
        return True
    return any(stem.casefold() in ship_name.casefold() for stem in ARMY_ALLOWED_STEMS.get(source_fleet, ()))


def source_fleet_id(source_book: str) -> int | None:
    match = re.search(r"DFS_SOURCE_FLEET_ID=(\d+)", source_book or "")
    return int(match.group(1)) if match else None


def source_fleet_name(source_book: str, fallback: str = "") -> str:
    """Return the published component fleet for a copied composite profile."""
    fleet_id = source_fleet_id(source_book)
    return SOURCE_FLEET_NAMES.get(fleet_id, fallback)


def _available_in_2259(value: str | None) -> bool:
    text = (value or "").strip().casefold()
    if text in {"", "all"}:
        return True
    years = [int(item) for item in re.findall(r"\d{4}", text)]
    if not years:
        return True
    if "+" in text:
        return years[0] <= 2259
    if len(years) >= 2:
        return years[0] <= 2259 <= years[1]
    return years[0] <= 2259


def _ensure_faction_and_fleet(connection: sqlite3.Connection, faction: str, fleet: str, initiative: str) -> int:
    connection.execute("INSERT OR IGNORE INTO factions(name) VALUES (?)", (faction,))
    faction_id = connection.execute("SELECT faction_id FROM factions WHERE name = ?", (faction,)).fetchone()[0]
    row = connection.execute("SELECT fleet_list_id FROM fleet_lists WHERE name = ?", (fleet,)).fetchone()
    if row:
        return int(row[0])
    cursor = connection.execute(
        "INSERT INTO fleet_lists(faction_id, name, year_range, initiative) VALUES (?, ?, ?, ?)",
        (faction_id, fleet, None, initiative),
    )
    return int(cursor.lastrowid)


def _copy_profile(connection: sqlite3.Connection, source_profile_id: int, target_fleet_id: int, source_fleet_id_value: int) -> None:
    exists = connection.execute(
        "SELECT 1 FROM acta_profiles WHERE fleet_list_id = ? AND source_book LIKE ?",
        (target_fleet_id, f"%DFS_SOURCE_PROFILE_ID={source_profile_id}%"),
    ).fetchone()
    if exists:
        return
    source = connection.execute("SELECT * FROM acta_profiles WHERE profile_id = ?", (source_profile_id,)).fetchone()
    if source is None:
        return
    source_book = str(source["source_book"] or "").strip()
    marker = f"DFS_SOURCE_PROFILE_ID={source_profile_id}; {SOURCE_MARKER}{source_fleet_id_value}"
    source_book = f"{source_book} | {marker}" if source_book else marker
    cursor = connection.execute(
        """INSERT INTO acta_profiles(
            ship_id, fleet_list_id, priority_level, speed, turn, hull, damage, crew,
            troops, craft, initiative, in_service, source_book, notes
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (source["ship_id"], target_fleet_id, source["priority_level"], source["speed"], source["turn"],
         source["hull"], source["damage"], source["crew"], source["troops"], source["craft"],
         source["initiative"], source["in_service"], source_book, source["notes"]),
    )
    new_id = int(cursor.lastrowid)
    connection.execute(
        "INSERT INTO traits(profile_id, trait, sort_order) SELECT ?, trait, sort_order FROM traits WHERE profile_id = ?",
        (new_id, source_profile_id),
    )
    connection.execute(
        """INSERT INTO weapons(profile_id, name, range_value, arc, attack_dice, traits, sort_order)
           SELECT ?, name, range_value, arc, attack_dice, traits, sort_order FROM weapons WHERE profile_id = ?""",
        (new_id, source_profile_id),
    )


def ensure_b5_composite_fleets(database_path: str | Path) -> None:
    connection = sqlite3.connect(str(database_path))
    connection.row_factory = sqlite3.Row
    try:
        league_id = _ensure_faction_and_fleet(connection, LEAGUE_FACTION, LEAGUE_FLEET, "+0")
        army_id = _ensure_faction_and_fleet(connection, ARMY_FACTION, ARMY_FLEET, "+0")

        for row in connection.execute(
            "SELECT ap.profile_id, ap.fleet_list_id, ap.in_service FROM acta_profiles ap WHERE ap.fleet_list_id IN (11,12,13,14,15,16,17)"
        ):
            if _available_in_2259(row["in_service"]):
                _copy_profile(connection, int(row["profile_id"]), league_id, int(row["fleet_list_id"]))

        for source_fleet in ARMY_SOURCE_FLEETS:
            for row in connection.execute(
                """SELECT ap.profile_id, s.ship_name FROM acta_profiles ap
                   JOIN ships s ON s.ship_id = ap.ship_id WHERE ap.fleet_list_id = ?""",
                (source_fleet,),
            ):
                if _army_name_allowed(source_fleet, str(row["ship_name"])):
                    _copy_profile(connection, int(row["profile_id"]), army_id, source_fleet)
        connection.commit()
    finally:
        connection.close()
