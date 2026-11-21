"""Source-backed Babylon 5 ACTA combat status rules used by Tactical Assistant.

The module contains only declarative published rule data and pure functions.
The UI presents these rules; it does not duplicate combat logic.
"""
from __future__ import annotations

from dataclasses import dataclass
import random
import re
from typing import Iterable

from dfs.domain.tactical.models import CriticalHitState, TacticalUnitState, UnitKind


@dataclass(frozen=True, slots=True)
class CriticalRule:
    key: str
    system: str
    roll: str
    label: str
    damage: str
    crew: str
    effect: str
    speed_penalty: int = 0
    weapon_ad_penalty: int = 0
    no_special_actions: bool = False
    no_damage_control: bool = False
    no_damage_control_this_turn: bool = False
    troop_penalty: int = 0
    power_fluctuations: bool = False
    adrift: bool = False
    target_kind: str = ""
    target_count: int = 0
    repairable: bool = True

    @property
    def display_label(self) -> str:
        return f"{self.system} {self.roll} - {self.label}"

    @property
    def fixed_damage(self) -> int | None:
        return _fixed_loss(self.damage)

    @property
    def fixed_crew(self) -> int | None:
        return _fixed_loss(self.crew)


def _fixed_loss(value: str) -> int | None:
    text = value.strip().upper().replace("-", "")
    if text.isdigit():
        return int(text)
    return None


CRITICAL_RULES: tuple[CriticalRule, ...] = (
    CriticalRule("engines-power-relays", "Engines", "1-2", "Power Relays Destroyed", "0", "0", "-1 Speed", speed_penalty=1),
    CriticalRule("engines-thrusters", "Engines", "3-4", "Thrusters Damaged", "1", "0", "-2 Speed", speed_penalty=2),
    CriticalRule("engines-fuel-systems", "Engines", "5", "Fuel Systems Ruptured", "2", "1", "-4 Speed", speed_penalty=4),
    CriticalRule("engines-disabled", "Engines", "6", "Engines Disabled", "3", "1", "Ship moves as though it is adrift", adrift=True),
    CriticalRule("reactor-capacitors", "Reactor", "1-2", "Capacitors Damaged", "0", "1", "-2 Speed; all weapons lose 1 AD", speed_penalty=2, weapon_ad_penalty=1),
    CriticalRule("reactor-power-feedback", "Reactor", "3-4", "Power Feedback", "1", "1", "Lose one random trait", target_kind="trait", target_count=1),
    CriticalRule("reactor-gas-leak", "Reactor", "5", "Reactor Gas Leak", "0", "3", "No Special Actions", no_special_actions=True),
    CriticalRule("reactor-explosion", "Reactor", "6", "Reactor Explosion", "3", "4", "No Special Actions; lose one random trait", no_special_actions=True, target_kind="trait", target_count=1),
    CriticalRule("weapons-targeting", "Weapons", "1-3", "Targeting Systems Damaged", "0", "1", "All weapons lose 1 AD", weapon_ad_penalty=1),
    CriticalRule("weapons-power-fluctuations", "Weapons", "4", "Power Fluctuations", "0", "0", "Roll 4+ before firing each weapon", power_fluctuations=True),
    CriticalRule("weapons-offline", "Weapons", "5", "Weapons Offline", "2", "2", "One random weapon system in a random arc cannot fire", target_kind="weapon", target_count=1),
    CriticalRule("weapons-ammunition-explosion", "Weapons", "6", "Catastrophic Ammunition Explosion", "3", "4", "No weapons in one random arc can fire", target_kind="arc", target_count=1),
    CriticalRule("crew-fire", "Crew", "1-2", "Fire", "0", "2", "No continuing core-rule effect"),
    CriticalRule("crew-multiple-fires", "Crew", "3-4", "Multiple Fires", "0", "3", "Damage Control suffers a -1 penalty"),
    CriticalRule("crew-decompression", "Crew", "5", "Localised Decompression", "1", "3", "-1 Troops; no Special Actions", no_special_actions=True, troop_penalty=1),
    CriticalRule("crew-hull-breach", "Crew", "6", "Hull Breach", "2", "4", "-2 Troops; no Damage Control this turn", no_damage_control_this_turn=True, troop_penalty=2),
    CriticalRule("vital-bridge", "Vital Systems", "1", "Bridge Hit", "0", "1", "No Special Actions", no_special_actions=True, repairable=False),
    CriticalRule("vital-secondary-explosions", "Vital Systems", "2", "Secondary Explosions", "1D6", "1D6", "Apply the rolled Damage and Crew losses", repairable=False),
    CriticalRule("vital-engineering", "Vital Systems", "3", "Engineering", "4", "3", "No Damage Control permitted", no_damage_control=True, repairable=False),
    CriticalRule("vital-weapons-control", "Vital Systems", "4", "Weapons Control", "4", "4", "No firing from one random arc", target_kind="arc", target_count=1, repairable=False),
    CriticalRule("vital-reactor-implosion", "Vital Systems", "5", "Reactor Implosion", "2D6", "4D6", "Lose one random trait", target_kind="trait", target_count=1, repairable=False),
    CriticalRule("vital-catastrophic-explosion", "Vital Systems", "6", "Catastrophic Explosion", "4D6", "2D6", "Lose two random traits", target_kind="trait", target_count=2, repairable=False),
)

