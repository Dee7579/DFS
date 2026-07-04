BEGIN TRANSACTION;

-- Factions
INSERT INTO factions (name)
SELECT 'Earth Alliance'
WHERE NOT EXISTS (
    SELECT 1 FROM factions WHERE name = 'Earth Alliance'
);

-- Fleet Lists
INSERT INTO fleet_lists (faction_id, name, year_range, initiative)
SELECT faction_id, 'Earth Alliance - The Early Years', '2220-2249', '+0'
FROM factions
WHERE name = 'Earth Alliance'
AND NOT EXISTS (
    SELECT 1 FROM fleet_lists WHERE name = 'Earth Alliance - The Early Years'
);

INSERT INTO fleet_lists (faction_id, name, year_range, initiative)
SELECT faction_id, 'Earth Alliance - Third Age', '2250-2266', '+1'
FROM factions
WHERE name = 'Earth Alliance'
AND NOT EXISTS (
    SELECT 1 FROM fleet_lists WHERE name = 'Earth Alliance - Third Age'
);

-- Hyperion Cruiser
INSERT INTO ships (ship_name, ship_class, faction_id)
SELECT 'Hyperion Cruiser', 'Cruiser', faction_id
FROM factions
WHERE name = 'Earth Alliance'
AND NOT EXISTS (
    SELECT 1 FROM ships WHERE ship_name = 'Hyperion Cruiser'
);

INSERT INTO acta_profiles
(ship_id, fleet_list_id, priority_level, speed, turn, hull, damage, crew, troops, craft, initiative, in_service, source_book)
SELECT s.ship_id, fl.fleet_list_id, 'Raid', 8, '2/45°', 5, '28/6', '32/6', '3',
       '1 Tiger Starfury Flight', '+0', '2230+', 'Fleet Lists'
FROM ships s, fleet_lists fl
WHERE s.ship_name = 'Hyperion Cruiser'
AND fl.name = 'Earth Alliance - The Early Years'
AND NOT EXISTS (
    SELECT 1 FROM acta_profiles ap
    WHERE ap.ship_id = s.ship_id
    AND ap.fleet_list_id = fl.fleet_list_id
);

DELETE FROM traits WHERE profile_id = (
    SELECT ap.profile_id
    FROM acta_profiles ap
    JOIN ships s ON ap.ship_id = s.ship_id
    WHERE s.ship_name = 'Hyperion Cruiser'
);

INSERT INTO traits (profile_id, trait, sort_order)
SELECT ap.profile_id, 'Anti-Fighter 2', 1 FROM acta_profiles ap JOIN ships s ON ap.ship_id = s.ship_id WHERE s.ship_name = 'Hyperion Cruiser'
UNION ALL SELECT ap.profile_id, 'Interceptors 2', 2 FROM acta_profiles ap JOIN ships s ON ap.ship_id = s.ship_id WHERE s.ship_name = 'Hyperion Cruiser'
UNION ALL SELECT ap.profile_id, 'Jump Engine', 3 FROM acta_profiles ap JOIN ships s ON ap.ship_id = s.ship_id WHERE s.ship_name = 'Hyperion Cruiser';

DELETE FROM weapons WHERE profile_id = (
    SELECT ap.profile_id
    FROM acta_profiles ap
    JOIN ships s ON ap.ship_id = s.ship_id
    WHERE s.ship_name = 'Hyperion Cruiser'
);

INSERT INTO weapons (profile_id, name, range_value, arc, attack_dice, traits, sort_order)
SELECT ap.profile_id, 'Heavy Laser Cannon', '18', 'B', '4', 'Beam, Double Damage', 1 FROM acta_profiles ap JOIN ships s ON ap.ship_id = s.ship_id WHERE s.ship_name = 'Hyperion Cruiser'
UNION ALL SELECT ap.profile_id, 'Heavy Laser Cannon', '18', 'B(A)', '2', 'Beam, Double Damage', 2 FROM acta_profiles ap JOIN ships s ON ap.ship_id = s.ship_id WHERE s.ship_name = 'Hyperion Cruiser'
UNION ALL SELECT ap.profile_id, 'Plasma Cannon', '8', 'F', '4', 'AP, Twin-Linked', 3 FROM acta_profiles ap JOIN ships s ON ap.ship_id = s.ship_id WHERE s.ship_name = 'Hyperion Cruiser'
UNION ALL SELECT ap.profile_id, 'Plasma Cannon', '8', 'A', '2', 'AP', 4 FROM acta_profiles ap JOIN ships s ON ap.ship_id = s.ship_id WHERE s.ship_name = 'Hyperion Cruiser'
UNION ALL SELECT ap.profile_id, 'Plasma Cannon', '8', 'P', '6', 'AP', 5 FROM acta_profiles ap JOIN ships s ON ap.ship_id = s.ship_id WHERE s.ship_name = 'Hyperion Cruiser'
UNION ALL SELECT ap.profile_id, 'Plasma Cannon', '8', 'S', '6', 'AP', 6 FROM acta_profiles ap JOIN ships s ON ap.ship_id = s.ship_id WHERE s.ship_name = 'Hyperion Cruiser';

