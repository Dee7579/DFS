SHIP_NAME = 'Shadow Scout'
SHIP_CLASS = 'Shadow Scout'
FILE_NAME = 'Shadow_Scout'
FACTION_NAME = 'The Shadows'

LEGACY_SHIP_NAMES = []

PROFILES = [
    {
        'fleet': 'The Shadows',
        'priority': 'Raid',
        'speed': 10,
        'turn': 'SM',
        'hull': 5,
        'damage': '25/7',
        'crew': '-',
        'troops': '-',
        'craft': '-',
        'in_service': 'Until 2261',
        'traits': ['Atmospheric', 'Dodge 6+', 'Scout', 'Self-Repair 1', 'Shields 5/5', 'Stealth 5+'],
        'notes': [
            'Fleet Rules: Hyperspace Mastery, Redundant Systems, Crew, Special Actions, Superior Technology, Superb Manoeuvrability.',
            'FAQ: Shadow critical hits repair in the End Phase after the turn they were inflicted.',
            'P&P: Anti-Fighter Defences, Merging, and Mind Scream may apply.',
            'Mind Scream: enemy ships with Psychic Crew lose 1 Crew when this vessel moves within 6 inches.',
        ],
        'weapons': [
            ('Phasing Pulse Cannon', '8', 'F', 6, 'Accurate, Double Damage, Super AP'),
        ],
    },
]
