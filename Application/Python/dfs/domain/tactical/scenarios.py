"""Babylon 5 ACTA scenario catalogue and Victory Point scoring.

The catalogue is declarative. Tactical Assistant consumes it for scenario
selection, concise rule reminders, and automatic points yielded by the local
fleet. Objective conditions that require table-position knowledge remain
explicit manual entries in the battle report.
"""
from __future__ import annotations

from dataclasses import dataclass
from math import ceil
import random
from typing import Iterable

from dfs.domain.tactical.models import TacticalGameState, TacticalUnitState, UnitKind
from dfs.domain.tactical.scenario_rules_text import SCENARIO_FULL_RULES


PRIORITY_LEVELS: tuple[str, ...] = (
    "Patrol",
    "Skirmish",
    "Raid",
    "Battle",
    "War",
    "Armageddon",
)


@dataclass(frozen=True, slots=True)
class ScenarioDefinition:
    key: str
    name: str
    category: str
    source: str
    fleets: str
    rules: str
    game_length: str
    victory: str
    uses_standard_victory_points: bool = False
    random_eligible: bool = False
    holding_ground_bonus: bool = True
    opponent_withdrawal_scores: bool = True

    @property
    def display_text(self) -> str:
        complete = SCENARIO_FULL_RULES.get(self.key)
        if complete:
            return complete
        parts = [
            f"Source: {self.source}",
            f"Fleets: {self.fleets}",
            f"Rules: {self.rules}",
            f"Game Length: {self.game_length}",
            f"Victory: {self.victory}",
        ]
        return "\n".join(parts)


def _scenario(
    key: str,
    name: str,
    category: str,
    source: str,
    fleets: str,
    rules: str,
    game_length: str,
    victory: str,
    *,
    standard_vp: bool = False,
    random_eligible: bool = False,
    holding_ground: bool = True,
    withdrawal_scores: bool = True,
) -> ScenarioDefinition:
    return ScenarioDefinition(
        key=key,
        name=name,
        category=category,
        source=source,
        fleets=fleets,
        rules=rules,
        game_length=game_length,
        victory=victory,
        uses_standard_victory_points=standard_vp,
        random_eligible=random_eligible,
        holding_ground_bonus=holding_ground,
        opponent_withdrawal_scores=withdrawal_scores,
    )


