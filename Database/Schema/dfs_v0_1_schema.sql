CREATE TABLE factions (
    faction_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE fleet_lists (
    fleet_list_id INTEGER PRIMARY KEY AUTOINCREMENT,
    faction_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    year_range TEXT,
    initiative TEXT,
    FOREIGN KEY (faction_id) REFERENCES factions(faction_id)
);

CREATE TABLE ships (
    ship_id INTEGER PRIMARY KEY AUTOINCREMENT,
    ship_name TEXT NOT NULL,
    ship_class TEXT,
    faction_id INTEGER NOT NULL,
    FOREIGN KEY (faction_id) REFERENCES factions(faction_id)
);

CREATE TABLE acta_profiles (
    profile_id INTEGER PRIMARY KEY AUTOINCREMENT,
    ship_id INTEGER NOT NULL,
    fleet_list_id INTEGER NOT NULL,
    priority_level TEXT,
    speed INTEGER,
    turn TEXT,
    hull INTEGER,
    damage TEXT,
    crew TEXT,
    crew_quality TEXT,
    troops TEXT,
    craft TEXT,
    initiative TEXT,
    in_service TEXT,
    source_book TEXT,
    FOREIGN KEY (ship_id) REFERENCES ships(ship_id),
    FOREIGN KEY (fleet_list_id) REFERENCES fleet_lists(fleet_list_id)
);

CREATE TABLE weapons (
    weapon_id INTEGER PRIMARY KEY AUTOINCREMENT,
    profile_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    range_value TEXT,
    arc TEXT,
    attack_dice TEXT,
    traits TEXT,
    sort_order INTEGER,
    FOREIGN KEY (profile_id) REFERENCES acta_profiles(profile_id)
);

CREATE TABLE traits (
    trait_id INTEGER PRIMARY KEY AUTOINCREMENT,
    profile_id INTEGER NOT NULL,
    trait TEXT NOT NULL,
    sort_order INTEGER,
    FOREIGN KEY (profile_id) REFERENCES acta_profiles(profile_id)
);