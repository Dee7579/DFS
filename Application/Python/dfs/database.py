import sqlite3

from dfs.ship import Ship, Weapon


class Database:
    def __init__(self, db_path):
        self.db_path = db_path

    def connect(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def get_ship(self, ship_name):
        with self.connect() as conn:
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT ap.profile_id
                FROM ships s
                JOIN acta_profiles ap ON s.ship_id = ap.ship_id
                WHERE s.ship_name = ?
                LIMIT 1;
                """,
                (ship_name,),
            )

            row = cursor.fetchone()

            if row is None:
                return None

            return self.get_ship_by_profile(row["profile_id"])

    def get_ship_by_profile(self, profile_id, fleet_override=None, initiative_override=None):
        with self.connect() as conn:
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT
                    s.ship_name,
                    s.ship_class,
                    s.file_name,
                    f.name AS faction,
                    fl.name AS fleet,
                    fl.initiative,
                    ap.profile_id,
                    ap.priority_level,
                    ap.speed,
                    ap.turn,
                    ap.hull,
                    ap.damage,
                    ap.crew,
                    ap.troops,
                    ap.craft,
                    ap.in_service,
                    ap.notes
                FROM acta_profiles ap
                JOIN ships s ON ap.ship_id = s.ship_id
                JOIN fleet_lists fl ON ap.fleet_list_id = fl.fleet_list_id
                JOIN factions f ON s.faction_id = f.faction_id
                WHERE ap.profile_id = ?;
                """,
                (profile_id,),
            )

            row = cursor.fetchone()

            if row is None:
                return None

            ship = Ship(
                name=row["ship_name"],
                ship_class=row["ship_class"],
                faction=row["faction"],
                fleet=fleet_override if fleet_override else row["fleet"],
                priority=row["priority_level"],
                speed=row["speed"],
                turn=row["turn"],
                hull=row["hull"],
                damage=row["damage"],
                crew=row["crew"],
                troops=row["troops"],
                craft=row["craft"],
                initiative=initiative_override if initiative_override else row["initiative"],
                in_service=row["in_service"],
            )

            ship.file_name = row["file_name"] if row["file_name"] else row["ship_name"]
            ship.traits = self.get_traits(profile_id)
            ship.weapons = self.get_weapons(profile_id)
            ship.notes = self.parse_notes(row["notes"])

            return ship

    def get_all_ships(self):
        with self.connect() as conn:
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT
                    ap.profile_id,
                    s.ship_name,
                    fl.name AS fleet_name,
                    fl.initiative AS fleet_initiative
                FROM ships s
                JOIN acta_profiles ap ON s.ship_id = ap.ship_id
                JOIN profile_fleet_lists pfl ON ap.profile_id = pfl.profile_id
                JOIN fleet_lists fl ON pfl.fleet_list_id = fl.fleet_list_id
                ORDER BY fl.name, s.ship_name;
                """
            )

            rows = cursor.fetchall()

        ships = []

        for row in rows:
            ship = self.get_ship_by_profile(
                row["profile_id"],
                fleet_override=row["fleet_name"],
                initiative_override=row["fleet_initiative"],
            )

            if ship is not None:
                ships.append(ship)

        return ships

    def get_traits(self, profile_id):
        with self.connect() as conn:
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT trait
                FROM traits
                WHERE profile_id = ?
                ORDER BY sort_order;
                """,
                (profile_id,),
            )

            return [row["trait"] for row in cursor.fetchall()]

    def get_weapons(self, profile_id):
        with self.connect() as conn:
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT
                    name,
                    range_value,
                    arc,
                    attack_dice,
                    traits
                FROM weapons
                WHERE profile_id = ?
                ORDER BY sort_order;
                """,
                (profile_id,),
            )

            weapons = []

            for row in cursor.fetchall():
                weapons.append(
                    Weapon(
                        name=row["name"],
                        range=row["range_value"],
                        arc=row["arc"],
                        attack_dice=row["attack_dice"],
                        traits=row["traits"],
                    )
                )

            return weapons

    def parse_notes(self, notes_text):
        if not notes_text:
            return []

        return [
            line.strip()
            for line in str(notes_text).splitlines()
            if line.strip()
        ]