SCENARIOS: tuple[ScenarioDefinition, ...] = (
    _scenario("ambush", "Ambush", "Rulebook - Standard", "Rulebook pp. 50-51", "Defender 5 FAP; attacker 3 FAP.", "Attacker wins Initiative on Turn 1; defending ships require CQ 10 to act normally on Turn 1.", "Until the attacker withdraws or one side has no viable ships.", "Standard Victory Points; defender gains no points for attacker tactical withdrawals.", standard_vp=True, random_eligible=True),
    _scenario("annihilation", "Annihilation", "Rulebook - Standard", "Rulebook p. 51", "Random FAP; fleets chosen freely.", "No special rules.", "Until one fleet has no ships remaining.", "Last fleet with a ship on the table wins.", random_eligible=True),
    _scenario("assassination", "Assassination", "Rulebook - Standard", "Rulebook pp. 52-53", "Random FAP; fleets chosen freely.", "Attacker secretly nominates the highest-PL eligible enemy ship as the target.", "12 turns or until a fleet withdraws or has no viable ships.", "Scenario objective centred on the nominated target; use the printed scenario result.", random_eligible=True),
    _scenario("blockade", "Blockade", "Rulebook - Standard", "Rulebook p. 53", "Blockader 5 FAP; runner 3 FAP.", "Runner receives one free opening turn.", "12 turns or until the runner withdraws or has no viable ships.", "Blockader scores standard VP. Runner scores full value only for ships exiting the blockader's long edge.", standard_vp=True, random_eligible=True, holding_ground=False),
    _scenario("call-to-arms", "Call to Arms", "Rulebook - Standard", "Rulebook p. 54", "Random FAP; fleets chosen freely.", "No special rules.", "12 turns or until a side has no viable ships.", "Standard Victory Points.", standard_vp=True, random_eligible=True),
    _scenario("carrier-clash", "Carrier Clash", "Rulebook - Standard", "Rulebook p. 55", "Random FAP; highest-PL choice must carry auxiliary craft.", "No special rules.", "12 turns or until a side has no viable ships.", "Standard Victory Points.", standard_vp=True, random_eligible=True),
    _scenario("convoy-duty", "Convoy Duty", "Rulebook - Standard", "Rulebook p. 56", "Attacker and defender use scenario fleets; defender has convoy ships.", "Convoy ships move in the End Phase.", "12 turns or until a side has no viable ships.", "Standard VP for combatants; +2 per convoy destroyed for attacker and +2 per convoy escaping for defender.", standard_vp=True, random_eligible=True, holding_ground=False),
    _scenario("flee-to-jump-gate", "Flee to the Jump Gate", "Rulebook - Standard", "Rulebook p. 57", "Scenario attacker and defender forces.", "Main attacker force arrives from the surprise entry point on Turn 2.", "Until the defender escapes or a side has no viable ships.", "Attacker scores standard VP; defender gains full value for ships escaping through the jump gate.", standard_vp=True, random_eligible=True, holding_ground=False),
    _scenario("planetary-assault", "Planetary Assault", "Rulebook - Standard", "Rulebook p. 58", "Scenario assault fleets and planetary defences.", "Use all Planetary Assault rules.", "Until the planetary victory conditions are met.", "Victory is determined by control of the planet and surviving Troops/Emplacements.", random_eligible=True),
    _scenario("planetfall", "Planetfall", "Rulebook - Standard", "Rulebook p. 59", "Random FAP; fleets chosen freely.", "First fleet to land counts as defender for planetary Troop combat.", "12 turns.", "Standard VP; side with more Troops on the planet gains +10 VP.", standard_vp=True, random_eligible=True),
    _scenario("recon-run", "Recon Run", "Rulebook - Standard", "Rulebook p. 60", "Defender 5 FAP; attacker 3 FAP.", "Attacking ships may scan one enemy ship per turn at 12 inches with CQ+d6 >= 7.", "12 turns or until all defending ships are scanned.", "Standard VP with attacker gaining half destroyed value for each successfully scanned ship.", standard_vp=True, random_eligible=True),
    _scenario("rescue", "Rescue", "Rulebook - Standard", "Rulebook p. 61", "Random FAP; fleets chosen freely.", "Objective ship cannot move, be boarded, or be fired upon.", "12 turns.", "Standard VP; +10 VP for controlling the objective ship at game end.", standard_vp=True, random_eligible=True),
    _scenario("space-superiority", "Space Superiority", "Rulebook - Standard", "Rulebook p. 62", "Random FAP; fleets chosen freely.", "Battlefield is divided into 24-inch grid squares.", "12 turns.", "Standard VP; +5 VP per uncontested grid square held by an eligible ship.", standard_vp=True, random_eligible=True),
    _scenario("supply-ships", "Supply Ships", "Rulebook - Standard", "Rulebook p. 63", "Random FAP; defender receives supply ships based on scenario PL.", "Supply ships move in the End Phase.", "12 turns or until withdrawal/no viable ships.", "Standard VP for combatants; +2 per supply ship destroyed or surviving as described.", standard_vp=True, random_eligible=True, holding_ground=False),

    _scenario("gravity-well", "Gravity Well", "P&P - Standard", "Powers & Principalities pp. 24-25", "Both fleets have 3 FAP.", "Search asteroid field for the admiral; star gravity and radiation affect nearby ships.", "Until victory conditions are met.", "Escape with the admiral to win; otherwise draw if the admiral is destroyed or never found.", random_eligible=True),
    _scenario("invasion", "Invasion", "P&P - Standard", "Powers & Principalities p. 25", "Defender 5 FAP; attacker starts with 3 and receives 1 FAP each turn.", "Defender may not make Tactical Withdrawals.", "8 turns.", "Attacker wins by wiping out defender; defender wins by retaining an unstricken ship.", random_eligible=True),
    _scenario("king-of-the-jump-gate", "King of the Jump Gate", "P&P - Standard", "Powers & Principalities pp. 26-27", "Up to eight players; 1 Raid FAP each.", "Whole fleets move by Initiative order; each player receives a secret random objective.", "Until all remaining players achieve their conditions.", "Complete the secret objective or be the last player on the table.", random_eligible=True),
    _scenario("on-the-back-foot", "On the Back Foot", "P&P - Standard", "Powers & Principalities p. 28", "Attacker 8 FAP; defender 5 FAP plus 5 FAP reinforcements.", "Attacker enters from both short edges; defender reinforcements arrive on Turn 5.", "12 turns.", "Standard Victory Points.", standard_vp=True, random_eligible=True),
    _scenario("towering-inferno", "Towering Inferno", "P&P - Standard", "Powers & Principalities p. 29", "Both fleets have 10 FAP but initially deploy only 1 FAP.", "Undeployed ships arrive randomly from random table edges.", "12 turns.", "Standard Victory Points.", standard_vp=True, random_eligible=True),

    _scenario("battle-of-the-line", "Battle of the Line", "Rulebook - Historical", "Rulebook pp. 64-65", "Fixed Earth Alliance and Minbari fleets.", "Historical deployment and jump-point entry.", "6 turns.", "Use the printed historical victory conditions."),
    _scenario("assault-on-ragesh-3", "Assault on Ragesh 3", "Rulebook - Historical", "Rulebook pp. 66-67", "Fixed Centauri and Narn forces.", "Historical scenario rules.", "Printed scenario length.", "Use the printed historical victory conditions."),
    _scenario("quadrant-37", "Quadrant 37", "Rulebook - Historical", "Rulebook pp. 68-69", "Fixed Narn and Shadow forces.", "Historical scenario rules.", "Printed scenario length.", "Use the printed historical victory conditions."),
    _scenario("second-battle-quadrant-14", "The Second Battle for Quadrant 14", "Rulebook - Historical", "Rulebook pp. 70-71", "Fixed Narn and Centauri forces.", "Historical scenario rules.", "Printed scenario length.", "Use the printed historical victory conditions."),
    _scenario("long-twilight-struggle", "The Long Twilight Struggle", "Rulebook - Historical", "Rulebook pp. 72-73", "Fixed Army of Light and Shadow forces.", "Historical scenario rules.", "Printed scenario length.", "Use the printed historical victory conditions."),
    _scenario("fall-of-night", "The Fall of Night", "Rulebook - Historical", "Rulebook pp. 74-75", "Fixed scenario forces.", "Historical scenario rules.", "Printed scenario length.", "Use the printed historical victory conditions."),
    _scenario("severed-dreams", "Severed Dreams", "Rulebook - Historical", "Rulebook pp. 76-77", "Fixed Earth Alliance and Babylon 5 forces.", "Historical scenario rules.", "Printed scenario length.", "Use the printed historical victory conditions."),
    _scenario("interludes-and-examinations", "Interludes and Examinations", "Rulebook - Historical", "Rulebook pp. 78-79", "Fixed Vorlon and Shadow forces.", "Historical scenario rules.", "Printed scenario length.", "Use the printed historical victory conditions."),
    _scenario("shadow-dancing", "Shadow Dancing", "Rulebook - Historical", "Rulebook pp. 80-81", "Fixed Army of Light and Shadow forces.", "Historical scenario rules.", "Printed scenario length.", "Use the printed historical victory conditions."),
    _scenario("into-the-fire", "Into the Fire", "Rulebook - Historical", "Rulebook pp. 82-83", "Fixed Army of Light and Vorlon forces.", "Historical scenario rules.", "Printed scenario length.", "Use the printed historical victory conditions."),
    _scenario("between-darkness-and-light", "Between the Darkness and the Light", "Rulebook - Historical", "Rulebook pp. 84-85", "Fixed scenario forces.", "Historical scenario rules.", "Printed scenario length.", "Use the printed historical victory conditions."),
    _scenario("border-dispute", "Border Dispute", "Rulebook - Historical", "Rulebook p. 76", "Fixed Brakiri and Drazi forces.", "Mock damage is used until either fleet opens fire for real.", "12 turns.", "Use the printed scenario victory conditions."),
    _scenario("hunting-the-hunters", "Hunting the Hunters", "Rulebook - Historical", "Rulebook p. 77", "Fixed ISA and Raiders forces.", "The White Star enters through a jump point; fighter deployment is delayed.", "Until victory conditions are met.", "Use the printed scenario victory conditions."),

    _scenario("initial-contact", "Initial Contact", "P&P - Deep Space Tournament", "Powers & Principalities pp. 31-32", "One Skirmish and one Battle ship per player.", "Battle ships arrive on Turns 5-6 if the patrol ship survives.", "Until withdrawal/no viable ships.", "Use the printed Battle Grade table."),
    _scenario("automaton-recovery", "Automaton Recovery", "P&P - Deep Space Tournament", "Powers & Principalities pp. 32-33", "Full two-ship tournament fleets.", "Recover drone counters with the Recover Drone Special Action.", "Until withdrawal/no viable ships.", "Use the printed Battle Grade table."),
    _scenario("first-strike", "First Strike!", "P&P - Deep Space Tournament", "Powers & Principalities pp. 33-34", "Full two-ship tournament fleets.", "Battle ships require 5+ to fire each weapon or launch each flight.", "Until withdrawal/no viable ships.", "Use the printed Battle Grade table."),
    _scenario("shadows-of-the-past", "Shadows of the Past", "P&P - Deep Space Tournament", "Powers & Principalities pp. 34-35", "Full two-ship tournament fleets.", "Land commandos on the enemy Battle ship through boarding.", "Until one side has no viable ships.", "Use the printed Battle Grade table."),
)

