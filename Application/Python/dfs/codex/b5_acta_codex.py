"""
DFS Babylon 5 ACTA Codex
Version 1.3

Primary Sources
---------------
Babylon 5: A Call to Arms Second Edition Rulebook
Babylon 5: A Call to Arms Second Edition Fleet Lists
Powers and Principalities
Official FAQ and published updates

Purpose
-------
Single authoritative rules source for generated DFS reference material.

Version 1.1 adds fighter substitution and conversion rules, searchable keywords,
and related-rule metadata.
"""

from __future__ import annotations

import re
from typing import Any


SHIP_TRAITS = {'Adaptive Armour': {'title': 'Adaptive Armour',
                     'category': 'Ship Trait',
                     'text': 'Halve the Damage and Crew loss caused by each separate '
                             'attack, rounding down to a minimum loss of 1. Each weapon '
                             'system or other single source counts as a separate attack.',
                     'source': 'B5 ACTA Second Edition Rulebook, p. 16',
                     'keywords': ['Adaptive Armour',
                                  'Ship Trait',
                                  'attack',
                                  'loss',
                                  'separate',
                                  'caused',
                                  'counts',
                                  'crew',
                                  'damage',
                                  'down'],
                     'see_also': ['Double Damage', 'Triple Damage', 'Quad Damage']},
 'Advanced Anti-Fighter': {'title': 'Advanced Anti-Fighter',
                           'category': 'Ship Trait',
                           'text': 'Use the normal Anti-Fighter rules, but add +1 to every '
                                   'Anti-Fighter die roll.',
                           'source': 'B5 ACTA Second Edition Rulebook, p. 16',
                           'keywords': ['Advanced Anti-Fighter',
                                        'Ship Trait',
                                        'anti-fighter',
                                        'normal',
                                        'roll'],
                           'see_also': ['Anti-Fighter', 'Fighter']},
 'Advanced Jump Engine': {'title': 'Advanced Jump Engine',
                          'category': 'Ship Trait',
                          'text': 'When this ship enters realspace, its jump point does '
                                  'not deviate and it may act normally that turn. A jump '
                                  'point created in realspace may be placed in any fire '
                                  'arc. Other arriving ships may act normally only if they '
                                  'also have Advanced Jump Engine.',
                          'source': 'B5 ACTA Second Edition Rulebook, p. 16',
                          'keywords': ['Advanced Jump Engine',
                                       'Ship Trait',
                                       'jump',
                                       'normally',
                                       'point',
                                       'realspace',
                                       'advanced',
                                       'also',
                                       'arriving',
                                       'created'],
                          'see_also': ['Jump Engine']},
 'Afterburner': {'title': 'Afterburner',
                 'category': 'Ship Trait',
                 'text': 'When using the All Power to Engines! Special Action, this ship '
                         'doubles its Speed for the turn instead of receiving the normal '
                         'increase.',
                 'source': 'B5 ACTA Second Edition Rulebook, p. 16',
                 'keywords': ['Afterburner',
                              'Ship Trait',
                              'action',
                              'doubles',
                              'engines',
                              'increase',
                              'instead',
                              'normal',
                              'power',
                              'receiving'],
                 'see_also': []},
 'Agile': {'title': 'Agile',
           'category': 'Ship Trait',
           'text': 'The ship need only move one quarter of its Speed in a straight line '
                   'before making its first turn, and only 1 inch before making each '
                   'subsequent turn.',
           'source': 'B5 ACTA Second Edition Rulebook, p. 16',
           'keywords': ['Agile',
                        'Ship Trait',
                        'before',
                        'making',
                        'only',
                        'turn',
                        'first',
                        'inch',
                        'line',
                        'move'],
           'see_also': []},
 'Anti-Fighter': {'title': 'Anti-Fighter',
                  'category': 'Ship Trait',
                  'text': 'When an enemy fighter flight moves into base contact, roll a '
                          'number of Attack Dice equal to the Anti-Fighter score before '
                          'the dogfight is resolved. Each die that rolls 4 or more '
                          'destroys the fighter flight. Anti-Fighter may be used once per '
                          'turn.',
                  'source': 'B5 ACTA Second Edition Rulebook, pp. 16, 28',
                  'keywords': ['Anti-Fighter',
                               'Ship Trait',
                               'anti-fighter',
                               'fighter',
                               'flight',
                               'attack',
                               'base',
                               'before',
                               'contact',
                               'destroys'],
                  'see_also': ['Advanced Anti-Fighter', 'Fighter', 'Escort']},
 'Atmospheric': {'title': 'Atmospheric',
                 'category': 'Ship Trait',
                 'text': 'This ship may enter a planetary atmosphere and take part in '
                         'planetary assaults, including attacking ground targets and '
                         'landing troops where the relevant rules allow.',
                 'source': 'B5 ACTA Second Edition Rulebook, pp. 16, 39',
                 'keywords': ['Atmospheric',
                              'Ship Trait',
                              'planetary',
                              'allow',
                              'assaults',
                              'atmosphere',
                              'attacking',
                              'enter',
                              'ground',
                              'including'],
                 'see_also': ['Orbital Bomb', 'Shuttles']},
 'Breaching Pod': {'title': 'Breaching Pod',
                   'category': 'Ship Trait',
                   'text': 'Counts as a Fighter but automatically loses any Dogfight, '
                           'cannot make planetary assaults, and cannot act as an '
                           'interceptor. It carries one Troop; after moving into base '
                           'contact with a ship or station, that Troop fights first in the '
                           'boarding action.',
                   'source': 'B5 ACTA Second Edition Rulebook, p. 16',
                   'keywords': ['Breaching Pod',
                                'Ship Trait',
                                'cannot',
                                'troop',
                                'action',
                                'after',
                                'assaults',
                                'automatically',
                                'base',
                                'boarding'],
                   'see_also': ['Shuttles']},
 'Cargo': {'title': 'Cargo',
           'category': 'Ship Trait',
           'text': 'This is a scenario classification for a vessel carrying freight. It '
                   'has no standalone combat effect unless the scenario or '
                   'platform-specific rules state otherwise.',
           'source': 'B5 ACTA Fleet Lists, Other Craft, pp. 155-156',
           'keywords': ['Cargo',
                        'Ship Trait',
                        'scenario',
                        'carrying',
                        'classification',
                        'combat',
                        'effect',
                        'freight',
                        'otherwise',
                        'platform-specific'],
           'see_also': []},
 'Carrier': {'title': 'Carrier',
             'category': 'Ship Trait',
             'text': 'The ship may launch or recover a number of fighter flights in a turn '
                     'equal to its Carrier score, instead of the normal limit of one '
                     'flight.',
             'source': 'B5 ACTA Second Edition Rulebook, p. 16',
             'keywords': ['Carrier',
                          'Ship Trait',
                          'carrier',
                          'equal',
                          'fighter',
                          'flight',
                          'flights',
                          'instead',
                          'launch',
                          'limit'],
             'see_also': ['Fleet Carrier', 'Fighter']},
 'Command': {'title': 'Command',
             'category': 'Ship Trait',
             'text': 'While this ship is on the table and is neither Crippled nor reduced '
                     "to a Skeleton Crew, add its Command score to the fleet's Initiative. "
                     'Command bonuses are not cumulative.',
             'source': 'B5 ACTA Second Edition Rulebook, p. 17',
             'keywords': ['Command',
                          'Ship Trait',
                          'command',
                          'bonuses',
                          'crew',
                          'crippled',
                          'cumulative',
                          "fleet's",
                          'initiative',
                          'neither'],
             'see_also': []},
 'Dodge': {'title': 'Dodge',
           'category': 'Ship Trait',
           'text': 'Whenever the ship suffers a hit, roll one die. If the result equals or '
                   'exceeds its Dodge score, ignore the attack completely. A ship that is '
                   'Adrift, unable to move, or did not move in the Movement Phase cannot '
                   'use Dodge. Dodge does not protect against Energy Mines or Jump Points.',
           'source': 'B5 ACTA Second Edition Rulebook, p. 17',
           'keywords': ['Dodge',
                        'Ship Trait',
                        'dodge',
                        'move',
                        'adrift',
                        'against',
                        'attack',
                        'cannot',
                        'completely',
                        'does'],
           'see_also': ['Accurate', 'Energy Mine']},
 'Escort': {'title': 'Escort',
            'category': 'Ship Trait',
            'text': "Before any Anti-Fighter fire, divide this ship's Anti-Fighter dice "
                    'between itself and any allied ships within 8 inches and line of '
                    'sight. The assigned dice are then used by those ships for that turn.',
            'source': 'B5 ACTA Second Edition Rulebook, p. 17',
            'keywords': ['Escort',
                         'Ship Trait',
                         'anti-fighter',
                         'dice',
                         'allied',
                         'assigned',
                         'before',
                         'between',
                         'divide',
                         'fire'],
            'see_also': ['Anti-Fighter', 'Interceptors']},
 'Fighter': {'title': 'Fighter',
             'category': 'Ship Trait',
             'text': 'Fighter flights have no Damage or Crew score, are destroyed by the '
                     'first hit they suffer, and may never attempt Special Actions.',
             'source': 'B5 ACTA Second Edition Rulebook, p. 17',
             'keywords': ['Fighter',
                          'Ship Trait',
                          'actions',
                          'attempt',
                          'crew',
                          'damage',
                          'destroyed',
                          'fighter',
                          'first',
                          'flights'],
             'see_also': ['Carrier', 'Fleet Carrier', 'Dodge']},
 'Fleet Carrier': {'title': 'Fleet Carrier',
                   'category': 'Ship Trait',
                   'text': 'May deploy up to half its carried flights before battle. While '
                           'operational, all fighter flights in the fleet gain +1 '
                           'Dogfight. When a friendly fighter within 30 inches is removed, '
                           'roll 5+ to recover it for relaunch next turn; apply -1 if an '
                           'enemy ship was within 4 inches or it was lost in a dogfight, '
                           'and +1 if within 10 inches of the carrier. Only craft the '
                           'carrier could normally carry may be recovered. All benefits '
                           'are lost if the carrier is Crippled or on Skeleton Crew.',
                   'source': 'B5 ACTA Second Edition Rulebook, pp. 17-18',
                   'keywords': ['Fleet Carrier',
                                'Ship Trait',
                                'carrier',
                                'inches',
                                'within',
                                'dogfight',
                                'fighter',
                                'flights',
                                'lost',
                                'apply'],
                   'see_also': ['Carrier', 'Fighter']},
 'Flight Computer': {'title': 'Flight Computer',
                     'category': 'Ship Trait',
                     'text': 'Crew Quality can never fall below 4. The ship ignores all '
                             'penalties for being reduced to a Skeleton Crew, except that '
                             'Troops are still halved and Fleet Carrier is still lost.',
                     'source': 'B5 ACTA Second Edition Rulebook, p. 18',
                     'keywords': ['Flight Computer',
                                  'Ship Trait',
                                  'crew',
                                  'still',
                                  'being',
                                  'below',
                                  'carrier',
                                  'except',
                                  'fall',
                                  'halved'],
                     'see_also': []},
 'Gravitic Energy Grid': {'title': 'Gravitic Energy Grid',
                          'category': 'Ship Trait',
                          'text': 'Reduce the total Damage and Crew loss caused by each '
                                  'separate weapon attack by the Gravitic Energy Grid '
                                  'score. Damage and special effects from Critical Hits '
                                  'are never reduced.',
                          'source': 'B5 ACTA Second Edition Rulebook, p. 18',
                          'keywords': ['Gravitic Energy Grid',
                                       'Ship Trait',
                                       'damage',
                                       'attack',
                                       'caused',
                                       'crew',
                                       'critical',
                                       'effects',
                                       'energy',
                                       'gravitic'],
                          'see_also': ['Shields', 'Adaptive Armour']},
 'Huge Hangars': {'title': 'Huge Hangars',
                  'category': 'Ship Trait',
                  'text': 'Carries a number of Drakh Light Raiders, Heavy Raiders, or '
                          'Scouts equal to the listed score. They cannot begin deployed, '
                          'but launch and recover as fighters and yield Victory Points '
                          'normally if destroyed. An Amu Mothership may instead use 8 '
                          'slots for each Cruiser or Strike Cruiser, or 2 slots for each '
                          'Fast Destroyer, Light Cruiser, or Patrol Cruiser.',
                  'source': 'B5 ACTA Fleet Lists, The Drakh, p. 144',
                  'keywords': ['Huge Hangars',
                               'Ship Trait',
                               'cruiser',
                               'light',
                               'raiders',
                               'slots',
                               'begin',
                               'cannot',
                               'carries',
                               'deployed'],
                  'see_also': []},
 'Interceptors': {'title': 'Interceptors',
                  'category': 'Ship Trait',
                  'text': 'Against the first incoming hit of the turn, roll a number of '
                          'dice equal to the Interceptor score; any result of 2+ cancels '
                          'that hit. Successful dice are rolled against the next hit '
                          'needing 3+, then 4+, and so on. Failed dice are discarded. Once '
                          'the required number reaches 6+, it remains 6+ for the rest of '
                          'the turn. Interceptors refresh at the start of the next turn.',
                  'source': 'B5 ACTA Second Edition Rulebook, p. 18',
                  'keywords': ['Interceptors',
                               'Ship Trait',
                               'dice',
                               'turn',
                               'against',
                               'next',
                               'cancels',
                               'discarded',
                               'equal',
                               'failed'],
                  'see_also': ['Beam', 'Mini-Beam', 'Energy Mine']},
 'Jump Engine': {'title': 'Jump Engine',
                 'category': 'Ship Trait',
                 'text': 'The ship may use the Initiate Jump Point! Special Action to '
                         'enter or leave hyperspace. Follow the hyperspace and jump-point '
                         'rules when placing the jump point, checking for deviation, and '
                         'moving ships through it.',
                 'source': 'B5 ACTA Second Edition Rulebook, pp. 18, 26-27',
                 'keywords': ['Jump Engine',
                              'Ship Trait',
                              'hyperspace',
                              'jump',
                              'point',
                              'action',
                              'checking',
                              'deviation',
                              'enter',
                              'follow'],
                 'see_also': ['Advanced Jump Engine']},
 'Lumbering': {'title': 'Lumbering',
               'category': 'Ship Trait',
               'text': 'The ship may make only one turn during its movement, regardless of '
                       'the number of turns shown in its profile.',
               'source': 'B5 ACTA Second Edition Rulebook, p. 19',
               'keywords': ['Lumbering',
                            'Ship Trait',
                            'during',
                            'make',
                            'movement',
                            'only',
                            'profile',
                            'regardless',
                            'shown',
                            'turn'],
               'see_also': []},
 'Passenger Vessel': {'title': 'Passenger Vessel',
                      'category': 'Ship Trait',
                      'text': 'This is a scenario classification for a civilian vessel '
                              'carrying passengers. It has no standalone combat effect '
                              'unless the scenario or platform-specific rules state '
                              'otherwise.',
                      'source': 'B5 ACTA Fleet Lists, Other Craft, pp. 155-156',
                      'keywords': ['Passenger Vessel',
                                   'Ship Trait',
                                   'scenario',
                                   'carrying',
                                   'civilian',
                                   'classification',
                                   'combat',
                                   'effect',
                                   'otherwise',
                                   'passengers'],
                      'see_also': []},
 'Psychic Crew': {'title': 'Psychic Crew',
                  'category': 'Ship Trait',
                  'text': 'Ships may use Cause Confusion, making an opposed check with '
                          'Psychic Crew instead of Crew Quality; if successful, the target '
                          'is forced to move and act as directed by that rule. Fighters '
                          'cannot use the action, but retain Dodge 4+ against Anti-Fighter '
                          'attacks and survive elimination in a dogfight on 4+, making the '
                          'dogfight a draw. Ships may also trigger Shadow Telepathic '
                          'Disruption using this score.',
                  'source': 'B5 ACTA Fleet Lists, The Psi Corps, p. 151',
                  'keywords': ['Psychic Crew',
                               'Ship Trait',
                               'crew',
                               'dogfight',
                               'making',
                               'action',
                               'against',
                               'also',
                               'anti-fighter',
                               'attacks'],
                  'see_also': []},
 'Scout': {'title': 'Scout',
           'category': 'Ship Trait',
           'text': 'At the start of the Attack Phase, a Scout within 36 inches may pass a '
                   "Crew Quality check of 8+ to reduce one target's Stealth by 1 for the "
                   'turn, or to let one non-Beam, non-Energy Mine, non-Twin-Linked weapon '
                   'system attacking that target re-roll all failed Attack Dice.',
           'source': 'B5 ACTA Second Edition Rulebook, p. 19',
           'keywords': ['Scout',
                        'Ship Trait',
                        'attack',
                        'attacking',
                        'check',
                        'crew',
                        'dice',
                        'failed',
                        'inches',
                        'mine'],
           'see_also': ['Stealth']},
 'Self-Repair': {'title': 'Self-Repair',
                 'category': 'Ship Trait',
                 'text': 'In the End Phase, regain Damage equal to the listed Self-Repair '
                         "score, up to the ship's starting Damage. A ship that has become "
                         'Crippled remains Crippled even if later repairs take it above '
                         'the threshold.',
                 'source': 'B5 ACTA Fleet Lists, The Shadows; based on Self-Repairing '
                           'rules',
                 'keywords': ['Self-Repair',
                              'Ship Trait',
                              'crippled',
                              'damage',
                              'above',
                              'become',
                              'equal',
                              'even',
                              'later',
                              'listed'],
                 'see_also': ['Self-Repairing']},
 'Self-Repairing': {'title': 'Self-Repairing',
                    'category': 'Ship Trait',
                    'text': 'Add +1 to all Damage Control checks. In each End Phase while '
                            'below starting Damage, regain Damage equal to the '
                            'Self-Repairing score, up to the starting total. Once '
                            'Crippled, the ship remains Crippled even if repaired above '
                            'the threshold.',
                    'source': 'B5 ACTA Second Edition Rulebook, p. 19',
                    'keywords': ['Self-Repairing',
                                 'Ship Trait',
                                 'damage',
                                 'crippled',
                                 'starting',
                                 'above',
                                 'below',
                                 'checks',
                                 'control',
                                 'equal'],
                    'see_also': ['Self-Repair']},
 'Shields': {'title': 'Shields',
             'category': 'Ship Trait',
             'text': 'The first value is the number of hits the shield can absorb. Double, '
                     'Triple, and Quad Damage hits remove 2, 3, or 4 shield points. Excess '
                     'hits pass to the hull. The second value is regenerated automatically '
                     'in each End Phase. Shields cease functioning while the ship is '
                     'Crippled.',
             'source': 'B5 ACTA Second Edition Rulebook, p. 19',
             'keywords': ['Shields',
                          'Ship Trait',
                          'hits',
                          'shield',
                          'value',
                          'absorb',
                          'automatically',
                          'cease',
                          'crippled',
                          'damage'],
             'see_also': ['Interceptors', 'Gravitic Energy Grid', 'Adaptive Armour']},
 'Shuttles': {'title': 'Shuttles',
              'category': 'Ship Trait',
              'text': 'The listed score is the number of Troops this ship may land on a '
                      'planet in one turn during a planetary assault.',
              'source': 'B5 ACTA Second Edition Rulebook, p. 19',
              'keywords': ['Shuttles',
                           'Ship Trait',
                           'assault',
                           'during',
                           'land',
                           'listed',
                           'planet',
                           'planetary',
                           'troops',
                           'turn'],
              'see_also': []},
 'Stealth': {'title': 'Stealth',
             'category': 'Ship Trait',
             'text': 'After declaring attacks against this ship, the attacker must roll at '
                     'least the listed Stealth score to lock on. Apply the normal '
                     'modifiers for range, Scouts, and other effects. If the lock-on roll '
                     'fails, those weapons may not attack another target.',
             'source': 'B5 ACTA Second Edition Rulebook, p. 19',
             'keywords': ['Stealth',
                          'Ship Trait',
                          'roll',
                          'after',
                          'against',
                          'another',
                          'apply',
                          'attack',
                          'attacker',
                          'attacks'],
             'see_also': ['Scout']},
 'Unique': {'title': 'Unique',
            'category': 'Ship Trait',
            'text': 'Only one ship with this specific profile may be included in a fleet.',
            'source': 'B5 ACTA Second Edition Rulebook, p. 20',
            'keywords': ['Unique', 'Ship Trait', 'included', 'only', 'profile', 'specific'],
            'see_also': []}}