CRITICAL_RULE_BY_KEY = {rule.key: rule for rule in CRITICAL_RULES}

CRITICAL_SYSTEMS_TABLE_HELP = (
    "Critical Systems Table (first D6 roll)\n\n"
    "1-2  Engines\n"
    "3     Reactor\n"
    "4     Weapons\n"
    "5     Crew\n"
    "6     Vital Systems\n\n"
    "After determining the system, roll on that system's Critical Results table."
)


def roll_loss_expression(expression: str, rng: random.Random | None = None) -> int:
    """Roll a fixed value or a standard ``NdM`` damage/crew expression."""

    text = str(expression or "").strip().upper().replace(" ", "")
    if not text:
        raise ValueError("a Damage or Crew loss expression is required")
    if text.isdigit():
        return int(text)
    match = re.fullmatch(r"(?P<count>\d*)D(?P<sides>\d+)", text)
    if match is None:
        raise ValueError(f"unsupported dice expression: {expression}")
    count = int(match.group("count") or "1")
    sides = int(match.group("sides"))
    if count < 1 or sides < 2:
        raise ValueError(f"invalid dice expression: {expression}")
    roller = rng or random.SystemRandom()
    return sum(roller.randint(1, sides) for _ in range(count))


@dataclass(frozen=True, slots=True)
class SpecialAction:
    name: str
    check: str
    effect: str
    faction: str = ""


CORE_SPECIAL_ACTIONS: tuple[SpecialAction, ...] = (
    SpecialAction("None / Normal Operations", "-", "No Special Action is being performed."),
    SpecialAction("Activate Jump Gate!", "Automatic or Opposed", "Operate a jump gate."),
    SpecialAction("All Hands on Deck!", "Automatic", "+2 Damage Control; repair any number of criticals; fire only one weapon system."),
    SpecialAction("All Power to Engines!", "Automatic", "+50% Speed this turn; no turns."),
    SpecialAction("All Stop!", "Automatic", "Move between 0 and half Speed; no turns."),
    SpecialAction("All Stop and Pivot!", "Automatic", "Do not move; fire one weapon system; turn up to double normal turn rate."),
    SpecialAction("Close Blast Doors and Activate Defence Grid!", "Automatic", "Fire at most one weapon system; ignore each Damage/Crew point on 5+."),
    SpecialAction("Come About!", "9", "Gain one extra turn or increase one turn by 45 degrees."),
    SpecialAction("Concentrate All Fire-power!", "8", "Re-roll misses against one target, subject to weapon-trait exclusions."),
    SpecialAction("Give Me Ramming Speed!", "9", "Crippled ships gain 50% current Speed and may turn once."),
    SpecialAction("Initiate Jump Point!", "Automatic", "Use a Jump Engine or Advanced Jump Engine to enter or leave hyperspace."),
    SpecialAction("Intensify Defensive Fire!", "8", "Halve weapon AD; double Interceptors and Anti-Fighter dice."),
    SpecialAction("Launch Breaching Pods and Shuttles!", "Automatic", "Launch a boarding action with embarked Troops."),
    SpecialAction("Run Silent!", "8", "Gain or improve Stealth; may not fire, exceed half Speed, or turn."),
    SpecialAction("Scramble! Scramble!", "7", "Launch two fighter flights; Carrier temporarily gains +2."),
    SpecialAction("Stand Down and Prepare to be Boarded!", "Opposed", "Attempt to force an eligible enemy ship to surrender."),
)

