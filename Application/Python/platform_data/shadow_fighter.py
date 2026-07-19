SHIP_NAME = 'Shadow Fighter'
SHIP_CLASS = 'Shadow Fighter'
FILE_NAME = 'Shadow_Fighter'
FACTION_NAME = 'The Shadows'

LEGACY_SHIP_NAMES = [
    'Shadow Fighter Flight',
    'Shadow Fighter Wing',
]

PROFILES = [
    {
        'fleet': 'The Shadows',
        'priority': 'Patrol',
        'speed': 12,
        'turn': 'SM',
        'hull': 5,
        'damage': '-',
        'crew': '-',
        'troops': '-',
        'craft': '-',
        'in_service': 'Until 2261',
        'traits': ['Atmospheric', 'Dodge 3+', 'Fighter', 'Shields 1/1'],
        'notes': [
            'Dogfight: +0',
            'Wing of Two Flights',
            'Shadow Fighters cannot be jammed.',
            'Shields work against Anti-Fighter, Advanced Anti-Fighter, and in dogfights. Ignore the first successful Anti-Fighter result; in a dogfight, the flight must be defeated twice to be destroyed.',
        ],
        'weapons': [
            ('Polarity Cannon', '2', 'T', 3, 'AP, Double Damage'),
        ],
    },
]
