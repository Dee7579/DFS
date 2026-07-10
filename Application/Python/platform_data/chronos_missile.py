SHIP_NAME = "Chronos-class Missile Frigate (Variant)"
SHIP_CLASS = "Chronos-class Missile Frigate"
FILE_NAME = "Chronos_Missile_Frigate_Variant"
FACTION_NAME = "Earth Alliance"

LEGACY_SHIP_NAMES = [
    "Chronos Missile Frigate",
]

PROFILES = [
    {
        "fleet": "Earth Alliance - Crusade Era",
        "priority": "Skirmish",
        "speed": 8,
        "turn": "2/45°",
        "hull": 6,
        "damage": "16/3",
        "crew": "18/5",
        "troops": 2,
        "craft": "None",
        "in_service": "2302+",
        "traits": ["Anti-Fighter 2", "Interceptors 2"],
        "notes": [
            "The Advanced Missile Racks ignore the Slow-Loading trait unless the Chronos is Crippled."
        ],
        "weapons": [
            ("Heavy Pulse Cannon", "12", "F", 2, "Twin-Linked"),
            ("Advanced Missile Rack", "30", "P", 2, "Precise, Slow-Loading, Super AP"),
            ("Advanced Missile Rack", "30", "S", 2, "Precise, Slow-Loading, Super AP"),
            ("Heavy Pulse Cannon", "12", "A", 2, "Twin-Linked"),
        ],
    },
]
