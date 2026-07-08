SHIP_NAME = 'Apollo-class Strike Cruiser (Variant)'
SHIP_CLASS = 'Apollo-class Strike Cruiser'
FILE_NAME = 'Apollo_Strike_Cruiser_Variant'
FACTION_NAME = "Earth Alliance"

LEGACY_SHIP_NAMES = [
    'Apollo Strike Cruiser',
]

PROFILES = [
    {
        'fleet': 'Earth Alliance - Crusade Era',
        'priority': 'Battle',
        'speed': 7,
        'turn': '1/45°',
        'hull': 6,
        'damage': '38/8',
        'crew': '46/9',
        'troops': 2,
        'craft': '1 Aurora Starfury flight',
        'in_service': '2268+',
        'traits': ['Anti-Fighter 4', 'Interceptors 3', 'Jump Engine'],
        'notes': ['Advanced Missile Racks ignore the Slow-Loading trait unless the Apollo is Crippled.'],
        'weapons': [
            ('Advanced Missile Rack', '30', 'F', 4, 'Precise, Slow-Loading *, Super AP'),
            ('Advanced Missile Rack', '30', 'A', 2, 'Precise, Slow-Loading *, Super AP'),
            ('Railgun', '20', 'P', 6, 'AP, Double Damage'),
            ('Railgun', '20', 'S', 6, 'AP, Double Damage'),
            ('Heavy Pulse Cannon', '12', 'P', 14, 'Twin-Linked'),
            ('Heavy Pulse Cannon', '12', 'S', 14, 'Twin-Linked'),
        ],
    },
]