WEAPON_TRAITS = {'AP': {'title': 'AP',
        'category': 'Weapon Trait',
        'text': 'Add +1 to every Attack Dice result rolled for this weapon.',
        'source': 'B5 ACTA Second Edition Rulebook, p. 20',
        'keywords': ['AP', 'Weapon Trait', 'attack', 'dice', 'result', 'rolled'],
        'see_also': ['Super AP']},
 'Accurate': {'title': 'Accurate',
              'category': 'Weapon Trait',
              'text': "This weapon ignores the target's Dodge score.",
              'source': 'B5 ACTA Second Edition Rulebook, p. 20',
              'keywords': ['Accurate', 'Weapon Trait', 'dodge', 'ignores', "target's"],
              'see_also': ['Dodge']},
 'Beam': {'title': 'Beam',
          'category': 'Weapon Trait',
          'text': 'This weapon always hits on a roll of 4 or more, regardless of Hull. '
                  'Each successful Attack Dice is rolled again and may continue scoring '
                  'additional hits while it keeps rolling 4 or more. Beam weapons ignore '
                  'Interceptors and may split fire only between targets within 4 inches of '
                  'one another.',
          'source': 'B5 ACTA Second Edition Rulebook, p. 20',
          'keywords': ['Beam',
                       'Weapon Trait',
                       'hits',
                       'more',
                       'additional',
                       'again',
                       'always',
                       'another',
                       'attack',
                       'beam'],
          'see_also': ['Mini-Beam', 'Interceptors']},
 'Comms Disruptor': {'title': 'Comms Disruptor',
                     'category': 'Weapon Trait',
                     'text': 'A successful hit causes no damage. Instead, the target '
                             'suffers a -2 penalty to all Crew Quality checks for the rest '
                             'of the current turn and all of the next turn. While '
                             'affected, it must also pass a Crew Quality check against '
                             'Difficulty 8 to attempt any Special Action.',
                     'source': 'B5 ACTA Fleet Lists, Abbai Matriarchy, p. 90',
                     'keywords': ['Comms Disruptor',
                                  'Weapon Trait',
                                  'crew',
                                  'quality',
                                  'turn',
                                  'action',
                                  'affected',
                                  'against',
                                  'also',
                                  'attempt'],
                     'see_also': []},
 'Double Damage': {'title': 'Double Damage',
                   'category': 'Weapon Trait',
                   'text': 'Double all Damage caused, including bonus Damage from Critical '
                           'Hits. A Bulkhead Hit still causes 1 point of Damage.',
                   'source': 'B5 ACTA Second Edition Rulebook, p. 20',
                   'keywords': ['Double Damage',
                                'Weapon Trait',
                                'damage',
                                'bonus',
                                'bulkhead',
                                'caused',
                                'causes',
                                'critical',
                                'double',
                                'hits'],
                   'see_also': ['Triple Damage', 'Quad Damage']},
 'Energy Mine': {'title': 'Energy Mine',
                 'category': 'Weapon Trait',
                 'text': "Choose a point in range and in the weapon's fire arc. Every "
                         'object within 3 inches is attacked automatically. The attack '
                         'ignores Interceptors and Dodge, converts all Critical Hits to '
                         'Solid Hits, and may not be split.',
                 'source': 'B5 ACTA Second Edition Rulebook, p. 20',
                 'keywords': ['Energy Mine',
                              'Weapon Trait',
                              'hits',
                              'attack',
                              'attacked',
                              'automatically',
                              'choose',
                              'converts',
                              'critical',
                              'dodge'],
                 'see_also': ['Dodge', 'Interceptors']},
 'Gravitic Shifter': {'title': 'Gravitic Shifter',
                      'category': 'Weapon Trait',
                      'text': 'This weapon has no Attack Dice. Nominate an enemy in range '
                              'and arc, then make opposed Crew Quality checks. If the '
                              'attacker wins, the target may immediately be turned up to '
                              '45 degrees in either direction.',
                      'source': 'B5 ACTA Second Edition Rulebook, p. 20',
                      'keywords': ['Gravitic Shifter',
                                   'Weapon Trait',
                                   'attack',
                                   'attacker',
                                   'checks',
                                   'crew',
                                   'degrees',
                                   'dice',
                                   'direction',
                                   'either'],
                      'see_also': []},
 'Mass Driver': {'title': 'Mass Driver',
                 'category': 'Weapon Trait',
                 'text': 'May attack only planetary targets, Immobile ships, ships Running '
                         'Adrift, or ships that have not moved during the current turn. It '
                         'ignores Interceptors, Shields, and Gravitic Energy Grids.',
                 'source': 'B5 ACTA Second Edition Rulebook, p. 20',
                 'keywords': ['Mass Driver',
                              'Weapon Trait',
                              'adrift',
                              'attack',
                              'current',
                              'during',
                              'energy',
                              'gravitic',
                              'grids',
                              'ignores'],
                 'see_also': ['Orbital Bomb', 'Slow-Loading']},
 'Mini-Beam': {'title': 'Mini-Beam',
               'category': 'Weapon Trait',
               'text': 'Always hits on a roll of 4 or more regardless of Hull and ignores '
                       'Interceptors. Unlike a Beam weapon, successful Attack Dice are not '
                       'rolled again for additional hits.',
               'source': 'B5 ACTA Second Edition Rulebook, p. 20',
               'keywords': ['Mini-Beam',
                            'Weapon Trait',
                            'hits',
                            'additional',
                            'again',
                            'always',
                            'attack',
                            'beam',
                            'dice',
                            'hull'],
               'see_also': ['Beam', 'Interceptors']},
 'One-Shot': {'title': 'One-Shot',
              'category': 'Weapon Trait',
              'text': 'After this weapon is used in an attack, it cannot be used again for '
                      'the rest of the game. If it fails to lock on to a Stealth target, '
                      'it does not count as fired.',
              'source': 'B5 ACTA Second Edition Rulebook, p. 20',
              'keywords': ['One-Shot',
                           'Weapon Trait',
                           'used',
                           'after',
                           'again',
                           'attack',
                           'cannot',
                           'count',
                           'does',
                           'fails'],
              'see_also': ['Slow-Loading']},
 'Orbital Bomb': {'title': 'Orbital Bomb',
                  'category': 'Weapon Trait',
                  'text': 'May be fired only at planetary targets and may attack '
                          'emplacements and/or troops.',
                  'source': 'B5 ACTA Second Edition Rulebook, p. 21',
                  'keywords': ['Orbital Bomb',
                               'Weapon Trait',
                               'attack',
                               'emplacements',
                               'fired',
                               'only',
                               'planetary',
                               'targets',
                               'troops'],
                  'see_also': ['Mass Driver', 'Atmospheric']},
 'Precise': {'title': 'Precise',
             'category': 'Weapon Trait',
             'text': 'Add +1 to every roll made on the Attack Table for this weapon.',
             'source': 'B5 ACTA Second Edition Rulebook, p. 21',
             'keywords': ['Precise', 'Weapon Trait', 'attack', 'made', 'roll', 'table'],
             'see_also': []},
 'Quad Damage': {'title': 'Quad Damage',
                 'category': 'Weapon Trait',
                 'text': 'Quadruple all Damage caused. A Bulkhead Hit still causes at '
                         'least 2 points of Damage.',
                 'source': 'B5 ACTA Second Edition Rulebook, p. 21',
                 'keywords': ['Quad Damage',
                              'Weapon Trait',
                              'damage',
                              'bulkhead',
                              'caused',
                              'causes',
                              'least',
                              'points',
                              'quadruple',
                              'still'],
                 'see_also': ['Double Damage', 'Triple Damage']},
 'Slow-Loading': {'title': 'Slow-Loading',
                  'category': 'Weapon Trait',
                  'text': 'This weapon may fire only every other turn. If it fails to lock '
                          'on to a Stealth target, it does not count as fired.',
                  'source': 'B5 ACTA Second Edition Rulebook, p. 21',
                  'keywords': ['Slow-Loading',
                               'Weapon Trait',
                               'count',
                               'does',
                               'fails',
                               'fire',
                               'fired',
                               'lock',
                               'only',
                               'other'],
                  'see_also': ['One-Shot']},
 'Super AP': {'title': 'Super AP',
              'category': 'Weapon Trait',
              'text': 'Add +2 to every Attack Dice result rolled for this weapon.',
              'source': 'B5 ACTA Second Edition Rulebook, p. 21',
              'keywords': ['Super AP',
                           'Weapon Trait',
                           'attack',
                           'dice',
                           'result',
                           'rolled'],
              'see_also': ['AP']},
 'Triple Damage': {'title': 'Triple Damage',
                   'category': 'Weapon Trait',
                   'text': 'Triple all Damage caused. A Bulkhead Hit still causes at least '
                           '1 point of Damage.',
                   'source': 'B5 ACTA Second Edition Rulebook, p. 21',
                   'keywords': ['Triple Damage',
                                'Weapon Trait',
                                'damage',
                                'bulkhead',
                                'caused',
                                'causes',
                                'least',
                                'point',
                                'still',
                                'triple'],
                   'see_also': ['Double Damage', 'Quad Damage']},
 'Twin-Linked': {'title': 'Twin-Linked',
                 'category': 'Weapon Trait',
                 'text': 'Any Attack Dice from this weapon that fail to hit may be '
                         're-rolled.',
                 'source': 'B5 ACTA Second Edition Rulebook, p. 21',
                 'keywords': ['Twin-Linked',
                              'Weapon Trait',
                              'attack',
                              'dice',
                              'fail',
                              're-rolled'],
                 'see_also': ['Scout']},
 'Weak': {'title': 'Weak',
          'category': 'Weapon Trait',
          'text': 'Apply -1 to every Attack Dice result rolled for this weapon.',
          'source': 'B5 ACTA Second Edition Rulebook, p. 21',
          'keywords': ['Weak',
                       'Weapon Trait',
                       'apply',
                       'attack',
                       'dice',
                       'result',
                       'rolled'],
          'see_also': []}}