SCENARIO_BY_KEY = {scenario.key: scenario for scenario in SCENARIOS}
SCENARIO_CATEGORIES: tuple[str, ...] = tuple(dict.fromkeys(s.category for s in SCENARIOS))

# Printed deployment diagrams extracted from the user's authoritative Rulebook
# and Powers & Principalities PDFs. Scenarios without a printed deployment map
# intentionally have no entry, allowing the UI to disable the Map button rather
# than displaying an invented diagram.
SCENARIO_MAP_FILES: dict[str, str] = {
    "ambush": "ambush.png",
    "annihilation": "annihilation.png",
    "assassination": "assassination.png",
    "blockade": "blockade.png",
    "call-to-arms": "call-to-arms.png",
    "carrier-clash": "carrier-clash.png",
    "convoy-duty": "convoy-duty.png",
    "flee-to-jump-gate": "flee-to-jump-gate.png",
    "planetary-assault": "planetary-assault.png",
    "planetfall": "planetfall.png",
    "recon-run": "recon-run.png",
    "rescue": "rescue.png",
    "space-superiority": "space-superiority.png",
    "supply-ships": "supply-ships.png",
    "gravity-well": "gravity-well.png",
    "king-of-the-jump-gate": "king-of-the-jump-gate.png",
    "on-the-back-foot": "on-the-back-foot.png",
    "towering-inferno": "towering-inferno.png",
    "battle-of-the-line": "battle-of-the-line.png",
    "assault-on-ragesh-3": "assault-on-ragesh-3.png",
    "quadrant-37": "quadrant-37.png",
    "second-battle-quadrant-14": "second-battle-quadrant-14.png",
    "long-twilight-struggle": "long-twilight-struggle.png",
    "fall-of-night": "fall-of-night.png",
    "severed-dreams": "severed-dreams.png",
    "interludes-and-examinations": "interludes-and-examinations.png",
    "shadow-dancing": "shadow-dancing.png",
    "into-the-fire": "into-the-fire.png",
    "between-darkness-and-light": "between-darkness-and-light.png",
    "border-dispute": "border-dispute.png",
    "hunting-the-hunters": "hunting-the-hunters.png",
    "initial-contact": "initial-contact.png",
    "automaton-recovery": "automaton-recovery.png",
    "first-strike": "first-strike.png",
}


