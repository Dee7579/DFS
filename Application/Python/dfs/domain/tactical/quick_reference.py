"""Shared table-side rules reference for the Tactical Assistant.

Contextual help buttons and the searchable Quick Reference window consume the
same strings from this module.  Keeping one catalogue prevents a short pop-up
and the full reference from quietly drifting apart.
"""
from __future__ import annotations

from dataclasses import dataclass

from dfs.domain.tactical.b5_acta import (
    CORE_SPECIAL_ACTIONS,
    CRITICAL_RULES,
    FACTION_SPECIAL_ACTIONS,
)


ATTACK_TABLE_HELP = """Attack Table

For each Attack Die that equals or beats the target's Hull score, roll 1D6:

1 - Bulkhead Hit: no Damage or Crew loss.
2-5 - Solid Hit: the target loses 1 Damage and 1 Crew.
6 - Critical Hit: resolve a Solid Hit, then roll on the Systems Table.

A natural 1 on the original Attack Die always misses; a natural 6 always hits.

Source: B5 ACTA Second Edition Rulebook, pp. 8-9"""


TURN_SEQUENCE_HELP = """Turn Sequence

Initiative Phase
- Roll Initiative and determine which player nominates first.

Movement Phase
- Ships move.
- Fighters move.
- Anti-Fighter attacks are resolved.
- Scout traits are used.

Attack Phase
- Fighter attacks and dogfights.
- Ship attacks: roll Attack Dice, resolve Dodge, Interceptors and Shields, roll
  on the Attack Table, then resolve Gravitic Energy Grid, critical hits, Close
  Blast Doors and pak'ma'ra Redundant Systems.
- Boarding actions are performed.

End Phase
- Compulsory movement, including ships Running Adrift.
- Damage Control.
- Fighters launch.
- Begin the next turn.

Source: B5 ACTA Second Edition Rulebook, p. 25"""


DAMAGE_CONTROL_HELP = """Damage Control

During the End Phase, select one eligible critical effect and roll:

1D6 + Crew Quality + active modifiers

A total of 9+ repairs the effect. Damage Control never restores Damage, Crew,
or Troop losses. A critical cannot be repaired during the turn in which it was
suffered, and Vital Systems criticals are permanent.

Normally only one critical may be attempted per ship. All Hands on Deck! grants
+2 and permits any number of attempts. Skeleton Crew applies -2 unless an
active Flight Computer ignores that penalty. Each Multiple Fires result applies
-1. An active Self-Repairing trait grants +1.

Source: B5 ACTA Second Edition Rulebook, pp. 12, 14, 18"""


MOVEMENT_HELP = """Movement and Turning

Ships normally move from 0 to their current Speed. Before the first turn, most
ships must move at least half their Speed straight ahead. Each later turn
requires at least 2 inches of straight movement unless a trait says otherwise.
The printed Turn score gives the number and maximum angle of turns.

Crippled ships move at half Speed, lose one turn to a minimum of one, and make
45-degree turns. Super-Manoeuvrable ships become Turns 2/45 degrees.

A ship Running Adrift takes no normal movement. In every End Phase it instead
moves half its current Speed straight ahead until it leaves the table.

Source: B5 ACTA Second Edition Rulebook, pp. 6, 9, 12"""


FIGHTER_OPERATIONS_HELP = """Fighter Operations

Ready flights remain aboard their carrier. Launched flights act as independent
craft. Fighters move after ships in the Movement Phase and attack before ships
in the Attack Phase. Dogfights are resolved before ship attacks. New flights
launch in the End Phase.

When an enemy flight enters base contact with a ship, resolve available
Anti-Fighter attacks before the dogfight. A flight reduced to Lost is removed
from play; changing Ready, Launched, and Lost counts never changes the carrier's
printed complement.

Source: B5 ACTA Second Edition Rulebook, pp. 25, 28-29"""


BOARDING_ACTIONS_HELP = """Boarding Actions

Boarding is resolved in the Attack Phase after normal attacks. A boarding ship
must meet the printed contact and movement requirements, then both sides commit
eligible Troops. Surviving Troops continue fighting in later Attack Phases.

Each attacking Troop rolls on the boarding table. Crew may be killed and a 6
causes a critical hit. If the defending Crew is eliminated, the ship is
captured and Runs Adrift; scenario and Victory Point rules determine its value.

Source: B5 ACTA Second Edition Rulebook, pp. 41-42"""


CONDITIONS_HELP = """Common Ship Conditions

Crippled - At or below the Damage threshold. Half Speed; reduced 45-degree
turns; one weapon per fire arc; Shields offline; check every trait for loss.

Skeleton Crew - At or below the Crew threshold. No Special Actions, one weapon
system per turn, -2 Damage Control, and half Troops unless an applicable rule
such as Flight Computer says otherwise.

Running Adrift - Move half current Speed straight ahead in the End Phase. A
ship with 0 Crew takes no further active part and has no Troops.

Stricken - Damage is 0 or lower. Roll on the Damage Table once, adding +1 for
each point below 0, to determine Adrift, Destroyed, or an explosion result.

Surrendered - Motionless and normally out of the battle while the surrendering
player maintains control under the Special Action's conditions.

Tactical Withdrawal - The ship leaves through a table edge or jump point.
Scenario rules decide which exits are safe and how many Victory Points are
yielded.

Source: B5 ACTA Second Edition Rulebook, pp. 9, 25, 49"""