NAMED_RULES = {}

FLEET_RULES = {'Abbai Matriarchy': [],
 'Brakiri Syndicracy': [{'title': 'Fighter Replacements',
                         'text': 'Any ship carrying one or more Falkosi flights may '
                                 'replace any number of them with Pikatos flights or '
                                 'Breaching Pods. Breaching Pods taken this way carry one '
                                 'Troop from the parent ship and do not include Troops of '
                                 'their own.',
                         'source': 'B5 ACTA Fleet Lists, The Brakiri Syndicracy, p. 99',
                         'keywords': ['fighters',
                                      'Falkosi',
                                      'Pikatos',
                                      'Breaching Pods',
                                      'replacement',
                                      'Troops'],
                         'see_also': ['Breaching Pod', 'Fighter'],
                         'category': 'Fleet Rule'}],
 'Centauri Republic': [{'title': 'Fighting Narn',
                        'text': 'Centauri vessels will never surrender to the Narn and are '
                                'immune to effects that would require them to surrender to '
                                'Narn vessels, including Stand Down and Prepare to be '
                                'Boarded!',
                        'source': 'B5 ACTA Fleet Lists, The Centauri Republic, p. 71',
                        'category': 'Fleet Rule',
                        'keywords': ['Fighting Narn',
                                     'Fleet Rule',
                                     'narn',
                                     'surrender',
                                     'vessels',
                                     'boarded',
                                     'centauri',
                                     'down',
                                     'effects',
                                     'immune'],
                        'see_also': []},
                       {'title': 'Mass Drivers',
                        'text': 'A Primus may replace 5 AD of its forward Ion Cannon with '
                                'one Mass Driver. An Octurion may replace 8 AD of its '
                                'forward Ion Cannon with two Mass Drivers. Each Mass '
                                'Driver has Range 10, Fore arc, 8 AD, and the Mass Driver, '
                                'Slow-Loading, Super AP, and Triple Damage traits.',
                        'source': 'B5 ACTA Fleet Lists, The Centauri Republic, p. 71',
                        'category': 'Fleet Rule',
                        'keywords': ['Mass Drivers',
                                     'Fleet Rule',
                                     'mass',
                                     'driver',
                                     'cannon',
                                     'forward',
                                     'replace',
                                     'damage',
                                     'drivers',
                                     'fore'],
                        'see_also': []},
                       {'title': 'Fighter Replacements',
                        'text': 'Any ship carrying one or more Sentri flights may replace '
                                'any number of them with Razik flights or Breaching Pods. '
                                'Breaching Pods taken this way carry one Troop from the '
                                'parent ship and do not include Troops of their own. '
                                'Rutarians may be bought separately, or up to four Sentri '
                                'flights may be replaced by Rutarians as one Patrol '
                                'choice.',
                        'source': 'B5 ACTA Fleet Lists, The Centauri Republic, p. 71',
                        'keywords': ['fighters',
                                     'Sentri',
                                     'Razik',
                                     'Rutarian',
                                     'Breaching Pods',
                                     'replacement'],
                        'see_also': ['Breaching Pod', 'Fighter'],
                        'category': 'Fleet Rule'}],
 'Dilgar Imperium': [{'title': 'Pentacon Formations',
                      'text': 'Dilgar ships may form squadrons of up to five ships. A '
                              'five-ship Pentacon may, once per turn when selected to '
                              'move, force an enemy ship to move instead. The Pentacon '
                              'must still move before the turn ends. At three or fewer '
                              'ships it becomes a normal squadron.',
                      'source': 'B5 ACTA Fleet Lists, The Dilgar Imperium, p. 40',
                      'category': 'Fleet Rule',
                      'keywords': ['Pentacon Formations',
                                   'Fleet Rule',
                                   'move',
                                   'pentacon',
                                   'turn',
                                   'becomes',
                                   'before',
                                   'dilgar',
                                   'ends',
                                   'enemy'],
                      'see_also': []},
                     {'title': 'Fighter Support',
                      'text': 'A Dilgar fighter flight may support a dogfight within 2 '
                              'inches as though in base contact, provided the Dilgar '
                              'flight in the dogfight moved into contact with the enemy '
                              'this turn. A supporting flight may not attack normally and '
                              'counts as involved in the dogfight.',
                      'source': 'B5 ACTA Fleet Lists, The Dilgar Imperium, p. 40',
                      'category': 'Fleet Rule',
                      'keywords': ['Fighter Support',
                                   'Fleet Rule',
                                   'dogfight',
                                   'flight',
                                   'contact',
                                   'dilgar',
                                   'attack',
                                   'base',
                                   'counts',
                                   'enemy'],
                      'see_also': []},
                     {'title': 'Suicide Fighters',
                      'text': 'In battles set in 2232, a Thorun Dartfighter flight may '
                              'move into contact with an enemy ship and intentionally '
                              'crash. The flight is destroyed at the start of the Attack '
                              'Phase and awards no Victory Points; the target suffers a 1 '
                              'AD attack with Super AP and Triple Damage.',
                      'source': 'B5 ACTA Fleet Lists, The Dilgar Imperium, p. 40',
                      'category': 'Fleet Rule',
                      'keywords': ['Suicide Fighters',
                                   'Fleet Rule',
                                   'attack',
                                   'flight',
                                   'awards',
                                   'battles',
                                   'contact',
                                   'crash',
                                   'damage',
                                   'dartfighter'],
                      'see_also': []},
                     {'title': 'Fighter Replacements',
                      'text': 'Any ship carrying one or more Thorun Dartfighter flights '
                              'may replace any number of them with Thorun Torpedofighter '
                              'flights or Breaching Pods. Breaching Pods taken this way '
                              'carry one Troop from the parent ship and do not include '
                              'Troops of their own.',
                      'source': 'B5 ACTA Fleet Lists, The Dilgar Imperium, p. 40',
                      'keywords': ['fighters',
                                   'Thorun Dartfighter',
                                   'Thorun Torpedofighter',
                                   'Breaching Pods',
                                   'replacement'],
                      'see_also': ['Breaching Pod', 'Fighter'],
                      'category': 'Fleet Rule'}],
 'Drazi Freehold': [{'title': 'Aggression',
                     'text': 'Drazi receive +1 on Crew Quality checks for Give Me Ramming '
                             'Speed! and Stand Down and Prepare to be Boarded!, whether '
                             'they are initiating or resisting the action.',
                     'source': 'B5 ACTA Fleet Lists, The Drazi Freehold, p. 105',
                     'category': 'Fleet Rule',
                     'keywords': ['Aggression',
                                  'Fleet Rule',
                                  'action',
                                  'boarded',
                                  'checks',
                                  'crew',
                                  'down',
                                  'drazi',
                                  'give',
                                  'initiating'],
                     'see_also': []},
                    {'title': 'Sky Hook Catapult',
                     'text': 'When a ship deploys Sky Serpents, place them up to 8 inches '
                             'away in its Fore arc. Star Snakes deploy normally.',
                     'source': 'B5 ACTA Fleet Lists, The Drazi Freehold, p. 105',
                     'category': 'Fleet Rule',
                     'keywords': ['Sky Hook Catapult',
                                  'Fleet Rule',
                                  'away',
                                  'deploy',
                                  'deploys',
                                  'fore',
                                  'inches',
                                  'normally',
                                  'place',
                                  'serpents'],
                     'see_also': []},
                    {'title': 'Tactics — Quick & Decisive',
                     'text': 'The Drazi Initiative bonus is +2 when the fleet is the '
                             'attacker. It is +1 when the fleet is the defender or when '
                             'the scenario does not specify an attacker and defender.',
                     'source': 'B5 ACTA Fleet Lists, The Drazi Freehold, p. 105',
                     'category': 'Fleet Rule',
                     'keywords': ['Tactics — Quick & Decisive',
                                  'Fleet Rule',
                                  'attacker',
                                  'defender',
                                  'bonus',
                                  'does',
                                  'drazi',
                                  'initiative',
                                  'scenario',
                                  'specify'],
                     'see_also': []},
                    {'title': 'Fighter Replacements',
                     'text': 'Any ship carrying one or more Star Snake flights may replace '
                             'any number of them with Breaching Pods. Breaching Pods taken '
                             'this way carry one Troop from the parent ship and do not '
                             'include Troops of their own.',
                     'source': 'B5 ACTA Fleet Lists, The Drazi Freehold, p. 105',
                     'keywords': ['fighters',
                                  'Star Snake',
                                  'Breaching Pods',
                                  'replacement',
                                  'Troops'],
                     'see_also': ['Breaching Pod', 'Fighter'],
                     'category': 'Fleet Rule'}],
 'Earth Alliance - Crusade Era': [{'title': 'Fighter Replacements',
                                   'text': 'Any ship carrying one or more Aurora Starfury '
                                           'flights may replace any number of them with '
                                           'Badgers, Thunderbolts, or Breaching Pods. '
                                           'Breaching Pods taken this way carry one Troop '
                                           'from the parent ship and do not include Troops '
                                           'of their own. Firebolts may be bought '
                                           'separately, or up to four other Starfury '
                                           'flights may be replaced by Firebolts as one '
                                           'Patrol choice.',
                                   'source': 'B5 ACTA Fleet Lists, Earth Alliance — The '
                                             'Crusade Era, p. 29',
                                   'keywords': ['fighters',
                                                'Aurora Starfury',
                                                'Badger',
                                                'Thunderbolt',
                                                'Firebolt',
                                                'Breaching Pods',
                                                'replacement'],
                                   'see_also': ['Breaching Pod', 'Fighter'],
                                   'category': 'Fleet Rule'}],
 'Earth Alliance - The Early Years': [{'title': 'Fighter Replacements',
                                       'text': 'A ship carrying Starfury flights may '
                                               'replace all of them with another type of '
                                               'Starfury, provided the replacement is in '
                                               'service for the scenario or campaign date. '
                                               'It may also replace any number of '
                                               'Starfuries with Breaching Pods. Breaching '
                                               'Pods taken this way carry one Troop from '
                                               'the parent ship and do not include Troops '
                                               'of their own.',
                                       'source': 'B5 ACTA Fleet Lists, Earth Alliance — '
                                                 'The Early Years, p. 7',
                                       'keywords': ['fighters',
                                                    'Starfury',
                                                    'Breaching Pods',
                                                    'replacement',
                                                    'in service'],
                                       'see_also': ['Breaching Pod', 'Fighter'],
                                       'category': 'Fleet Rule'}],
 'Earth Alliance - Third Age': [{'title': 'Fighter Replacements',
                                 'text': 'Any ship carrying one or more Aurora Starfury '
                                         'flights may replace any number of them with '
                                         'Badgers, Thunderbolts, where the scenario date '
                                         'permits, or Breaching Pods. Breaching Pods taken '
                                         'this way carry one Troop from the parent ship '
                                         'and do not include Troops of their own.',
                                 'source': 'B5 ACTA Fleet Lists, Earth Alliance — Dawn of '
                                           'the Third Age, p. 19',
                                 'keywords': ['fighters',
                                              'Aurora Starfury',
                                              'Badger',
                                              'Thunderbolt',
                                              'Breaching Pods',
                                              'replacement'],
                                 'see_also': ['Breaching Pod', 'Fighter'],
                                 'category': 'Fleet Rule'}],
 'Gaim Intelligence': [{'title': 'Assault Drones',
                        'text': 'When Gaim Troops attack during a boarding action or '
                                'planetary assault, roll two dice for each attack and use '
                                'the better result.',
                        'source': 'B5 ACTA Fleet Lists, The Gaim Intelligence, p. 112',
                        'category': 'Fleet Rule',
                        'keywords': ['Assault Drones',
                                     'Fleet Rule',
                                     'attack',
                                     'action',
                                     'assault',
                                     'better',
                                     'boarding',
                                     'dice',
                                     'during',
                                     'gaim'],
                        'see_also': []},
                       {'title': 'The Queens',
                        'text': 'Every Gaim fleet must include at least one Queen ship. '
                                'The Queen of the highest Priority Level is the Ruling '
                                'Queen, and only one Queen of that type may be present. '
                                'The Ruling Queen receives +1 Crew Quality. Each Gaim ship '
                                'uses the Crew Quality of the nearest Queen within 12 '
                                'inches.',
                        'source': 'Powers and Principalities, The Gaim Intelligence, p. 18',
                        'category': 'Fleet Rule',
                        'keywords': ['The Queens',
                                     'Fleet Rule',
                                     'queen',
                                     'crew',
                                     'gaim',
                                     'quality',
                                     'ruling',
                                     'highest',
                                     'inches',
                                     'include'],
                        'see_also': []},
                       {'title': 'Dynamic Squadrons',
                        'text': 'Gaim ships need not form squadrons before the battle. At '
                                'the start of a Movement Phase, eligible ships may declare '
                                'a squadron. It may remain together or disband in any End '
                                'Phase.',
                        'source': 'Powers and Principalities, The Gaim Intelligence, p. 18',
                        'category': 'Fleet Rule',
                        'keywords': ['Dynamic Squadrons',
                                     'Fleet Rule',
                                     'phase',
                                     'battle',
                                     'before',
                                     'declare',
                                     'disband',
                                     'eligible',
                                     'form',
                                     'gaim'],
                        'see_also': []},
                       {'title': 'Protect the Queen',
                        'text': 'If all Queen ships are lost, every remaining Gaim ship '
                                'immediately suffers -4 Crew Quality and the fleet '
                                'Initiative becomes -3. Enemy players receive double the '
                                'normal Victory Points for destroying a Queen ship.',
                        'source': 'Powers and Principalities, The Gaim Intelligence, p. 18',
                        'category': 'Fleet Rule',
                        'keywords': ['Protect the Queen',
                                     'Fleet Rule',
                                     'queen',
                                     'becomes',
                                     'crew',
                                     'destroying',
                                     'double',
                                     'enemy',
                                     'gaim',
                                     'immediately'],
                        'see_also': []},
                       {'title': 'Klikkita Conversion',
                        'text': 'A Klikkita flight may convert into a Klikkitak flight in '
                                'any End Phase, whether launched or still aboard its '
                                'parent ship. The change is permanent. Klikkitaks cannot '
                                'intercept fighters or Breaching Pods and cannot be '
                                'recovered by Fleet Carrier if destroyed.',
                        'source': 'B5 ACTA Fleet Lists, The Gaim Intelligence, p. 112',
                        'keywords': ['fighters',
                                     'Klikkita',
                                     'Klikkitak',
                                     'conversion',
                                     'Fleet Carrier',
                                     'interception'],
                        'see_also': ['Fighter', 'Fleet Carrier'],
                        'category': 'Fleet Rule'}],
 'Hurr': [],
 'Interstellar Alliance': [{'title': 'Allied Fleets',
                            'text': 'An ISA fleet may spend 1 Fleet Allocation Point from '
                                    'its allowance on ships from one of the following '
                                    'fleet lists: Earth Alliance (Third Age or Crusade '
                                    'Era), Narn Regime, Minbari Federation, or any League '
                                    'fleet. In campaign games, allied ships are limited to '
                                    'a maximum of 1 Battle-level Fleet Allocation Point at '
                                    'any one time.',
                            'source': 'B5 ACTA Fleet Lists, The Interstellar Alliance, p. '
                                      '82',
                            'keywords': ['Allied Fleets',
                                         'Fleet Rule',
                                         'allies',
                                         'Earth Alliance',
                                         'Narn',
                                         'Minbari',
                                         'League',
                                         'Fleet Allocation'],
                            'see_also': [],
                            'category': 'Fleet Rule'},
                           {'title': 'In Service Dates',
                            'text': 'The Interstellar Alliance fleet list may not be used '
                                    'in scenarios set before 2262, even though some '
                                    'individual ships existed earlier.',
                            'source': 'B5 ACTA Fleet Lists, The Interstellar Alliance, p. '
                                      '82',
                            'keywords': ['In Service Dates',
                                         'Fleet Rule',
                                         '2262',
                                         'scenario date',
                                         'fleet availability'],
                            'see_also': [],
                            'category': 'Fleet Rule'},
                           {'title': 'Rangers',
                            'text': 'All ISA ships receive +1 Crew Quality, to a maximum '
                                    'score of 6.',
                            'source': 'B5 ACTA Fleet Lists, The Interstellar Alliance, p. '
                                      '82',
                            'keywords': ['Rangers',
                                         'Fleet Rule',
                                         'Crew Quality',
                                         'bonus',
                                         'maximum 6'],
                            'see_also': [],
                            'category': 'Fleet Rule'},
                           {'title': 'Skin Dancing',
                            'text': 'Blue Stars, White Stars, White Star IIs, White Star '
                                    'Fighters, and all Minbari fighters may attempt Skin '
                                    'Dancing. Move into contact with the target; close '
                                    'escorts may intercept normally. Ships must pass a '
                                    'Crew Quality check of 9, while fighters must roll 5+. '
                                    'On a failure, the attacker is destroyed and the '
                                    'target suffers a Double Damage attack: 1 AD for a '
                                    "fighter, or AD equal to the ship's starting Damage "
                                    'for a ship. On success, the attacker may attack only '
                                    'that target for the rest of the turn, may use all '
                                    'weapons regardless of fire arc, and ignores '
                                    'Interceptors. The target may not fire back; other '
                                    'enemies may target the skin-dancing craft only with '
                                    'Accurate or Precise weapons.',
                            'source': 'B5 ACTA Fleet Lists, The Interstellar Alliance, pp. '
                                      '82-83',
                            'keywords': ['Skin Dancing',
                                         'Fleet Rule',
                                         'White Star',
                                         'Blue Star',
                                         'Minbari fighters',
                                         'Crew Quality',
                                         'Interceptors',
                                         'Accurate',
                                         'Precise'],
                            'see_also': ['Interceptors', 'Accurate', 'Precise'],
                            'category': 'Fleet Rule'},
                           {'title': 'Fighter Replacements',
                            'text': 'Any ship carrying one or more Starfury flights may '
                                    'replace any number of them with Thunderbolt Starfury '
                                    'flights.',
                            'source': 'B5 ACTA Fleet Lists, The Interstellar Alliance, p. '
                                      '82',
                            'keywords': ['Fighter Replacements',
                                         'Fleet Rule',
                                         'Starfury',
                                         'Thunderbolt',
                                         'replacement'],
                            'see_also': ['Fighter'],
                            'category': 'Fleet Rule'}],
 'Ipsha': [],
 'Lumati': [],
 'Minbari Federation': [{'title': 'Skin Dancing',
                         'text': 'Only Minbari fighters may attempt Skin Dancing. Move the '
                                 'fighter into contact with an enemy ship; close escorts '
                                 'may intercept normally. Roll one die: on 1-4 the fighter '
                                 'is destroyed and the target suffers a 1 AD Double Damage '
                                 'attack. On 5+, the fighter may attack only that ship '
                                 'this turn, may use all its weapons regardless of fire '
                                 'arc, and ignores the target’s Interceptors.',
                         'source': 'B5 ACTA Fleet Lists, The Minbari Federation, p. 49',
                         'category': 'Fleet Rule',
                         'keywords': ['Skin Dancing',
                                      'Fleet Rule',
                                      'fighter',
                                      'attack',
                                      'only',
                                      'attempt',
                                      'close',
                                      'contact',
                                      'damage',
                                      'dancing'],
                         'see_also': []},
                        {'title': 'Fighter Replacements',
                         'text': 'Any ship carrying one or more Nial flights may replace '
                                 'any number of them with Tishats, in scenarios set in '
                                 '2231 or later, or with Breaching Pods. Breaching Pods '
                                 'taken this way carry one Troop from the parent ship and '
                                 'do not include Troops of their own.',
                         'source': 'B5 ACTA Fleet Lists, The Minbari Federation, p. 49',
                         'keywords': ['fighters',
                                      'Nial',
                                      'Tishat',
                                      'Breaching Pods',
                                      'replacement',
                                      '2231'],
                         'see_also': ['Breaching Pod', 'Fighter'],
                         'category': 'Fleet Rule'}],
 'Narn Regime': [{'title': 'Fighting Centauri',
                  'text': 'Narn vessels will never surrender to the Centauri and are '
                          'immune to effects that would require them to surrender to '
                          'Centauri vessels, including Stand Down and Prepare to be '
                          'Boarded!',
                  'source': 'B5 ACTA Fleet Lists, The Narn Regime, p. 59',
                  'category': 'Fleet Rule',
                  'keywords': ['Fighting Centauri',
                               'Fleet Rule',
                               'centauri',
                               'surrender',
                               'vessels',
                               'boarded',
                               'down',
                               'effects',
                               'immune',
                               'including'],
                  'see_also': []},
                 {'title': 'Fighter Replacements',
                  'text': 'Any ship carrying one or more Frazi flights may replace any '
                          'number of them with Gorith flights or Breaching Pods. Breaching '
                          'Pods taken this way carry one Troop from the parent ship and do '
                          'not include Troops of their own.',
                  'source': 'B5 ACTA Fleet Lists, The Narn Regime, p. 59',
                  'keywords': ['fighters',
                               'Frazi',
                               'Gorith',
                               'Breaching Pods',
                               'replacement',
                               'Troops'],
                  'see_also': ['Breaching Pod', 'Fighter'],
                  'category': 'Fleet Rule'}],
 'Others': [],
 'Psi Corps': [{'title': 'Best of the Best',
                'text': 'All ships in a Psi Corps fleet receive +1 Crew Quality, to a '
                        'maximum score of 6.',
                'source': 'B5 ACTA Fleet Lists, The Psi Corps, p. 151',
                'category': 'Fleet Rule',
                'keywords': ['Best of the Best',
                             'Fleet Rule',
                             'corps',
                             'crew',
                             'maximum',
                             'quality',
                             'receive'],
                'see_also': []},
               {'title': 'EarthForce Requisition',
                'text': 'A Psi Corps fleet may spend up to 2 Fleet Allocation Points from '
                        'its allowance on ships from one Earth Alliance fleet list.',
                'source': 'B5 ACTA Fleet Lists, The Psi Corps, p. 151',
                'category': 'Fleet Rule',
                'keywords': ['EarthForce Requisition',
                             'Fleet Rule',
                             'alliance',
                             'allocation',
                             'allowance',
                             'corps',
                             'earth',
                             'list',
                             'points',
                             'spend'],
                'see_also': []}],
 'Raiders': [{'title': 'Allied Fleets',
              'text': 'A Raiders fleet may spend 1 Fleet Allocation Point from its '
                      'allowance on ships from one of these fleet lists: Abbai Matriarchy, '
                      'Brakiri Syndicracy, Drazi Freehold, Gaim Intelligence, pak’ma’ra, '
                      'or Vree Conglomerate.',
              'source': 'B5 ACTA Fleet Lists, The Raiders, p. 128',
              'category': 'Fleet Rule',
              'keywords': ['Allied Fleets',
                           'Fleet Rule',
                           'abbai',
                           'allocation',
                           'allowance',
                           'brakiri',
                           'conglomerate',
                           'drazi',
                           'freehold',
                           'gaim'],
              'see_also': []},
             {'title': 'Fighter Replacements',
              'text': 'Any ship carrying one or more Delta-V flights may replace any '
                      'number of them with Breaching Pods. Breaching Pods taken this way '
                      'carry one Troop from the parent ship and do not include Troops of '
                      'their own. Up to eight Delta-V flights carried by ships may be '
                      'replaced by Delta-V2 flights as one Patrol choice.',
              'source': 'B5 ACTA Fleet Lists, The Raiders, p. 128',
              'keywords': ['fighters',
                           'Delta-V',
                           'Delta-V2',
                           'Breaching Pods',
                           'replacement'],
              'see_also': ['Breaching Pod', 'Fighter'],
              'category': 'Fleet Rule'}],
 'Techno Mages': [],
 'The Ancients': [{'title': 'Priority Level',
                   'text': 'Ancient is a Priority Level above Armageddon. One Ancient ship '
                           'is equivalent to 2 Armageddon, 4 War, 8 Battle, 12 Raid, 18 '
                           'Skirmish, or 30 Patrol ships. Fleet Allocation Points may be '
                           'split normally.',
                   'source': 'B5 ACTA Fleet Lists, The Ancients, p. 140',
                   'category': 'Fleet Rule',
                   'keywords': ['Priority Level',
                                'Fleet Rule',
                                'Ancient',
                                'Armageddon',
                                'Fleet Allocation',
                                'Patrol',
                                'Skirmish',
                                'Raid',
                                'Battle',
                                'War'],
                   'see_also': []},
                  {'title': 'Initiative',
                   'text': 'A fleet consisting of Ancients has an Initiative score of +4.',
                   'source': 'B5 ACTA Fleet Lists, The Ancients, p. 140',
                   'category': 'Fleet Rule',
                   'keywords': ['Initiative', 'Fleet Rule', 'Ancients', '+4'],
                   'see_also': []},
                  {'title': 'Crew Quality',
                   'text': 'All Ancients are considered to have Crew Quality 7.',
                   'source': 'B5 ACTA Fleet Lists, The Ancients, p. 140',
                   'category': 'Fleet Rule',
                   'keywords': ['Crew Quality', 'Fleet Rule', 'Ancients', '7'],
                   'see_also': []},
                  {'title': 'Stealth Penetration',
                   'text': 'Ancient vessels ignore the Stealth score of every target.',
                   'source': 'B5 ACTA Fleet Lists, The Ancients, p. 140',
                   'category': 'Fleet Rule',
                   'keywords': ['Stealth Penetration',
                                'Fleet Rule',
                                'Ancients',
                                'Stealth',
                                'ignore'],
                   'see_also': ['Stealth']},
                  {'title': 'Redundant Systems',
                   'text': 'Ancient vessels take damage normally, but every Critical Hit '
                           'is automatically repaired in the End Phase of the following '
                           'turn. Critical Hits to Vital Systems are repaired at the same '
                           'time.',
                   'source': 'B5 ACTA Fleet Lists, The Ancients, p. 140',
                   'category': 'Fleet Rule',
                   'keywords': ['Redundant Systems',
                                'Fleet Rule',
                                'Ancients',
                                'Critical Hits',
                                'Vital Systems',
                                'repair',
                                'End Phase'],
                   'see_also': ['Self-Repairing']},
                  {'title': 'Crew',
                   'text': 'Ancient vessels have no Crew or Troops score. They cannot be '
                           'boarded or initiate boarding actions and are immune to '
                           'Critical Hits that affect Crew.',
                   'source': 'B5 ACTA Fleet Lists, The Ancients, p. 140',
                   'category': 'Fleet Rule',
                   'keywords': ['Crew',
                                'Fleet Rule',
                                'Ancients',
                                'Troops',
                                'boarding',
                                'Critical Hits',
                                'immune'],
                   'see_also': []}],
 'The Drakh': [],
 'The Shadows': [{'title': 'Hyperspace Mastery',
                  'text': 'Shadow vessels enter realspace without deviation, without an '
                          'allied ship already on the table, and without causing jump '
                          'point shock-wave damage. They may act normally on the turn they '
                          'arrive. To enter hyperspace they use Initiate Jump Point! but '
                          'place no jump point; remove the vessel at the start of its next '
                          'turn. Shadow fighters may enter or leave hyperspace the same '
                          'way without taking a Special Action.',
                  'source': 'B5 ACTA Fleet Lists, The Shadows, p. 137',
                  'category': 'Fleet Rule',
                  'keywords': ['Hyperspace Mastery',
                               'Fleet Rule',
                               'without',
                               'enter',
                               'jump',
                               'point',
                               'hyperspace',
                               'shadow',
                               'turn',
                               'action'],
                  'see_also': []},
                 {'title': 'Redundant Systems',
                  'text': 'Shadow vessels take damage normally, but automatically repair '
                          'all critical hits, including Vital Systems criticals, in the '
                          'End Phase of the following turn.',
                  'source': 'B5 ACTA Fleet Lists, The Shadows, p. 137',
                  'category': 'Fleet Rule',
                  'keywords': ['Redundant Systems',
                               'Fleet Rule',
                               'automatically',
                               'critical',
                               'criticals',
                               'damage',
                               'following',
                               'hits',
                               'including',
                               'normally'],
                  'see_also': []},
                 {'title': 'Crew',
                  'text': 'Shadow vessels have no Crew or Troops score. They cannot be '
                          'boarded or initiate boarding actions and ignore all critical '
                          'hits that affect Crew.',
                  'source': 'B5 ACTA Fleet Lists, The Shadows, p. 137',
                  'category': 'Fleet Rule',
                  'keywords': ['Crew',
                               'Fleet Rule',
                               'crew',
                               'actions',
                               'affect',
                               'boarded',
                               'boarding',
                               'cannot',
                               'critical',
                               'hits'],
                  'see_also': []},
                 {'title': 'Special Actions',
                  'text': 'Shadow vessels may use only Initiate Jump Point! and Run '
                          'Silent!',
                  'source': 'B5 ACTA Fleet Lists, The Shadows, p. 137',
                  'category': 'Fleet Rule',
                  'keywords': ['Special Actions',
                               'Fleet Rule',
                               'initiate',
                               'jump',
                               'only',
                               'point',
                               'shadow',
                               'silent',
                               'vessels'],
                  'see_also': []},
                 {'title': 'Superior Technology',
                  'text': 'Shadow vessels receive +1 on rolls made to overcome an enemy '
                          'ship’s Stealth.',
                  'source': 'B5 ACTA Fleet Lists, The Shadows, p. 137',
                  'category': 'Fleet Rule',
                  'keywords': ['Superior Technology',
                               'Fleet Rule',
                               'enemy',
                               'made',
                               'overcome',
                               'receive',
                               'rolls',
                               'shadow',
                               'ship’s',
                               'stealth'],
                  'see_also': []},
                 {'title': 'Superb Manoeuvrability',
                  'text': 'Shadow Ships and Shadow Scouts may use normal '
                          'Super-Manoeuvrability or instead turn up to 90 degrees at the '
                          'start of movement and then move up to twice Speed in a straight '
                          'line.',
                  'source': 'B5 ACTA Fleet Lists, The Shadows, p. 137',
                  'category': 'Fleet Rule',
                  'keywords': ['Superb Manoeuvrability',
                               'Fleet Rule',
                               'shadow',
                               'degrees',
                               'instead',
                               'line',
                               'move',
                               'movement',
                               'normal',
                               'scouts'],
                  'see_also': []},
                 {'title': 'Jump Point Disruptor',
                  'text': 'A Shadow Ship may use its Jump Point Disruptor instead of '
                          'firing other weapons. Select a jump point leading to hyperspace '
                          'within 18 inches; it closes immediately. Each ship that used it '
                          'this turn, or lies within 4 inches of its forward arc, rolls '
                          'one die: on 1 it suffers 3d6 Damage; on 2-3 it suffers 1d6 '
                          'critical hits with all Damage tripled; on 4-6 it is destroyed. '
                          'Auxiliary craft are destroyed on 2+.',
                  'source': 'B5 ACTA Fleet Lists, The Shadows, p. 137',
                  'category': 'Fleet Rule',
                  'keywords': ['Jump Point Disruptor',
                               'Fleet Rule',
                               'damage',
                               'destroyed',
                               'inches',
                               'jump',
                               'point',
                               'suffers',
                               'within',
                               'auxiliary'],
                  'see_also': []}],
 'Vorlon Empire': [{'title': 'Redundant Systems',
                    'text': 'Vorlon vessels take damage normally, but automatically repair '
                            'all critical hits, including Vital Systems criticals, in the '
                            'End Phase of the following turn.',
                    'source': 'B5 ACTA Fleet Lists, The Vorlon Empire, p. 133',
                    'category': 'Fleet Rule',
                    'keywords': ['Redundant Systems',
                                 'Fleet Rule',
                                 'automatically',
                                 'critical',
                                 'criticals',
                                 'damage',
                                 'following',
                                 'hits',
                                 'including',
                                 'normally'],
                    'see_also': []},
                   {'title': 'Crew',
                    'text': 'Vorlon vessels have no Crew or Troops score. They cannot be '
                            'boarded or initiate boarding actions and ignore all critical '
                            'hits that affect Crew.',
                    'source': 'B5 ACTA Fleet Lists, The Vorlon Empire, p. 133',
                    'category': 'Fleet Rule',
                    'keywords': ['Crew',
                                 'Fleet Rule',
                                 'crew',
                                 'actions',
                                 'affect',
                                 'boarded',
                                 'boarding',
                                 'cannot',
                                 'critical',
                                 'hits'],
                    'see_also': []},
                   {'title': 'Special Actions',
                    'text': 'Vorlon vessels may use only Activate Jump Gate!, All Stop!, '
                            'All Stop and Pivot!, Come About!, Initiate Jump Point!, and '
                            'Run Silent!',
                    'source': 'B5 ACTA Fleet Lists, The Vorlon Empire, p. 133',
                    'category': 'Fleet Rule',
                    'keywords': ['Special Actions',
                                 'Fleet Rule',
                                 'jump',
                                 'stop',
                                 'about',
                                 'activate',
                                 'come',
                                 'gate',
                                 'initiate',
                                 'only'],
                    'see_also': []},
                   {'title': 'Superior Technology',
                    'text': 'Vorlon vessels receive +1 on rolls made to overcome an enemy '
                            'ship’s Stealth.',
                    'source': 'B5 ACTA Fleet Lists, The Vorlon Empire, p. 133',
                    'category': 'Fleet Rule',
                    'keywords': ['Superior Technology',
                                 'Fleet Rule',
                                 'enemy',
                                 'made',
                                 'overcome',
                                 'receive',
                                 'rolls',
                                 'ship’s',
                                 'stealth',
                                 'vessels'],
                    'see_also': []}],
 'Vree Conglomerate': [{'title': 'Telepathy',
                        'text': 'All Vree receive +1 on Crew Quality checks. Vree '
                                'telepaths cannot disrupt Shadow vessels.',
                        'source': 'B5 ACTA Fleet Lists, The Vree Conglomerate, p. 122',
                        'category': 'Fleet Rule',
                        'keywords': ['Telepathy',
                                     'Fleet Rule',
                                     'vree',
                                     'cannot',
                                     'checks',
                                     'crew',
                                     'disrupt',
                                     'quality',
                                     'receive',
                                     'shadow'],
                        'see_also': []},
                       {'title': 'Super Manoeuvrability',
                        'text': 'A Vree ship may move less than half its Speed. When it '
                                'does, it may move as though it had the Super Manoeuvrable '
                                'trait.',
                        'source': 'B5 ACTA Fleet Lists, The Vree Conglomerate, p. 122',
                        'category': 'Fleet Rule',
                        'keywords': ['Super Manoeuvrability',
                                     'Fleet Rule',
                                     'move',
                                     'does',
                                     'half',
                                     'less',
                                     'manoeuvrable',
                                     'speed',
                                     'super',
                                     'though'],
                        'see_also': []}],
 "pak'ma'ra": [{'title': 'Redundant Systems',
                'text': "Whenever a pak'ma'ra ship loses Damage or Crew, roll one die for "
                        'each point lost. On a 6+, that point is ignored. The special '
                        'effects of Critical Hits still apply, although Damage and Crew '
                        'caused by the critical are rolled for normally. If the ship uses '
                        'Close Blast Doors and Activate Defence Grid!, this roll improves '
                        'to 5+; it does not receive two separate rolls.',
                'source': "B5 ACTA Fleet Lists, The pak'ma'ra, p. 116",
                'category': 'Fleet Rule',
                'keywords': ['Redundant Systems',
                             'Fleet Rule',
                             "pak'ma'ra",
                             'Damage',
                             'Crew',
                             'Critical Hits',
                             'Close Blast Doors',
                             'defence'],
                'see_also': []},
               {'title': 'Plasma Web',
                'text': "A squadron of pak'ma'ra ships may target the same point in space "
                        'with Plasma Cannon and Heavy Plasma Cannon. Combine their AD and '
                        'halve the total, rounding down; the attack gains Energy Mine. '
                        'Heavy Plasma Cannon retain Double Damage only if no ordinary '
                        'Plasma Cannon contribute to the web.',
                'source': "B5 ACTA Fleet Lists, The pak'ma'ra, p. 117",
                'category': 'Fleet Rule',
                'keywords': ['Plasma Web',
                             'Fleet Rule',
                             "pak'ma'ra",
                             'Plasma Cannon',
                             'Heavy Plasma Cannon',
                             'Energy Mine',
                             'Double Damage',
                             'squadron'],
                'see_also': ['Energy Mine', 'Double Damage']},
               {'title': 'Gentle Beings',
                'text': "All pak'ma'ra ships suffer a -1 penalty to their Crew Quality "
                        'scores.',
                'source': "B5 ACTA Fleet Lists, The pak'ma'ra, p. 117",
                'category': 'Fleet Rule',
                'keywords': ['Gentle Beings',
                             'Fleet Rule',
                             "pak'ma'ra",
                             'Crew Quality',
                             'penalty'],
                'see_also': []}]}