def random_scenario(rng: random.Random | None = None) -> ScenarioDefinition:
    choices = tuple(scenario for scenario in SCENARIOS if scenario.random_eligible)
    if not choices:
        raise RuntimeError("No random-eligible Tactical Assistant scenarios are configured.")
    chooser = rng or random.SystemRandom()
    return chooser.choice(choices)


def random_priority_level(rng: random.Random | None = None) -> str:
    """Roll the published 2d6 random scenario Priority Level table."""

    roller = rng or random.SystemRandom()
    total = roller.randint(1, 6) + roller.randint(1, 6)
    if total <= 4:
        return "Patrol"
    if total <= 6:
        return "Skirmish"
    if total <= 8:
        return "Raid"
    if total <= 10:
        return "Battle"
    return "War"


def random_player_role(rng: random.Random | None = None) -> str:
    chooser = rng or random.SystemRandom()
    return chooser.choice(("attacker", "defender"))


def priority_index(priority_level: str) -> int | None:
    normalized = str(priority_level or "").strip().casefold()
    for index, name in enumerate(PRIORITY_LEVELS):
        if normalized == name.casefold():
            return index
    return None


def destroyed_victory_points(unit_priority: str, scenario_priority: str) -> int:
    ship_index = priority_index(unit_priority)
    scenario_index = priority_index(scenario_priority)
    if ship_index is None or scenario_index is None:
        return 0
    difference = ship_index - scenario_index
    if difference >= 0:
        return 10 * (difference + 1)
    lower = {-1: 5, -2: 3, -3: 2, -4: 1, -5: 0.5}
    value = lower.get(difference, 0)
    return int(value) if value >= 1 else 0