FACTION_SPECIAL_ACTIONS: tuple[SpecialAction, ...] = (
    SpecialAction("Deploy Mines!", "Automatic", "Deploy an Abbai mine marker during movement.", faction="abbai"),
    SpecialAction("Divert Auxiliary Power to Shields!", "Automatic", "Restore half total Shields in the next End Phase.", faction="abbai"),
    SpecialAction("Alpha Strike!", "9", "Dilgar squadron concentrates fire and escalates matching critical systems.", faction="dilgar"),
    SpecialAction("Start Attack Run!", "8", "Drazi ship performs a forward-arc attack during movement.", faction="drazi"),
    SpecialAction("Regenerate!", "9", "Vorlon ship doubles Self-Repair for the End Phase and becomes Adrift while regenerating.", faction="vorlon"),
    SpecialAction("Initiate Extraction!", "Automatic", "Vree ship attempts to extract enemy crew at close range.", faction="vree"),
    SpecialAction("Cause Confusion", "Opposed", "Psychic Crew attempts to cancel an enemy Special Action.", faction="psi corps"),
)


@dataclass(frozen=True, slots=True)
class SpecialActionAvailability:
    action: SpecialAction
    allowed: bool
    reason: str = ""


def _active_trait_names(unit: TacticalUnitState) -> tuple[str, ...]:
    return tuple(
        trait.name.casefold()
        for trait in unit.traits
        if not unit.trait_is_inactive(trait.trait_key)
    )


def _has_trait(unit: TacticalUnitState, name: str) -> bool:
    expected = name.casefold()
    return any(
        trait == expected or trait.startswith(expected + " ")
        for trait in _active_trait_names(unit)
    )


def special_action_availability(unit: TacticalUnitState) -> tuple[SpecialActionAvailability, ...]:
    faction = unit.faction_name.casefold()
    actions = list(CORE_SPECIAL_ACTIONS)
    actions.extend(action for action in FACTION_SPECIAL_ACTIONS if action.faction in faction)

    shadow_only = {"None / Normal Operations", "Initiate Jump Point!", "Run Silent!"}
    vorlon_only = {
        "None / Normal Operations",
        "Activate Jump Gate!",
        "All Stop!",
        "All Stop and Pivot!",
        "Come About!",
        "Initiate Jump Point!",
        "Run Silent!",
        "Regenerate!",
    }

    result: list[SpecialActionAvailability] = []
    for action in actions:
        allowed = True
        reason = ""
        if action.name == "None / Normal Operations":
            result.append(SpecialActionAvailability(action, True, ""))
            continue
        if unit.kind is UnitKind.CRAFT:
            allowed, reason = False, "Fighter and auxiliary craft may not attempt Special Actions."
        elif unit.is_destroyed:
            allowed, reason = False, "Destroyed or stricken ships may not attempt Special Actions."
        elif unit.is_adrift:
            allowed, reason = False, "This ship is Running Adrift."
        elif unit.special_actions_blocked:
            allowed, reason = False, "Skeleton Crew or an active critical hit prevents Special Actions."
        elif "shadow" in faction and action.name not in shadow_only:
            allowed, reason = False, "Shadow vessels are restricted to their published Special Actions."
        elif "vorlon" in faction and action.name not in vorlon_only:
            allowed, reason = False, "Vorlon vessels are restricted to their published Special Actions."
        elif action.name == "Give Me Ramming Speed!" and not unit.is_crippled:
            allowed, reason = False, "Only a Crippled ship may attempt this action."
        elif action.name == "Initiate Jump Point!" and not (
            _has_trait(unit, "jump engine")
            or _has_trait(unit, "advanced jump engine")
            or _has_trait(unit, "jump point")
        ):
            allowed, reason = False, "Requires a Jump Engine, Advanced Jump Engine, or Jump Point trait."
        elif action.name == "Launch Breaching Pods and Shuttles!":
            try:
                troops = int(str(unit.troops or "0").split("/")[0])
            except ValueError:
                troops = 0
            if troops <= 0:
                allowed, reason = False, "Requires Troops on board."
        elif action.name == "Scramble! Scramble!" and not (
            _has_trait(unit, "carrier") or any(child for child in unit.metadata if "craft" in str(child).casefold())
        ):
            # The builder does not currently embed a parent->children count in the
            # unit snapshot, so Carrier remains the reliable direct requirement.
            allowed, reason = False, "Requires carried fighters or a Carrier trait."
        elif action.name == "Cause Confusion" and not _has_trait(unit, "psychic crew"):
            allowed, reason = False, "Requires the Psychic Crew trait."
        result.append(SpecialActionAvailability(action, allowed, reason))
    return tuple(result)


