SHIP_NAME = 'The Excalibur Destroyer'
SHIP_CLASS = 'Victory-class Destroyer'
FILE_NAME = 'Excalibur_Destroyer'
FACTION_NAME = "Earth Alliance"

LEGACY_SHIP_NAMES = [
    'Excalibur',
    'The Excalibur',
]

PROFILES = [
    {
        'fleet': 'Earth Alliance - Crusade Era',
        'priority': 'Armageddon',
        'speed': 10,
        'turn': '1/45°',
        'hull': 6,
        'damage': '100/16',
        'crew': '110/20',
        'troops': 6,
        'craft': '3 Aurora Starfury flights, 3 Thunderbolt Starfury flights',
        'in_service': '2266+',
        'traits': ['Adaptive Armour', 'Advanced Jump Engine', 'Afterburner', 'Anti-Fighter 6', 'Carrier 2', 'Command +3', 'Flight Computer', 'Interceptors 6', 'Unique'],
        'notes': ['If the Lightning Cannon is fired, the Excalibur may not fire any other weapons and will be moved forward 4" next turn. It cannot do anything else until after the End Phase of the next turn.'],
        'weapons': [
            ('Lightning Cannon', '20', 'B', 8, 'Beam, Precise, Quad Damage'),
            ('Improved Neutron Laser', '30', 'F', 6, 'Beam, Precise, Triple Damage'),
            ('Improved Neutron Laser', '30', 'A', 4, 'Beam, Precise, Triple Damage'),
            ('Heavy Pulse Cannon', '12', 'T', 20, 'Twin-Linked'),
            ('Fusion Cannon', '18', 'T', 10, 'Mini-Beam'),
        ],
    },
]