_ALIASES = {
    'Slow Loading': 'Slow-Loading',
    'Double-Damage': 'Double Damage',
    'Triple-Damage': 'Triple Damage',
    'Quad-Damage': 'Quad Damage',
    'Twin Linked': 'Twin-Linked',
    'One Shot': 'One-Shot',
    'Mini Beam': 'Mini-Beam',
    'Super-AP': 'Super AP',
    'Comm Disruptor': 'Comms Disruptor',
    'Interceptor': 'Interceptors',
    'Shield': 'Shields',
}


_PARAMETER_PATTERN = re.compile(
    r"^(.+?)\s+([+-]?\d+\+?|\d+[dD]\d+|\d+/(?:\d+|\d+[dD]\d+))$"
)



def normalize_rule_name(value: str) -> str:
    value = re.sub(r'\s+', ' ', str(value).strip())

    if value in _ALIASES:
        return _ALIASES[value]

    match = _PARAMETER_PATTERN.match(value)

    if match:
        base = match.group(1).strip()
        return _ALIASES.get(base, base)

    return value


def split_weapon_traits(value: str) -> list[str]:
    value = str(value).strip()

    if not value:
        return []

    return [
        normalize_rule_name(part)
        for part in value.split(',')
        if part.strip()
    ]


def get_rule(name: str) -> dict[str, Any] | None:
    key = normalize_rule_name(name)

    for collection in (SHIP_TRAITS, WEAPON_TRAITS, NAMED_RULES):
        if key in collection:
            return collection[key]

    return None