def critical_targets(unit: TacticalUnitState, rule: CriticalRule) -> tuple[tuple[str, str], ...]:
    if rule.target_kind == "trait":
        return tuple((trait.trait_key, trait.name) for trait in unit.traits if not unit.trait_is_inactive(trait.trait_key))
    if rule.target_kind == "weapon":
        return tuple((weapon.weapon_key, f"{weapon.arc} - {weapon.name}") for weapon in unit.weapons if not unit.weapon_is_inactive(weapon.weapon_key))
    if rule.target_kind == "arc":
        arcs = []
        for weapon in unit.weapons:
            if weapon.arc and weapon.arc not in arcs:
                arcs.append(weapon.arc)
        return tuple((arc, arc) for arc in arcs)
    return ()


def apply_critical_rule(
    unit: TacticalUnitState,
    rule_key: str,
    *,
    damage_loss: int | None = None,
    crew_loss: int | None = None,
    target_keys: Iterable[str] = (),
    target_labels: Iterable[str] = (),
    applied_turn: int = 1,
    damage_multiplier: int = 1,
    include_solid_hit: bool = False,
) -> TacticalUnitState:
    rule = CRITICAL_RULE_BY_KEY[rule_key]
    resolved_damage = rule.fixed_damage if damage_loss is None else int(damage_loss)
    resolved_crew = rule.fixed_crew if crew_loss is None else int(crew_loss)
    if resolved_damage is None or resolved_crew is None:
        raise ValueError("rolled critical Damage and Crew totals must be entered")
    multiplier = int(damage_multiplier)
    if multiplier not in {1, 2, 3, 4}:
        raise ValueError("critical damage multiplier must be x1, x2, x3, or x4")
    solid_hit_loss = 1 if include_solid_hit else 0
    total_damage = (solid_hit_loss + max(0, resolved_damage)) * multiplier
    total_crew = (solid_hit_loss + max(0, resolved_crew)) * multiplier
    resolved_targets = tuple(str(item) for item in target_keys if str(item))
    resolved_labels = tuple(str(item) for item in target_labels if str(item))
    if rule.target_count and len(resolved_targets) < rule.target_count:
        raise ValueError(f"{rule.label} requires {rule.target_count} target selection(s)")
    critical = CriticalHitState.create(
        rule.label,
        rule.effect,
        rule_key=rule.key,
        system=rule.system,
        roll=rule.roll,
        damage_loss=total_damage,
        crew_loss=total_crew,
        speed_penalty=rule.speed_penalty,
        weapon_ad_penalty=rule.weapon_ad_penalty,
        no_special_actions=rule.no_special_actions,
        no_damage_control=rule.no_damage_control,
        no_damage_control_this_turn=rule.no_damage_control_this_turn,
        troop_penalty=rule.troop_penalty,
        power_fluctuations=rule.power_fluctuations,
        adrift=rule.adrift,
        target_kind=rule.target_kind,
        target_keys=resolved_targets[: rule.target_count or None],
        target_labels=resolved_labels[: rule.target_count or None],
        repairable=rule.repairable,
        applied_turn=max(1, int(applied_turn)),
        damage_multiplier=multiplier,
        before_damage=unit.damage.current,
        before_crew=unit.crew.current,
        before_crippled=unit.crippled,
        before_skeleton_crew=unit.skeleton_crew,
        before_destroyed=unit.destroyed,
        before_special_action=unit.special_action,
    )
    return unit.add_critical(critical)
