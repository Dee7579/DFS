SHIP_NAME = 'Techno Mage Pinnace'
SHIP_CLASS = 'Techno Mage Pinnace'
FILE_NAME = 'Techno_Mage_Pinnace'
FACTION_NAME = 'Others'

LEGACY_SHIP_NAMES = [
]

PROFILES = [
    {
        'fleet': 'Others',
        'priority': 'Raid',
        'speed': 10,
        'turn': '2/45°',
        'hull': 5,
        'damage': '10/1',
        'crew': '1',
        'crew_quality': '6',
        'troops': '-',
        'craft': 'None',
        'initiative': '+5',
        'in_service': '2160+',
        'traits': ['Advanced Jump Engine', 'Agile', 'Scout', 'Stealth 6+'],
        'notes': [
            'Techno Mage ships never suffer Crew Damage.',
            "Uses the Shadows' Hyperspace Mastery special rules.",
            'Dreamers and Shapers: As a Special Action, choose one of the following options.',
            'Regain 1D6 lost Damage.',
            'Move immediately up to 10 inches in any direction and choose any facing. On a Crew Quality 10 check, also create two dummy Techno Mage ships. The real ship need not be identified. Dummies move and take damage normally, but cannot attack or use Special Actions. Remove a dummy if it is destroyed or moves more than 20 inches from the real ship. Remove both dummies when the real ship attacks or uses another Special Action.',
            "Use the Shadows' Jump Engine Disruptor special rule at a range of 12 inches.",
            'Prepare to deflect Beam attacks. When attacked by a Beam weapon, make a Crew Quality 9 check. On success, reflect the attack back at the attacker and resolve its Damage normally. Increase the target number by 1 after each Beam weapon successfully reflected.',
        ],
        'weapons': [
            ('Energy Blast', '18', 'F', 2, 'Precise, Super AP, Triple Damage'),
        ],
    },
]
