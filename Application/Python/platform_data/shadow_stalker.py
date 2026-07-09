SHIP_NAME = 'Shadow Stalker'
SHIP_CLASS = 'Shadow Stalker (Shadow Scout Variant)'
FILE_NAME = 'Shadow_Stalker'
FACTION_NAME = 'The Shadows'

LEGACY_SHIP_NAMES = [
    'Shadow Stalker (Shadow Scout Variant)',
]

PROFILES = [
    {
        'fleet': 'The Shadows',
        'priority': 'Battle',
        'speed': 10,
        'turn': 'SM',
        'hull': 6,
        'damage': '25/7',
        'crew': '-',
        'troops': '-',
        'craft': '-',
        'in_service': 'Until 2261',
        'traits': ['Atmospheric', 'Dodge 6+', 'Self-Repair 1D6', 'Shields 10/5', 'Stealth 5+'],
        'notes': [
            'Variant of Shadow Scout.',
            'Fleet Rules: Hyperspace Mastery, Redundant Systems, Crew, Special Actions, Superior Technology, Superb Manoeuvrability.',
            'FAQ: Shadow critical hits repair in the End Phase after the turn they were inflicted.',
            'P&P: Shadow Stalker gains Stealth 5+.',
            'P&P: Anti-Fighter Defences, Merging, and Mind Scream may apply.',
            'Mind Scream: enemy ships with Psychic Crew lose 2 Crew when this vessel moves within 6 inches.',
        ],
        'weapons': [
            ('Molecular Slicer Beam', '18', 'F', 3, 'Beam, Precise, Triple Damage'),
        ],
    },
]