def get_fleet_rules(fleet_name: str) -> list[str]:
    return list(FLEET_RULES.get(str(fleet_name), []))



def get_rule_metadata(name: str) -> dict[str, Any] | None:
    entry = get_rule(name)
    if entry is None:
        return None
    return {
        "title": entry.get("title", normalize_rule_name(name)),
        "category": entry.get("category", "Rule"),
        "source": entry.get("source", ""),
        "keywords": list(entry.get("keywords", [])),
        "see_also": list(entry.get("see_also", [])),
    }


def get_related_rules(name: str) -> list[str]:
    entry = get_rule(name)
    if entry is None:
        return []
    return list(entry.get("see_also", []))


def search_rules(query: str) -> list[dict[str, Any]]:
    terms = {
        term.casefold()
        for term in re.findall(r"[A-Za-z0-9+'’-]+", str(query))
        if term.strip()
    }
    if not terms:
        return []

    results = []
    for collection_name, collection in (
        ("Ship Trait", SHIP_TRAITS),
        ("Weapon Trait", WEAPON_TRAITS),
        ("Named Rule", NAMED_RULES),
    ):
        for key, entry in collection.items():
            searchable = " ".join([
                key,
                str(entry.get("title", "")),
                str(entry.get("category", collection_name)),
                str(entry.get("text", "")),
                " ".join(str(x) for x in entry.get("keywords", [])),
                " ".join(str(x) for x in entry.get("see_also", [])),
            ]).casefold()
            score = sum(1 for term in terms if term in searchable)
            if score:
                results.append({
                    "key": key,
                    "title": entry.get("title", key),
                    "category": entry.get("category", collection_name),
                    "text": entry.get("text", ""),
                    "source": entry.get("source", ""),
                    "keywords": list(entry.get("keywords", [])),
                    "see_also": list(entry.get("see_also", [])),
                    "score": score,
                })

    return sorted(results, key=lambda item: (-item["score"], str(item["title"]).casefold()))


def get_missing_rule_texts() -> list[str]:
    missing = []

    for collection in (SHIP_TRAITS, WEAPON_TRAITS, NAMED_RULES):
        for key, entry in collection.items():
            if not str(entry.get('text', '')).strip():
                missing.append(key)

    return sorted(set(missing), key=str.casefold)

