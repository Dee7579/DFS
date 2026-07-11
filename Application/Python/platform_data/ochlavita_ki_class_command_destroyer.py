SHIP_NAME = 'Ochlavita-Ki class Command Destroyer (Ochlavita Variant)'
SHIP_CLASS = 'Ochlavita-Ki class Command Destroyer (Ochlavita Variant)'
FILE_NAME = 'Ochlavita_Ki_class_Command_Destroyer'
FACTION_NAME = 'Dilgar Imperium'

LEGACY_SHIP_NAMES = [
    'Ochlavita-Ki class Command Destroyer (Variant)',
]

PROFILES = [
    {
        'fleet': 'Dilgar Imperium',
        'priority': 'Skirmish',
        'speed': 10,
        'turn': '2/45°',
        'hull': 5,
        'damage': '22/4',
        'crew': '20/4',
        'troops': 3,
        'craft': 'None',
        'in_service': '2231-2232',
        'traits': ['Agile', 'Anti-Fighter 2', 'Command +1'],
        'notes': ['While within a Pentacon, all other ships it leads gain +1 to Crew Quality checks.'],
        'weapons': [
            ('Anti-Ship Missiles', '24', 'F', 4, 'AP, Double Damage, Slow-Loading'),
            ('Medium Bolters', '10', 'F', 2, 'AP, Double Damage'),
            ('Medium Bolters', '10', 'A', 2, 'AP, Double Damage'),
            ('Light Pulsars', '8', 'T', 4, ''),
        ],
    },
]
