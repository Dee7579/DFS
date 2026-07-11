SHIP_NAME = 'Nemesis-class Advanced Destroyer'
SHIP_CLASS = 'Nemesis-class Advanced Destroyer'
FILE_NAME = 'Nemesis_class_Advanced_Destroyer'
FACTION_NAME = 'Psi Corps'

LEGACY_SHIP_NAMES = [
]

PROFILES = [
    {
        'fleet': 'Psi Corps',
        'priority': 'Armageddon',
        'speed': 9,
        'turn': '1/45°',
        'hull': 6,
        'damage': '95/18',
        'crew': '105/20',
        'troops': 3,
        'craft': '4 Shadowfury flights',
        'in_service': '2268+',
        'traits': ['Advanced Jump Engine', 'Anti-Fighter 8', 'Flight Computer', 'Interceptors 6', 'Self-Repairing 2D6', 'Shields 20/2D6'],
        'notes': ['HEL track array: +1 to attempts to break through a target’s Stealth.', 'Advanced Missile Rack ignores Slow-Loading unless the Nemesis is Crippled.'],
        'weapons': [
            ('Molecular Slicer Beam', '30', 'B', 8, 'Beam, Triple Damage'),
            ('Heavy Phasing Pulse', '12', 'F', 12, 'AP, Double Damage'),
            ('Advanced Missile Rack', '30', 'F', 6, 'Precise, Slow-Loading **, Super AP'),
            ('Light Multi-Phased Cutter', '10', 'P', 12, 'Mini-Beam, Twin-Linked'),
            ('Light Multi-Phased Cutter', '10', 'S', 12, 'Mini-Beam, Twin-Linked'),
            ('Light Multi-Phased Cutter', '10', 'A', 8, 'Mini-Beam, Twin-Linked'),
        ],
    },
]