def _is_space_station(unit: TacticalUnitState) -> bool:
    return any("immobile" in trait.name.casefold() for trait in unit.traits) or (
        "station" in unit.platform_name.casefold()
    )


@dataclass(frozen=True, slots=True)
class UnitVictoryPoints:
    unit_id: str
    label: str
    reason: str
    points: int


@dataclass(frozen=True, slots=True)
class VictoryPointSummary:
    scenario_key: str
    scenario_name: str
    scenario_priority: str
    automatic_points: int
    entries: tuple[UnitVictoryPoints, ...]
    note: str = ""


def opponent_victory_points_from_local_fleet(
    game: TacticalGameState,
) -> VictoryPointSummary:
    scenario = SCENARIO_BY_KEY.get(game.scenario_key)
    if scenario is None:
        return VictoryPointSummary(
            scenario_key="",
            scenario_name="None",
            scenario_priority=game.scenario_priority,
            automatic_points=0,
            entries=(),
            note="Select a scenario and Priority Level to calculate Victory Points.",
        )
    if not scenario.uses_standard_victory_points:
        return VictoryPointSummary(
            scenario_key=scenario.key,
            scenario_name=scenario.name,
            scenario_priority=game.scenario_priority,
            automatic_points=0,
            entries=(),
            note="This scenario uses its printed victory conditions rather than standard unit Victory Points.",
        )
    if priority_index(game.scenario_priority) is None:
        return VictoryPointSummary(
            scenario_key=scenario.key,
            scenario_name=scenario.name,
            scenario_priority=game.scenario_priority,
            automatic_points=0,
            entries=(),
            note="Select the scenario Priority Level to calculate unit Victory Points.",
        )

    if scenario.key == "blockade" and game.player_role == "attacker":
        return VictoryPointSummary(
            scenario_key=scenario.key,
            scenario_name=scenario.name,
            scenario_priority=game.scenario_priority,
            automatic_points=0,
            entries=(),
            note=(
                "The blockade-running opponent scores for its own ships escaping the "
                "specified edge, so those objective points must be entered manually."
            ),
        )

    withdrawal_scores = scenario.opponent_withdrawal_scores
    if scenario.key == "ambush" and game.player_role == "attacker":
        withdrawal_scores = False

    entries: list[UnitVictoryPoints] = []
    for unit in game.units:
        if unit.kind is UnitKind.CRAFT:
            if unit.parent_unit_id is None and unit.is_destroyed:
                entries.append(UnitVictoryPoints(unit.unit_id, unit.platform_name, "Destroyed purchased fighter flight", 1))
            continue

        base = destroyed_victory_points(unit.priority_level, game.scenario_priority)
        if base <= 0:
            continue
        reason = ""
        points = 0
        if unit.is_surrendered:
            reason, points = "Surrendered", base * 2
        elif unit.is_destroyed:
            reason, points = "Destroyed", base
        elif unit.is_adrift:
            reason, points = "Running Adrift (counts as destroyed)", base
        elif unit.is_withdrawn and withdrawal_scores:
            reason, points = "Tactical Withdrawal", ceil(base / 4)
        else:
            partial = 0
            partial_reason = ""
            if _is_space_station(unit) and unit.is_crippled:
                partial = ceil(base / 2)
                partial_reason = "Crippled space station"
            elif unit.is_crippled or unit.is_skeleton_crew:
                partial = ceil(base / 4)
                if unit.is_crippled and unit.is_skeleton_crew:
                    partial_reason = "Crippled / Skeleton Crew"
                elif unit.is_crippled:
                    partial_reason = "Crippled"
                else:
                    partial_reason = "Skeleton Crew"
            reason, points = partial_reason, partial
        if points:
            entries.append(UnitVictoryPoints(unit.unit_id, unit.platform_name, reason, points))

    note = (
        "Automatic total covers unit-derived standard Victory Points. Enter any "
        "scenario objective bonuses in the battle report."
    )
    return VictoryPointSummary(
        scenario_key=scenario.key,
        scenario_name=scenario.name,
        scenario_priority=game.scenario_priority,
        automatic_points=sum(entry.points for entry in entries),
        entries=tuple(entries),
        note=note,
    )
