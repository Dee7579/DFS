SHIP_NAME = 'Victory-class Destroyer'
SHIP_CLASS = 'Victory-class Destroyer'
FILE_NAME = 'Victory_class_Destroyer'
FACTION_NAME = "Interstellar Alliance"

LEGACY_SHIP_NAMES = [
    'Victory Destroyer',
    'Victory-class destroyer',
]

PROFILES = [
    {
        'fleet': 'Interstellar Alliance',
        'priority': 'Armageddon',
        'speed': 10,
        'turn': '1/45°',
        'hull': 6,
        'damage': '100/16',
        'crew': '110/20',
        'troops': 6,
        'craft': '3 Aurora Starfury Flights, 3 Thunderbolt Starfury Flights',
        'in_service': '2266+',
        'traits': ['Adaptive Armour', 'Advanced Jump Engine', 'Afterburner', 'Anti-Fighter 6', 'Carrier 2', 'Command +3', 'Flight Computer', 'Interceptors 6'],
        'notes': ['If the Lightning Cannon is fired, the Victory may not fire any other weapons and will be moved forward 4” next turn. It then cannot do anything else except take damage until after the End Phase of the next turn.'],
        'weapons': [
            ('Lightning Cannon', '20', 'B', 8, 'Beam, Precise, Quad Damage'),
            ('Improved Neutron Laser', '30', 'F', 6, 'Beam, Precise, Triple Damage'),
            ('Improved Neutron Laser', '30', 'A', 4, 'Beam, Precise, Triple Damage'),
            ('Heavy Pulse Cannon', '12', 'T', 20, 'Twin-Linked'),
            ('Fusion Cannon', '18', 'T', 10, 'Mini-Beam'),
        ],
    },
]
