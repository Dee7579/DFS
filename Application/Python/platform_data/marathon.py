SHIP_NAME = 'Marathon-class Advanced Cruiser'
SHIP_CLASS = 'Marathon-class Advanced Cruiser'
FILE_NAME = 'Marathon_Advanced_Cruiser'
FACTION_NAME = "Earth Alliance"

LEGACY_SHIP_NAMES = [
    'Marathon Advanced Cruiser',
]

PROFILES = [
    {
        'fleet': 'Earth Alliance - Crusade Era',
        'priority': 'Battle',
        'speed': 12,
        'turn': '2/45°',
        'hull': 6,
        'damage': '40/12',
        'crew': '45/14',
        'troops': 4,
        'craft': '2 Aurora Starfury Flights',
        'in_service': '2266+',
        'traits': ['Anti-Fighter 4', 'Flight Computer', 'Interceptors 4', 'Jump Engine'],
        'notes': ['Advanced Missile Rack ignores the Slow-Loading trait unless the Marathon is Crippled.'],
        'weapons': [
            ('Medium Neutron Cannon', '25', 'B', 4, 'Beam, Triple Damage'),
            ('Medium Neutron Cannon', '25', 'B(a)', 2, 'Beam, Triple Damage'),
            ('Heavy Pulse Cannon', '12', 'F', 6, 'Twin-Linked'),
            ('Heavy Pulse Cannon', '12', 'A', 4, 'Twin-Linked'),
            ('Heavy Pulse Cannon', '12', 'P', 10, 'Twin-Linked'),
            ('Heavy Pulse Cannon', '12', 'S', 10, 'Twin-Linked'),
            ('Advanced Missile Rack', '30', 'F', 4, 'Precise, Slow-Loading *, Super AP'),
        ],
    },
]
