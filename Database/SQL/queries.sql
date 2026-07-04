--------------------------------------------------------------------
-- DFS SQL TOOLBOX
-- Common queries for verifying database contents.
--
-- Tip:
-- Change only the values in the WHERE clauses (ship or fleet name).
--------------------------------------------------------------------



--------------------------------------------------------------------
-- 1. SHOW EVERY SHIP
--------------------------------------------------------------------

SELECT
    s.ship_name,
    s.ship_class,
    f.name AS faction,
    fl.name AS fleet,
    ap.priority_level
FROM ships s
JOIN factions f
    ON s.faction_id = f.faction_id
JOIN acta_profiles ap
    ON s.ship_id = ap.ship_id
JOIN fleet_lists fl
    ON ap.fleet_list_id = fl.fleet_list_id
ORDER BY
    f.name,
    fl.name,
    CASE ap.priority_level
        WHEN 'Patrol' THEN 1
        WHEN 'Skirmish' THEN 2
        WHEN 'Raid' THEN 3
        WHEN 'Battle' THEN 4
        WHEN 'War' THEN 5
        WHEN 'Armageddon' THEN 6
    END,
    s.ship_name;



--------------------------------------------------------------------
-- 2. SHOW EVERY SHIP IN A FLEET
-- Change the fleet name below.
--------------------------------------------------------------------

SELECT
    s.ship_name,
    ap.priority_level
FROM ships s
JOIN acta_profiles ap
    ON s.ship_id = ap.ship_id
JOIN fleet_lists fl
    ON ap.fleet_list_id = fl.fleet_list_id
WHERE fl.name = 'Earth Alliance - Third Age'
ORDER BY
CASE ap.priority_level
    WHEN 'Patrol' THEN 1
    WHEN 'Skirmish' THEN 2
    WHEN 'Raid' THEN 3
    WHEN 'Battle' THEN 4
    WHEN 'War' THEN 5
    WHEN 'Armageddon' THEN 6
END,
s.ship_name;



--------------------------------------------------------------------
-- 3. SHOW ALL SHIPS OF A PRIORITY LEVEL
-- Change 'Battle' as desired.
--------------------------------------------------------------------

SELECT
    s.ship_name,
    fl.name
FROM ships s
JOIN acta_profiles ap
    ON s.ship_id = ap.ship_id
JOIN fleet_lists fl
    ON ap.fleet_list_id = fl.fleet_list_id
WHERE ap.priority_level = 'Battle'
ORDER BY
    fl.name,
    s.ship_name;



--------------------------------------------------------------------
-- 4. SHOW ALL SHIPS WITH A GIVEN TRAIT
-- Change the trait below.
--------------------------------------------------------------------

SELECT
    s.ship_name,
    fl.name
FROM ships s
JOIN acta_profiles ap
    ON s.ship_id = ap.ship_id
JOIN traits t
    ON ap.profile_id = t.profile_id
JOIN fleet_lists fl
    ON ap.fleet_list_id = fl.fleet_list_id
WHERE t.trait = 'Jump Engine'
ORDER BY
    fl.name,
    s.ship_name;



--------------------------------------------------------------------
-- 5. SHOW ALL SHIPS CARRYING FIGHTERS
--------------------------------------------------------------------

SELECT
    s.ship_name,
    ap.craft
FROM ships s
JOIN acta_profiles ap
    ON s.ship_id = ap.ship_id
WHERE ap.craft IS NOT NULL
  AND ap.craft <> ''
ORDER BY
    s.ship_name;



--------------------------------------------------------------------
-- 6. SHOW ALL WEAPONS WITH A GIVEN TRAIT
-- Change the search text below.
--------------------------------------------------------------------

SELECT
    s.ship_name,
    w.name,
    w.arc,
    w.attack_dice,
    w.traits
FROM weapons w
JOIN acta_profiles ap
    ON w.profile_id = ap.profile_id
JOIN ships s
    ON ap.ship_id = s.ship_id
WHERE w.traits LIKE '%Beam%'
ORDER BY
    s.ship_name,
    w.name;



--------------------------------------------------------------------
-- 7. FULL SHIP CARD
-- Change the ship name below.
--------------------------------------------------------------------

SELECT
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
    ap.in_service,
    ap.source_book
FROM ships s
JOIN factions f
    ON s.faction_id = f.faction_id
JOIN acta_profiles ap
    ON s.ship_id = ap.ship_id
JOIN fleet_lists fl
    ON ap.fleet_list_id = fl.fleet_list_id
WHERE s.ship_name = 'Omega Destroyer';



--------------------------------------------------------------------
-- 8. SHIP TRAITS
-- Change the ship name below.
--------------------------------------------------------------------

SELECT
    t.trait
FROM ships s
JOIN acta_profiles ap
    ON s.ship_id = ap.ship_id
JOIN traits t
    ON ap.profile_id = t.profile_id
WHERE s.ship_name = 'Omega Destroyer'
ORDER BY
    t.sort_order;



--------------------------------------------------------------------
-- 9. SHIP WEAPONS
-- Change the ship name below.
--------------------------------------------------------------------

SELECT
    w.name,
    w.range_value,
    w.arc,
    w.attack_dice,
    w.traits
FROM ships s
JOIN acta_profiles ap
    ON s.ship_id = ap.ship_id
JOIN weapons w
    ON ap.profile_id = w.profile_id
WHERE s.ship_name = 'Omega Destroyer'
ORDER BY
    w.sort_order;



--------------------------------------------------------------------
-- 10. COMPLETE SHIP SHEET
-- Everything for one ship in one query.
-- Change the ship name below.
--------------------------------------------------------------------

SELECT
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
    ap.in_service,
    GROUP_CONCAT(DISTINCT t.trait, ', ') AS traits
FROM ships s
JOIN factions f
    ON s.faction_id = f.faction_id
JOIN acta_profiles ap
    ON s.ship_id = ap.ship_id
JOIN fleet_lists fl
    ON ap.fleet_list_id = fl.fleet_list_id
LEFT JOIN traits t
    ON ap.profile_id = t.profile_id
WHERE s.ship_name = 'Omega Destroyer'
GROUP BY
    s.ship_id;