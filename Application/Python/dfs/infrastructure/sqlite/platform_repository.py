"""SQLite implementation of the read-only DFS platform repository."""

from __future__ import annotations

from collections import defaultdict
from typing import Any

from dfs.domain.catalog import (
    FilterOption,
    PlatformDetail,
    PlatformFilter,
    PlatformProfile,
    PlatformSummary,
    WeaponDetail,
)
from dfs.infrastructure.sqlite.connection import SQLiteConnectionFactory
from dfs.domain.weapon_order import order_weapons


class SQLitePlatformRepository:
    GENERATED_PROFILE_MARKER = "DFS_SOURCE_PROFILE_ID="

    def __init__(self, connections: SQLiteConnectionFactory):
        self._connections = connections

    @staticmethod
    def _placeholders(values: tuple[Any, ...]) -> str:
        return ", ".join("?" for _ in values)

    def _filter_sql(self, filters: PlatformFilter) -> tuple[str, list[Any]]:
        clauses: list[str] = []
        params: list[Any] = []

        text = filters.search_text.strip()
        if text:
            clauses.append("(s.ship_name LIKE ? COLLATE NOCASE OR s.ship_class LIKE ? COLLATE NOCASE)")
            token = f"%{text}%"
            params.extend((token, token))

        if filters.faction_ids:
            marks = self._placeholders(filters.faction_ids)
            clauses.append(
                f"(s.faction_id IN ({marks}) OR EXISTS ("
                "SELECT 1 FROM acta_profiles apx JOIN fleet_lists flx ON flx.fleet_list_id = apx.fleet_list_id "
                f"WHERE apx.ship_id = s.ship_id AND flx.faction_id IN ({marks})))"
            )
            params.extend(filters.faction_ids)
            params.extend(filters.faction_ids)

        if filters.fleet_list_ids:
            clauses.append(
                "EXISTS (SELECT 1 FROM acta_profiles apf "
                f"WHERE apf.ship_id = s.ship_id AND apf.fleet_list_id IN ({self._placeholders(filters.fleet_list_ids)}))"
            )
            params.extend(filters.fleet_list_ids)

        if filters.priority_levels:
            clauses.append(
                "EXISTS (SELECT 1 FROM acta_profiles app "
                f"WHERE app.ship_id = s.ship_id AND app.priority_level IN ({self._placeholders(filters.priority_levels)}))"
            )
            params.extend(filters.priority_levels)

        for trait in filters.traits:
            clauses.append(
                "EXISTS (SELECT 1 FROM acta_profiles apt "
                "JOIN traits t ON t.profile_id = apt.profile_id "
                "WHERE apt.ship_id = s.ship_id AND t.trait = ? COLLATE NOCASE)"
            )
            params.append(trait)

        for weapon in filters.weapons:
            clauses.append(
                "EXISTS (SELECT 1 FROM acta_profiles apw "
                "JOIN weapons w ON w.profile_id = apw.profile_id "
                "WHERE apw.ship_id = s.ship_id AND w.name = ? COLLATE NOCASE)"
            )
            params.append(weapon)

        if filters.available_year is not None:
            clauses.append(
                "EXISTS (SELECT 1 FROM acta_profiles apy "
                "WHERE apy.ship_id = s.ship_id "
                "AND dfs_year_available(apy.in_service, ?) = 1)"
            )
            params.append(filters.available_year)

        return (" AND ".join(clauses) if clauses else "1 = 1"), params

    def search(self, filters: PlatformFilter) -> list[PlatformSummary]:
        where_sql, params = self._filter_sql(filters)
        sql = f"""
            SELECT
                s.ship_id,
                s.ship_name,
                COALESCE(s.ship_class, '') AS ship_class,
                f.faction_id,
                f.name AS faction_name,
                COUNT(DISTINCT ap.profile_id) AS profile_count,
                GROUP_CONCAT(DISTINCT fl.name) AS fleet_names,
                GROUP_CONCAT(DISTINCT ap.priority_level) AS priorities,
                GROUP_CONCAT(DISTINCT ap.in_service) AS in_service_values
            FROM ships s
            JOIN factions f ON f.faction_id = s.faction_id
            LEFT JOIN acta_profiles ap ON ap.ship_id = s.ship_id
            LEFT JOIN fleet_lists fl ON fl.fleet_list_id = ap.fleet_list_id
            WHERE {where_sql}
            GROUP BY s.ship_id, s.ship_name, s.ship_class, f.faction_id, f.name
            ORDER BY f.name COLLATE NOCASE, s.ship_name COLLATE NOCASE
            LIMIT ? OFFSET ?
        """
        params.extend((max(1, min(filters.limit, 1000)), max(0, filters.offset)))

        with self._connections.connect() as connection:
            rows = connection.execute(sql, params).fetchall()

        return [
            PlatformSummary(
                ship_id=row["ship_id"],
                name=row["ship_name"],
                ship_class=row["ship_class"],
                faction_id=row["faction_id"],
                faction_name=row["faction_name"],
                profile_count=row["profile_count"],
                fleet_names=tuple(sorted(filter(None, (row["fleet_names"] or "").split(",")))),
                priority_levels=tuple(sorted(filter(None, (row["priorities"] or "").split(",")))),
                in_service_values=tuple(sorted(filter(None, (row["in_service_values"] or "").split(",")))),
            )
            for row in rows
        ]

    def count(self, filters: PlatformFilter) -> int:
        where_sql, params = self._filter_sql(filters)
        with self._connections.connect() as connection:
            row = connection.execute(
                f"SELECT COUNT(*) AS total FROM ships s WHERE {where_sql}", params
            ).fetchone()
        return int(row["total"])

    def count_profiles(self, include_generated: bool = False) -> int:
        sql = "SELECT COUNT(*) AS total FROM acta_profiles"
        params: tuple[Any, ...] = ()
        if not include_generated:
            sql += " WHERE COALESCE(source_book, '') NOT LIKE ?"
            params = (f"%{self.GENERATED_PROFILE_MARKER}%",)
        with self._connections.connect() as connection:
            row = connection.execute(sql, params).fetchone()
        return int(row["total"])

    def get_by_id(self, ship_id: int) -> PlatformDetail | None:
        with self._connections.connect() as connection:
            ship_row = connection.execute(
                """
                SELECT s.ship_id, s.ship_name, COALESCE(s.ship_class, '') AS ship_class,
                       COALESCE(s.file_name, '') AS file_name,
                       f.faction_id, f.name AS faction_name
                FROM ships s
                JOIN factions f ON f.faction_id = s.faction_id
                WHERE s.ship_id = ?
                """,
                (ship_id,),
            ).fetchone()
            if ship_row is None:
                return None

            profile_rows = connection.execute(
                """
                SELECT ap.*, fl.name AS fleet_name, COALESCE(fl.initiative, '') AS fleet_initiative
                FROM acta_profiles ap
                JOIN fleet_lists fl ON fl.fleet_list_id = ap.fleet_list_id
                WHERE ap.ship_id = ?
                ORDER BY fl.name COLLATE NOCASE, ap.profile_id
                """,
                (ship_id,),
            ).fetchall()
            profile_ids = tuple(row["profile_id"] for row in profile_rows)

            traits_by_profile: dict[int, list[str]] = defaultdict(list)
            weapons_by_profile: dict[int, list[WeaponDetail]] = defaultdict(list)
            if profile_ids:
                marks = self._placeholders(profile_ids)
                for row in connection.execute(
                    f"SELECT profile_id, trait FROM traits WHERE profile_id IN ({marks}) ORDER BY profile_id, sort_order, trait",
                    profile_ids,
                ):
                    traits_by_profile[row["profile_id"]].append(row["trait"])

                for row in connection.execute(
                    f"""
                    SELECT profile_id, name, COALESCE(range_value, '') AS range_value,
                           COALESCE(arc, '') AS arc, COALESCE(attack_dice, '') AS attack_dice,
                           COALESCE(traits, '') AS traits, COALESCE(sort_order, 0) AS sort_order
                    FROM weapons
                    WHERE profile_id IN ({marks})
                    ORDER BY profile_id, sort_order, weapon_id
                    """,
                    profile_ids,
                ):
                    weapons_by_profile[row["profile_id"]].append(
                        WeaponDetail(
                            name=row["name"], range_value=row["range_value"], arc=row["arc"],
                            attack_dice=str(row["attack_dice"]), traits=row["traits"], sort_order=row["sort_order"]
                        )
                    )

        profiles = tuple(
            PlatformProfile(
                profile_id=row["profile_id"],
                fleet_list_id=row["fleet_list_id"],
                fleet_name=row["fleet_name"],
                initiative=str(row["initiative"] or row["fleet_initiative"] or ""),
                priority_level=str(row["priority_level"] or ""),
                speed=str(row["speed"] if row["speed"] is not None else ""),
                turn=str(row["turn"] or ""),
                hull=str(row["hull"] if row["hull"] is not None else ""),
                damage=str(row["damage"] or ""), crew=str(row["crew"] or ""),
                troops=str(row["troops"] or ""), craft=str(row["craft"] or ""),
                in_service=str(row["in_service"] or ""), source_book=str(row["source_book"] or ""),
                crew_quality=str(row["crew_quality"] or ""),
                notes=tuple(line.strip() for line in str(row["notes"] or "").splitlines() if line.strip()),
                traits=tuple(traits_by_profile[row["profile_id"]]),
                weapons=order_weapons(weapons_by_profile[row["profile_id"]]),
            )
            for row in profile_rows
        )

        return PlatformDetail(
            ship_id=ship_row["ship_id"], name=ship_row["ship_name"], ship_class=ship_row["ship_class"],
            file_name=ship_row["file_name"], faction_id=ship_row["faction_id"],
            faction_name=ship_row["faction_name"], profiles=profiles,
        )


    def get_profile_by_id(self, profile_id: int) -> PlatformProfile | None:
        """Load one fleet-list profile for Fleet Manager and Tactical Assistant."""
        with self._connections.connect() as connection:
            row = connection.execute(
                """
                SELECT ap.*, fl.name AS fleet_name, COALESCE(fl.initiative, '') AS fleet_initiative
                FROM acta_profiles ap
                JOIN fleet_lists fl ON fl.fleet_list_id = ap.fleet_list_id
                WHERE ap.profile_id = ?
                """,
                (profile_id,),
            ).fetchone()
            if row is None:
                return None
            traits = tuple(
                item["trait"]
                for item in connection.execute(
                    "SELECT trait FROM traits WHERE profile_id = ? ORDER BY sort_order, trait",
                    (profile_id,),
                )
            )
            weapons = []
            for item in connection.execute(
                """
                SELECT name, COALESCE(range_value, '') AS range_value,
                       COALESCE(arc, '') AS arc, COALESCE(attack_dice, '') AS attack_dice,
                       COALESCE(traits, '') AS traits, COALESCE(sort_order, 0) AS sort_order
                FROM weapons WHERE profile_id = ? ORDER BY sort_order, weapon_id
                """,
                (profile_id,),
            ):
                weapons.append(WeaponDetail(
                    name=item["name"], range_value=item["range_value"], arc=item["arc"],
                    attack_dice=str(item["attack_dice"]), traits=item["traits"],
                    sort_order=item["sort_order"],
                ))
        return PlatformProfile(
            profile_id=row["profile_id"],
            fleet_list_id=row["fleet_list_id"],
            fleet_name=row["fleet_name"],
            initiative=str(row["initiative"] or row["fleet_initiative"] or ""),
            priority_level=str(row["priority_level"] or ""),
            speed=str(row["speed"] if row["speed"] is not None else ""),
            turn=str(row["turn"] or ""),
            hull=str(row["hull"] if row["hull"] is not None else ""),
            damage=str(row["damage"] or ""),
            crew=str(row["crew"] or ""),
            troops=str(row["troops"] or ""),
            craft=str(row["craft"] or ""),
            in_service=str(row["in_service"] or ""),
            source_book=str(row["source_book"] or ""),
            crew_quality=str(row["crew_quality"] or ""),
            notes=tuple(line.strip() for line in str(row["notes"] or "").splitlines() if line.strip()),
            traits=traits,
            weapons=order_weapons(weapons),
        )

    def _options(self, sql: str, params: tuple[Any, ...] = ()) -> list[FilterOption]:
        with self._connections.connect() as connection:
            rows = connection.execute(sql, params).fetchall()
        return [FilterOption(id=row["id"], label=row["label"], count=row["total"]) for row in rows]

    def list_factions(self) -> list[FilterOption]:
        return self._options("""
            SELECT f.faction_id AS id, f.name AS label,
                   COUNT(DISTINCT COALESCE(s.ship_id, ap.ship_id)) AS total
            FROM factions f
            LEFT JOIN ships s ON s.faction_id = f.faction_id
            LEFT JOIN fleet_lists fl ON fl.faction_id = f.faction_id
            LEFT JOIN acta_profiles ap ON ap.fleet_list_id = fl.fleet_list_id
            GROUP BY f.faction_id, f.name ORDER BY f.name COLLATE NOCASE
        """)

    def list_fleets(self, faction_id: int | None = None) -> list[FilterOption]:
        if faction_id is None:
            return self._options("""
                SELECT fl.fleet_list_id AS id, fl.name AS label, COUNT(DISTINCT ap.ship_id) AS total
                FROM fleet_lists fl LEFT JOIN acta_profiles ap ON ap.fleet_list_id = fl.fleet_list_id
                GROUP BY fl.fleet_list_id, fl.name ORDER BY fl.name COLLATE NOCASE
            """)
        return self._options("""
            SELECT fl.fleet_list_id AS id, fl.name AS label, COUNT(DISTINCT ap.ship_id) AS total
            FROM fleet_lists fl LEFT JOIN acta_profiles ap ON ap.fleet_list_id = fl.fleet_list_id
            WHERE fl.faction_id = ? GROUP BY fl.fleet_list_id, fl.name ORDER BY fl.name COLLATE NOCASE
        """, (faction_id,))

    def list_priorities(self) -> list[FilterOption]:
        return self._options("""
            SELECT priority_level AS id, priority_level AS label, COUNT(DISTINCT ship_id) AS total
            FROM acta_profiles WHERE priority_level IS NOT NULL AND priority_level <> ''
            GROUP BY priority_level
            ORDER BY CASE priority_level WHEN 'Patrol' THEN 1 WHEN 'Skirmish' THEN 2 WHEN 'Raid' THEN 3
                WHEN 'Battle' THEN 4 WHEN 'War' THEN 5 WHEN 'Armageddon' THEN 6 ELSE 99 END
        """)

    def list_traits(self) -> list[FilterOption]:
        return self._options("""
            SELECT trait AS id, trait AS label, COUNT(DISTINCT ap.ship_id) AS total
            FROM traits t JOIN acta_profiles ap ON ap.profile_id = t.profile_id
            GROUP BY trait ORDER BY trait COLLATE NOCASE
        """)

    def list_weapons(self) -> list[FilterOption]:
        return self._options("""
            SELECT name AS id, name AS label, COUNT(DISTINCT ap.ship_id) AS total
            FROM weapons w JOIN acta_profiles ap ON ap.profile_id = w.profile_id
            GROUP BY name ORDER BY name COLLATE NOCASE
        """)
