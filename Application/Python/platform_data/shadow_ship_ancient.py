SHIP_NAME = 'Shadow Ship (Ancient)'
SHIP_CLASS = 'Shadow Ship (Ancient)'
FILE_NAME = 'Shadow_Ship_Ancient'
FACTION_NAME = 'The Shadows'

LEGACY_SHIP_NAMES = [
    'Shadow Ship Ancient',
    'Shadow Ship (ancient)',
]

PROFILES = [
    {
        'fleet': 'The Shadows',
        'priority': 'Armageddon',
        'speed': 8,
        'turn': 'SM',
        'hull': 6,
        'damage': '150/38',
        'crew': '-',
        'troops': '-',
        'craft': '6 Shadow Fighter flights',
        'in_service': 'Until 2261',
        'traits': ['Atmospheric', 'Self-Repair 3D6', 'Shields 20/10'],
        'notes': [
            'Fleet Rules: Hyperspace Mastery, Redundant Systems, Crew, Special Actions, Superior Technology, Superb Manoeuvrability.',
            'FAQ: Shadow critical hits repair in the End Phase after the turn they were inflicted.',
            'P&P: Anti-Fighter Defences, Merging, and Mind Scream may apply.',
            'Mind Scream: enemy ships with Psychic Crew lose 2D6 Crew when this vessel moves within 6 inches.',
            'Jump Point Disruptor may be used in place of other weapons.',
            'Fighter Dispersal Tube: carries Shadow Fighters as part of the ship cost.',
        ],
        'weapons': [
            ('Molecular Slicer Beam', '24', 'F', 6, 'Beam, Precise, Quad Damage'),
            ('Jump Point Disruptor', '18', 'F', '-', ''),
            ('Fighter Dispersal Tube', '30', 'F', '-', ''),
        ],
    },
]