DISPOSITION_DAMAGE_TABLE_HELP = """Stricken Ships - Damage Table

When a ship's Damage is reduced to 0, roll 1D6 and add +1 for every point below
0. Once this roll is made, the ship may not be attacked again.

1-6 - Running Adrift
The ship follows the Running Adrift rules.

7-11 - Ship Destroyed
Leave a burned-out hulk stationary on the table.

12-17 - Ship Explodes (delayed)
The ship Runs Adrift, then explodes at the end of the next Movement Phase.
Every target within 4 inches is attacked with half the ship's starting Damage
in AD, to a maximum of 15 AD. Remove the ship after resolving the attacks.

18+ - Ship Explodes (immediate)
The ship explodes immediately. Every target within 4 inches is attacked with
half the ship's starting Damage in AD, to a maximum of 15 AD. Remove the ship
after resolving the attacks.

Source: B5 ACTA Second Edition Rulebook, p. 9"""


DISPOSITION_DESCRIPTIONS = {
    "operational": (
        "Operational - The platform remains under control and acts normally, "
        "subject to its other damage, Crew, trait, and critical effects."
    ),
    "adrift": (
        "Running Adrift - No normal movement. Move half current Speed straight "
        "ahead in each End Phase. A ship with active Crew may still attempt a "
        "Special Action when selected in the Movement Phase."
    ),
    "destroyed": (
        "Destroyed - The platform takes no further part in the battle. Apply the "
        "appropriate hulk, explosion, removal, and Victory Point rules."
    ),
    "surrendered": (
        "Surrendered - Leave the ship motionless. It takes no further part while "
        "the surrender remains in force; the printed surrender rule governs when "
        "control can return."
    ),
    "withdrawn": (
        "Tactical Withdrawal - The ship has safely left the battle through a "
        "permitted edge or jump point. Scenario rules determine the Victory "
        "Points yielded and whether that exit was safe."
    ),
}


def _special_actions_help() -> str:
    lines = ["Special Actions", ""]
    for action in (*CORE_SPECIAL_ACTIONS, *FACTION_SPECIAL_ACTIONS):
        faction = f" [{action.faction.title()}]" if action.faction else ""
        lines.extend(
            (
                f"{action.name}{faction}",
                f"Crew Quality Check: {action.check}",
                action.effect,
                "",
            )
        )
    lines.append("Source: B5 ACTA Second Edition Rulebook and official fleet rules")
    return "\n".join(lines).strip()


def _critical_tables_help() -> str:
    lines = ["Critical Hit Tables", "", "Systems roll: 1-2 Engines; 3 Reactor; 4 Weapons; 5 Crew; 6 Vital Systems."]
    previous_system = ""
    for rule in CRITICAL_RULES:
        if rule.system != previous_system:
            lines.extend(("", rule.system))
            previous_system = rule.system
        lines.append(
            f"{rule.roll} - {rule.label}: Damage {rule.damage}; Crew {rule.crew}. {rule.effect or 'No additional effect.'}"
        )
    lines.extend(("", "Vital Systems criticals cannot be repaired through Damage Control.", "", "Source: B5 ACTA Second Edition Rulebook, pp. 10-12"))
    return "\n".join(lines)


SPECIAL_ACTIONS_HELP = _special_actions_help()
CRITICAL_TABLES_HELP = _critical_tables_help()


@dataclass(frozen=True, slots=True)
class ReferenceEntry:
    title: str
    category: str
    text: str
    source: str = ""


REFERENCE_ENTRIES = (
    ReferenceEntry("Turn Sequence", "Core Procedures", TURN_SEQUENCE_HELP),
    ReferenceEntry("Attack Procedure and Hit Chart", "Core Procedures", ATTACK_TABLE_HELP),
    ReferenceEntry("Movement and Turning", "Core Procedures", MOVEMENT_HELP),
    ReferenceEntry("Damage Control", "Damage and Criticals", DAMAGE_CONTROL_HELP),
    ReferenceEntry("Critical Hit Tables", "Damage and Criticals", CRITICAL_TABLES_HELP),
    ReferenceEntry("Stricken Ship Damage Table", "Damage and Criticals", DISPOSITION_DAMAGE_TABLE_HELP),
    ReferenceEntry("Common Ship Conditions", "Damage and Criticals", CONDITIONS_HELP),
    ReferenceEntry("Special Actions", "Actions", SPECIAL_ACTIONS_HELP),
    ReferenceEntry("Fighter Operations", "Craft and Boarding", FIGHTER_OPERATIONS_HELP),
    ReferenceEntry("Boarding Actions", "Craft and Boarding", BOARDING_ACTIONS_HELP),
)


COMMON_CODEX_RULE_NAMES = (
    "Adaptive Armour",
    "Advanced Anti-Fighter",
    "Agile",
    "Anti-Fighter",
    "Carrier",
    "Dodge",
    "Escort",
    "Fighter",
    "Flight Computer",
    "Interceptors",
    "Jump Engine",
    "Self-Repairing",
    "Shields",
    "Stealth",
    "Accurate",
    "AP",
    "Beam",
    "Double Damage",
    "Energy Mine",
    "Mini-Beam",
    "Precise",
    "Quad Damage",
    "Slow-Loading",
    "Super AP",
    "Triple Damage",
    "Twin-Linked",
)
