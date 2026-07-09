SHIP_NAME = 'Shadow Ship (Young)'
SHIP_CLASS = 'Shadow Ship (Young)'
FILE_NAME = 'Shadow_Ship_Young'
FACTION_NAME = 'The Shadows'

LEGACY_SHIP_NAMES = [
    'Shadow Ship Young',
    'Shadow Ship (young)',
]

PROFILES = [
    {
        'fleet': 'The Shadows',
        'priority': 'War',
        'speed': 8,
        'turn': 'SM',
        'hull': 6,
        'damage': '75/19',
        'crew': '-',
        'troops': '-',
        'craft': '2 Shadow Fighter flights',
        'in_service': 'Until 2261',
        'traits': ['Atmospheric', 'Self-Repair 2D6', 'Shields 10/5'],
        'notes': [
            'Fleet Rules: Hyperspace Mastery, Redundant Systems, Crew, Special Actions, Superior Technology, Superb Manoeuvrability.',
            'FAQ: Shadow critical hits repair in the End Phase after the turn they were inflicted.',
            'P&P: Anti-Fighter Defences, Merging, and Mind Scream may apply.',
            'Mind Scream: enemy ships with Psychic Crew lose 1D6 Crew when this vessel moves within 6 inches.',
            'Fighter Dispersal Tube: carries Shadow Fighters as part of the ship cost.',
        ],
        'weapons': [
            ('Molecular Slicer Beam', '24', 'F', 6, 'Beam, Precise, Triple Damage'),
            ('Fighter Dispersal Tube', '30', 'F', '-', ''),
        ],
    },
]
