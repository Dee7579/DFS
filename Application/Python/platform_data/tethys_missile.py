SHIP_NAME = 'Tethys-class Missile Boat (Variant)'
SHIP_CLASS = 'Tethys-class Missile Boat'
FILE_NAME = 'Tethys_Missile_Boat_Variant'
FACTION_NAME = "Earth Alliance"

LEGACY_SHIP_NAMES = [
    'Tethys Missile Boat',
]

PROFILES = [
    {
        'fleet': 'Earth Alliance - The Early Years',
        'priority': 'Patrol',
        'speed': 8,
        'turn': '2/45°',
        'hull': 4,
        'damage': '6/2',
        'crew': '8/2',
        'troops': '-',
        'craft': 'None',
        'in_service': '2231+',
        'traits': ['Interceptors 1'],
        'notes': ['Two Ships', 'Missile Variants: The Tethys Missile Boat may not use the missile variants detailed in the Earth Alliance fleet list.'],
        'weapons': [
            ('Missile Rack', '20', 'F', 2, 'AP, Precise, Slow-Loading'),
            ('Light Plasma Cannon', '6', 'F', 2, 'AP'),
            ('Light Plasma Cannon', '6', 'P', 1, 'AP'),
            ('Light Plasma Cannon', '6', 'S', 1, 'AP'),
        ],
    },
]