-- Omega Destroyer
INSERT INTO ships (ship_name, ship_class, faction_id)
SELECT 'Omega Destroyer', 'Destroyer', faction_id
FROM factions
WHERE name = 'Earth Alliance'
AND NOT EXISTS (
    SELECT 1 FROM ships WHERE ship_name = 'Omega Destroyer'
);

INSERT INTO acta_profiles
(ship_id, fleet_list_id, priority_level, speed, turn, hull, damage, crew, troops, craft, initiative, in_service, source_book)
SELECT s.ship_id, fl.fleet_list_id, 'Battle', 7, '1/45°', 6, '48/10', '62/14', '4',
       '4 Aurora Starfury Flights', '+1', '2250+', 'Fleet Lists'
FROM ships s, fleet_lists fl
WHERE s.ship_name = 'Omega Destroyer'
AND fl.name = 'Earth Alliance - Third Age'
AND NOT EXISTS (
    SELECT 1 FROM acta_profiles ap
    WHERE ap.ship_id = s.ship_id
    AND ap.fleet_list_id = fl.fleet_list_id
);

DELETE FROM traits WHERE profile_id = (
    SELECT ap.profile_id
    FROM acta_profiles ap
    JOIN ships s ON ap.ship_id = s.ship_id
    WHERE s.ship_name = 'Omega Destroyer'
);

INSERT INTO traits (profile_id, trait, sort_order)
SELECT ap.profile_id, 'Anti-Fighter 6', 1 FROM acta_profiles ap JOIN ships s ON ap.ship_id = s.ship_id WHERE s.ship_name = 'Omega Destroyer'
UNION ALL SELECT ap.profile_id, 'Interceptors 3', 2 FROM acta_profiles ap JOIN ships s ON ap.ship_id = s.ship_id WHERE s.ship_name = 'Omega Destroyer'
UNION ALL SELECT ap.profile_id, 'Jump Engine', 3 FROM acta_profiles ap JOIN ships s ON ap.ship_id = s.ship_id WHERE s.ship_name = 'Omega Destroyer'
UNION ALL SELECT ap.profile_id, 'Lumbering', 4 FROM acta_profiles ap JOIN ships s ON ap.ship_id = s.ship_id WHERE s.ship_name = 'Omega Destroyer';

DELETE FROM weapons WHERE profile_id = (
    SELECT ap.profile_id
    FROM acta_profiles ap
    JOIN ships s ON ap.ship_id = s.ship_id
    WHERE s.ship_name = 'Omega Destroyer'
);

INSERT INTO weapons (profile_id, name, range_value, arc, attack_dice, traits, sort_order)
SELECT ap.profile_id, 'Heavy Laser Cannon', '30', 'B', '6', 'Beam, Double Damage', 1 FROM acta_profiles ap JOIN ships s ON ap.ship_id = s.ship_id WHERE s.ship_name = 'Omega Destroyer'
UNION ALL SELECT ap.profile_id, 'Heavy Laser Cannon', '30', 'B(A)', '4', 'Beam, Double Damage', 2 FROM acta_profiles ap JOIN ships s ON ap.ship_id = s.ship_id WHERE s.ship_name = 'Omega Destroyer'
UNION ALL SELECT ap.profile_id, 'Heavy Pulse Cannon', '12', 'F', '8', 'Twin-Linked', 3 FROM acta_profiles ap JOIN ships s ON ap.ship_id = s.ship_id WHERE s.ship_name = 'Omega Destroyer'
UNION ALL SELECT ap.profile_id, 'Light Laser Cannon', '15', 'P', '4', 'Mini-Beam, Slow-Loading', 4 FROM acta_profiles ap JOIN ships s ON ap.ship_id = s.ship_id WHERE s.ship_name = 'Omega Destroyer'
UNION ALL SELECT ap.profile_id, 'Light Laser Cannon', '15', 'S', '4', 'Mini-Beam, Slow-Loading', 5 FROM acta_profiles ap JOIN ships s ON ap.ship_id = s.ship_id WHERE s.ship_name = 'Omega Destroyer'
UNION ALL SELECT ap.profile_id, 'Medium Pulse Cannon', '10', 'A', '4', 'Twin-Linked', 6 FROM acta_profiles ap JOIN ships s ON ap.ship_id = s.ship_id WHERE s.ship_name = 'Omega Destroyer'
UNION ALL SELECT ap.profile_id, 'Medium Pulse Cannon', '10', 'P', '8', 'Twin-Linked', 7 FROM acta_profiles ap JOIN ships s ON ap.ship_id = s.ship_id WHERE s.ship_name = 'Omega Destroyer'
UNION ALL SELECT ap.profile_id, 'Medium Pulse Cannon', '10', 'S', '8', 'Twin-Linked', 8 FROM acta_profiles ap JOIN ships s ON ap.ship_id = s.ship_id WHERE s.ship_name = 'Omega Destroyer';

COMMIT;