"""Game-neutral live battle-state models for the DFS Tactical Assistant.

Canonical platform and fleet data are immutable inputs. These models contain
only mutable state for one played game and are persisted separately from the
DFS database and platform-data modules.
"""
from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from enum import Enum
import re
from typing import Any, Mapping
from uuid import uuid4


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class GamePhase(str, Enum):
    SETUP = "setup"
    INITIATIVE = "initiative"
    MOVEMENT = "movement"
    ATTACK = "attack"
    END = "end"


class UnitKind(str, Enum):
    PLATFORM = "platform"
    CRAFT = "craft"


class UnitDisposition(str, Enum):
    OPERATIONAL = "operational"
    ADRIFT = "adrift"
    DESTROYED = "destroyed"
    SURRENDERED = "surrendered"
    WITHDRAWN = "withdrawn"


@dataclass(frozen=True, slots=True)
class TrackState:
    """One current/maximum tactical track."""

    maximum: int | None = None
    current: int | None = None
    threshold: int | None = None
    recovery: str = ""

    @classmethod
    def create(
        cls,
        maximum: int | None,
        *,
        threshold: int | None = None,
        recovery: str = "",
    ) -> "TrackState":
        if maximum is not None and maximum < 0:
            raise ValueError("maximum cannot be negative")
        if threshold is not None and threshold < 0:
            raise ValueError("threshold cannot be negative")
        return cls(
            maximum=maximum,
            current=maximum,
            threshold=threshold,
            recovery=recovery.strip(),
        )

    @property
    def available(self) -> bool:
        return self.maximum is not None

    def set_current(self, value: int) -> "TrackState":
        if self.maximum is None:
            raise ValueError("this track is not available for the unit")
        return replace(self, current=max(0, min(int(value), self.maximum)))

    def lose(self, amount: int) -> "TrackState":
        if amount < 0:
            raise ValueError("loss amount cannot be negative")
        if self.current is None:
            raise ValueError("this track is not available for the unit")
        return replace(self, current=max(0, self.current - amount))

    def restore(self, amount: int) -> "TrackState":
        if amount < 0:
            raise ValueError("restore amount cannot be negative")
        if self.current is None or self.maximum is None:
            raise ValueError("this track is not available for the unit")
        return replace(self, current=min(self.maximum, self.current + amount))

    def apply_expression(self, expression: str) -> "TrackState":
        """Apply an absolute value or a signed relative change.

        ``24`` sets the track to 24, ``-8`` removes eight, and ``+4`` restores
        four. Whitespace is ignored and the result is clamped to the legal
        range.
        """

        text = str(expression).strip().replace(" ", "")
        if not text:
            return self
        if not re.fullmatch(r"[+-]?\d+", text):
            raise ValueError("enter a whole number, +amount, or -amount")
        value = int(text)
        if text.startswith(("+", "-")):
            if self.current is None:
                raise ValueError("this track is not available for the unit")
            value = self.current + value
        return self.set_current(value)


@dataclass(frozen=True, slots=True)
class TraitState:
    trait_key: str
    name: str
    disabled: bool = False
    destroyed: bool = False


@dataclass(frozen=True, slots=True)
class WeaponState:
    weapon_key: str
    name: str
    arc: str = ""
    range_value: str = ""
    attack_dice: str = ""
    traits: str = ""
    disabled: bool = False
    destroyed: bool = False


@dataclass(frozen=True, slots=True)
class CriticalHitState:
    critical_id: str
    label: str
    effect: str = ""
    repaired: bool = False
    notes: str = ""
    rule_key: str = ""
    system: str = ""
    roll: str = ""
    damage_loss: int = 0
    crew_loss: int = 0
    speed_penalty: int = 0
    weapon_ad_penalty: int = 0
    no_special_actions: bool = False
    no_damage_control: bool = False
    no_damage_control_this_turn: bool = False
    troop_penalty: int = 0
    power_fluctuations: bool = False
    adrift: bool = False
    target_kind: str = ""
    target_keys: tuple[str, ...] = ()
    target_labels: tuple[str, ...] = ()
    repairable: bool = True
    applied_turn: int = 1
    damage_multiplier: int = 1
    before_damage: int | None = None
    before_crew: int | None = None
    before_crippled: bool = False
    before_skeleton_crew: bool = False
    before_destroyed: bool = False
    before_special_action: str = ""

    @classmethod
    def create(
        cls,
        label: str,
        effect: str = "",
        notes: str = "",
        **kwargs: Any,
    ) -> "CriticalHitState":
        return cls(
            critical_id=str(uuid4()),
            label=label.strip() or "Critical hit",
            effect=effect.strip(),
            notes=notes,
            **kwargs,
        )

    def can_repair_on_turn(self, turn_number: int) -> bool:
        """Return whether Damage Control may repair this result now."""

        return bool(
            self.repairable
            and not self.repaired
            and int(turn_number) > self.applied_turn
        )

    def repair_status(self, turn_number: int) -> str:
        if self.repaired:
            return "Repaired"
        if not self.repairable:
            return "Permanent"
        if int(turn_number) <= self.applied_turn:
            return "New"
        return "Repairable"


_SPEED_PATTERN = re.compile(r"^\s*(\d+(?:\.\d+)?)\s*(?:\"|in)?\s*$", re.IGNORECASE)
_TURN_PATTERN = re.compile(r"^\s*(\d+)\s*/\s*(\d+)", re.IGNORECASE)


def _format_decimal(value: Decimal) -> str:
    integral = value.to_integral_value()
    if value == integral:
        return str(int(integral))
    return format(value.normalize(), "f")


def _parse_speed(value: str) -> Decimal | None:
    match = _SPEED_PATTERN.match(str(value or ""))
    if not match:
        return None
    try:
        return Decimal(match.group(1))
    except InvalidOperation:
        return None


def _trait_base_name(name: str) -> str:
    text = str(name or "").strip()
    match = re.match(r"^(.+?)(?:\s+[+]?\d+(?:\s*/\s*[^ ]+)?)?$", text)
    return (match.group(1) if match else text).strip().casefold()


@dataclass(frozen=True, slots=True)
class TacticalUnitState:
    unit_id: str
    source_entry_id: str
    profile_id: int | None
    parent_unit_id: str | None
    kind: UnitKind
    platform_name: str
    vessel_name: str = ""
    instance_number: int = 1
    faction_name: str = ""
    fleet_name: str = ""
    priority_level: str = ""
    initiative: str = ""
    speed: str = ""
    turn: str = ""
    hull: str = ""
    troops: str = ""
    source_notes: tuple[str, ...] = ()
    metadata: Mapping[str, Any] = field(default_factory=dict)
    damage: TrackState = field(default_factory=TrackState)
    crew: TrackState = field(default_factory=TrackState)
    shields: TrackState = field(default_factory=TrackState)
    crew_quality: str = ""
    traits: tuple[TraitState, ...] = ()
    weapons: tuple[WeaponState, ...] = ()
    critical_hits: tuple[CriticalHitState, ...] = ()
    special_action: str = ""
    craft_status: str = "ready"
    disposition: UnitDisposition = UnitDisposition.OPERATIONAL
    notes: str = ""
    destroyed: bool = False
    crippled: bool = False
    skeleton_crew: bool = False
    crippled_correction: bool = False
    skeleton_crew_correction: bool = False

    @property
    def display_name(self) -> str:
        return self.vessel_name or self.platform_name

    @property
    def effective_craft_status(self) -> str:
        if self.kind is not UnitKind.CRAFT:
            return ""
        if self.is_destroyed:
            return "lost"
        return "launched" if self.craft_status.casefold() == "launched" else "ready"

    @property
    def is_destroyed(self) -> bool:
        # Damage at or below zero makes a ship Stricken and triggers the
        # disposition roll; it does not by itself decide that the ship is
        # Destroyed. Keeping the roll outcome separate also lets a mistaken
        # Destroyed selection be corrected through the Disposition control.
        return self.destroyed or self.disposition is UnitDisposition.DESTROYED

    @property
    def is_crippled(self) -> bool:
        if self.crippled_correction:
            return False
        if self.crippled:
            return True
        return bool(
            self.damage.threshold is not None
            and self.damage.current is not None
            and self.damage.current <= self.damage.threshold
        )

    @property
    def is_skeleton_crew(self) -> bool:
        if self.skeleton_crew_correction:
            return False
        if self.skeleton_crew:
            return True
        return bool(
            self.crew.threshold is not None
            and self.crew.current is not None
            and self.crew.current <= self.crew.threshold
        )

    @property
    def is_surrendered(self) -> bool:
        return self.disposition is UnitDisposition.SURRENDERED

    @property
    def is_withdrawn(self) -> bool:
        return self.disposition is UnitDisposition.WITHDRAWN

    @property
    def active_critical_hits(self) -> tuple[CriticalHitState, ...]:
        return tuple(critical for critical in self.critical_hits if not critical.repaired)

    @property
    def has_flight_computer(self) -> bool:
        for trait in self.traits:
            if _trait_base_name(trait.name) != "flight computer":
                continue
            if trait.disabled or trait.destroyed:
                continue
            if any(
                critical.target_kind == "trait" and trait.trait_key in critical.target_keys
                for critical in self.active_critical_hits
            ):
                continue
            return True
        return False

    @property
    def is_adrift(self) -> bool:
        if self.disposition is UnitDisposition.ADRIFT:
            return True
        if self.crew.available and self.crew.current == 0:
            return True
        return any(critical.adrift for critical in self.active_critical_hits)

    @property
    def effective_speed(self) -> str:
        original = _parse_speed(self.speed)
        if original is None:
            return self.speed
        current = original
        if self.is_crippled:
            current = current / Decimal(2)
        penalties = [critical.speed_penalty for critical in self.active_critical_hits]
        if penalties:
            current -= Decimal(max(penalties))
        current = max(Decimal(0), current)
        return _format_decimal(current)

    @property
    def adrift_movement(self) -> str:
        """Compulsory End Phase movement at half the current Speed."""

        current = _parse_speed(self.effective_speed)
        if current is None:
            return self.effective_speed
        return _format_decimal(max(Decimal(0), current / Decimal(2)))

    @property
    def effective_turn(self) -> str:
        original = str(self.turn or "")
        if not self.is_crippled:
            return original
        if original.strip().casefold() in {"sm", "super manoeuvrable", "super-manoeuvrable"}:
            return "2/45°"
        match = _TURN_PATTERN.match(original)
        if not match:
            return original
        turns = max(1, int(match.group(1)) - 1)
        return f"{turns}/45°"

    @property
    def speed_is_modified(self) -> bool:
        return bool(self.speed and self.effective_speed != self.speed)

    @property
    def turn_is_modified(self) -> bool:
        normalized_original = self.turn.replace("o", "°")
        return bool(self.turn and self.effective_turn != normalized_original)

    @property
    def shields_online(self) -> bool:
        if not self.shields.available or self.is_crippled or self.is_destroyed:
            return False
        shield_traits = [
            trait for trait in self.traits if _trait_base_name(trait.name) == "shields"
        ]
        return not shield_traits or any(
            not self.trait_is_inactive(trait.trait_key) for trait in shield_traits
        )

    @property
    def effective_troops(self) -> str:
        text = str(self.troops or "").strip()
        match = re.match(r"^(\d+)(.*)$", text)
        if not match:
            return text
        current = int(match.group(1))
        if self.is_skeleton_crew:
            current //= 2
        current = max(0, current - sum(
            critical.troop_penalty for critical in self.active_critical_hits
        ))
        return f"{current}{match.group(2)}"

    @property
    def troops_are_modified(self) -> bool:
        return bool(self.troops and self.effective_troops != self.troops)

    @property
    def weapon_ad_penalty(self) -> int:
        return sum(critical.weapon_ad_penalty for critical in self.active_critical_hits)

    @property
    def power_fluctuations(self) -> bool:
        return any(critical.power_fluctuations for critical in self.active_critical_hits)

    @property
    def special_actions_blocked(self) -> bool:
        if self.kind is UnitKind.CRAFT or self.is_destroyed or self.is_adrift:
            return True
        if self.is_skeleton_crew and not self.has_flight_computer:
            return True
        return any(critical.no_special_actions for critical in self.active_critical_hits)

    @property
    def damage_control_blocked(self) -> bool:
        return any(critical.no_damage_control for critical in self.active_critical_hits)

    def damage_control_blocked_on_turn(self, turn_number: int) -> bool:
        if self.damage_control_blocked:
            return True
        return any(
            critical.no_damage_control_this_turn
            and critical.applied_turn == int(turn_number)
            for critical in self.active_critical_hits
        )

    def damage_control_block_reason(self, turn_number: int) -> str:
        if any(critical.no_damage_control for critical in self.active_critical_hits):
            return "Not permitted - an active critical prevents Damage Control."
        if any(
            critical.no_damage_control_this_turn
            and critical.applied_turn == int(turn_number)
            for critical in self.active_critical_hits
        ):
            return "Not permitted this turn - an active Hull Breach prevents Damage Control."
        return ""

    @property
    def damage_control_penalty(self) -> int:
        critical_penalty = sum(
            1
            for critical in self.active_critical_hits
            if critical.rule_key == "crew-multiple-fires"
        )
        skeleton_penalty = 0 if self.has_flight_computer else (2 if self.is_skeleton_crew else 0)
        return critical_penalty + skeleton_penalty

    @property
    def has_self_repairing(self) -> bool:
        for trait in self.traits:
            normalized = trait.name.casefold().replace("‑", "-").replace("–", "-")
            if not (normalized.startswith("self-repairing") or normalized.startswith("self repairing")):
                continue
            if not self.trait_is_inactive(trait.trait_key):
                return True
        return False

    @property
    def damage_control_modifiers(self) -> tuple[tuple[str, int], ...]:
        modifiers: list[tuple[str, int]] = []
        if self.is_skeleton_crew and not self.has_flight_computer:
            modifiers.append(("Skeleton Crew", -2))
        multiple_fires = sum(
            1
            for critical in self.active_critical_hits
            if critical.rule_key == "crew-multiple-fires"
        )
        if multiple_fires:
            modifiers.append((
                "Multiple Fires" if multiple_fires == 1 else f"Multiple Fires x{multiple_fires}",
                -multiple_fires,
            ))
        if self.has_self_repairing:
            modifiers.append(("Self-Repairing", 1))
        if self.special_action.casefold() == "all hands on deck!".casefold():
            modifiers.append(("All Hands on Deck!", 2))
        return tuple(modifiers)

    def damage_control_equation(self, turn_number: int) -> str:
        blocked = self.damage_control_block_reason(turn_number)
        if blocked:
            return blocked

        crew_quality = str(self.crew_quality or "?").strip() or "?"
        terms = ["1D6", f"+ CQ {crew_quality}"]
        for label, modifier in self.damage_control_modifiers:
            sign = "+" if modifier >= 0 else "-"
            terms.append(f"{sign} {abs(modifier)} {label}")
        equation = " ".join(terms)

        match = re.search(r"-?\d+", crew_quality)
        required_note = ""
        if match:
            fixed = int(match.group()) + sum(value for _label, value in self.damage_control_modifiers)
            required = 9 - fixed
            if required <= 1:
                required_note = " Need 1+ on the die."
            elif required <= 6:
                required_note = f" Need {required}+ on the die."
            else:
                required_note = f" Need {required}+ on the die; another modifier is required."

        flight_computer_note = (
            " Flight Computer ignores the Skeleton Crew -2 penalty."
            if self.is_skeleton_crew and self.has_flight_computer
            else ""
        )
        return f"Roll {equation}; 9+ repairs one eligible critical.{required_note}{flight_computer_note}"

    @property
    def firing_restrictions(self) -> tuple[str, ...]:
        restrictions: list[str] = []
        if self.is_crippled:
            restrictions.append("Crippled: only one weapon per fire arc may be used.")
        if self.is_skeleton_crew and not self.has_flight_computer:
            restrictions.append("Skeleton Crew: only one weapon system may be fired this turn.")
        if self.power_fluctuations:
            restrictions.append("Power Fluctuations: roll 4+ before firing each weapon.")
        return tuple(restrictions)

    def trait_is_inactive(self, trait_key: str) -> bool:
        trait = next((item for item in self.traits if item.trait_key == trait_key), None)
        if trait is None:
            raise KeyError(f"Unknown trait key: {trait_key}")
        if trait.disabled or trait.destroyed:
            return True
        return any(
            critical.target_kind == "trait" and trait_key in critical.target_keys
            for critical in self.active_critical_hits
        )

    def trait_status(self, trait_key: str) -> str:
        trait = next((item for item in self.traits if item.trait_key == trait_key), None)
        if trait is None:
            raise KeyError(f"Unknown trait key: {trait_key}")
        if trait.destroyed:
            return "Destroyed"
        if trait.disabled:
            return "Disabled"
        if any(
            critical.target_kind == "trait" and trait_key in critical.target_keys
            for critical in self.active_critical_hits
        ):
            return "Critical"
        if self.is_crippled and _trait_base_name(trait.name) == "shields":
            return "Offline (Crippled)"
        return "Operational"

    def weapon_is_inactive(self, weapon_key: str) -> bool:
        weapon = next((item for item in self.weapons if item.weapon_key == weapon_key), None)
        if weapon is None:
            raise KeyError(f"Unknown weapon key: {weapon_key}")
        if weapon.disabled or weapon.destroyed:
            return True
        for critical in self.active_critical_hits:
            if critical.target_kind == "weapon" and weapon_key in critical.target_keys:
                return True
            if critical.target_kind == "arc" and weapon.arc in critical.target_keys:
                return True
        return False

    def weapon_status(self, weapon_key: str) -> str:
        weapon = next((item for item in self.weapons if item.weapon_key == weapon_key), None)
        if weapon is None:
            raise KeyError(f"Unknown weapon key: {weapon_key}")
        if weapon.destroyed:
            return "Destroyed"
        if weapon.disabled:
            return "Disabled"
        for critical in self.active_critical_hits:
            if critical.target_kind == "weapon" and weapon_key in critical.target_keys:
                return "Critical"
            if critical.target_kind == "arc" and weapon.arc in critical.target_keys:
                return "Arc Offline"
        if self.power_fluctuations:
            return "Roll 4+"
        return "Operational"

    def effective_attack_dice(self, weapon: WeaponState) -> str:
        text = str(weapon.attack_dice or "").strip()
        if self.weapon_ad_penalty <= 0:
            return text
        if re.fullmatch(r"\d+", text):
            return str(max(0, int(text) - self.weapon_ad_penalty))
        return f"{text} (-{self.weapon_ad_penalty} AD)" if text else f"-{self.weapon_ad_penalty} AD"

    def set_damage_current(self, value: int) -> "TacticalUnitState":
        if self.damage.maximum is None:
            raise ValueError("this track is not available for the unit")
        previous = self.damage.current
        # Damage may continue below zero because the negative amount is the
        # modifier to the Stricken Ship Damage Table roll. Only the upper end
        # is capped at the certified starting Damage value.
        updated = replace(
            self.damage,
            current=min(int(value), int(self.damage.maximum)),
        )
        threshold = updated.threshold
        crossed = bool(
            threshold is not None
            and updated.current is not None
            and updated.current <= threshold
            and (previous is None or previous > threshold)
        )
        correction = self.crippled_correction
        if threshold is not None and updated.current is not None and updated.current > threshold:
            correction = False
        if crossed:
            correction = False
        return replace(
            self,
            damage=updated,
            crippled=(self.crippled or crossed) and not correction,
            crippled_correction=correction,
        )

    def apply_damage_expression(self, expression: str) -> "TacticalUnitState":
        text = str(expression).strip().replace(" ", "")
        if not text:
            return self
        if not re.fullmatch(r"[+-]?\d+", text):
            raise ValueError("enter a whole number, +amount, or -amount")
        value = int(text)
        if text.startswith(("+", "-")):
            if self.damage.current is None:
                raise ValueError("this track is not available for the unit")
            value = self.damage.current + value
        return self.set_damage_current(value)

    def lose_damage(self, amount: int) -> "TacticalUnitState":
        if amount < 0:
            raise ValueError("loss amount cannot be negative")
        if self.damage.current is None:
            raise ValueError("this track is not available for the unit")
        return self.set_damage_current(self.damage.current - amount)

    def restore_damage(self, amount: int) -> "TacticalUnitState":
        if amount < 0:
            raise ValueError("restore amount cannot be negative")
        if self.damage.current is None:
            raise ValueError("this track is not available for the unit")
        return self.set_damage_current(self.damage.current + amount)

    def set_crew_current(self, value: int) -> "TacticalUnitState":
        previous = self.crew.current
        updated = self.crew.set_current(value)
        threshold = updated.threshold
        crossed = bool(
            threshold is not None
            and updated.current is not None
            and updated.current <= threshold
            and (previous is None or previous > threshold)
        )
        correction = self.skeleton_crew_correction
        if threshold is not None and updated.current is not None and updated.current > threshold:
            correction = False
        if crossed:
            correction = False
        return replace(
            self,
            crew=updated,
            skeleton_crew=(self.skeleton_crew or crossed) and not correction,
            skeleton_crew_correction=correction,
        )

    def apply_crew_expression(self, expression: str) -> "TacticalUnitState":
        updated = self.crew.apply_expression(expression)
        return self.set_crew_current(int(updated.current or 0))

    def lose_crew(self, amount: int) -> "TacticalUnitState":
        updated = self.crew.lose(amount)
        return self.set_crew_current(int(updated.current or 0))

    def restore_crew(self, amount: int) -> "TacticalUnitState":
        updated = self.crew.restore(amount)
        return self.set_crew_current(int(updated.current or 0))

    def set_shields_current(self, value: int) -> "TacticalUnitState":
        return replace(self, shields=self.shields.set_current(value))

    def apply_shields_expression(self, expression: str) -> "TacticalUnitState":
        return replace(self, shields=self.shields.apply_expression(expression))

    def lose_shields(self, amount: int) -> "TacticalUnitState":
        return replace(self, shields=self.shields.lose(amount))

    def restore_shields(self, amount: int) -> "TacticalUnitState":
        return replace(self, shields=self.shields.restore(amount))

    def mark_destroyed(self, destroyed: bool = True) -> "TacticalUnitState":
        return replace(
            self,
            destroyed=bool(destroyed),
            disposition=(
                UnitDisposition.DESTROYED if destroyed else UnitDisposition.OPERATIONAL
            ),
        )

    def set_disposition(self, disposition: UnitDisposition | str) -> "TacticalUnitState":
        resolved = (
            disposition
            if isinstance(disposition, UnitDisposition)
            else UnitDisposition(str(disposition).strip().casefold())
        )
        if self.kind is UnitKind.CRAFT and resolved not in {
            UnitDisposition.OPERATIONAL,
            UnitDisposition.DESTROYED,
        }:
            raise ValueError("fighter flights use Ready, Launched, or Lost status")
        return replace(
            self,
            disposition=resolved,
            destroyed=(resolved is UnitDisposition.DESTROYED),
        )

    def correct_crippled_status(self) -> "TacticalUnitState":
        return replace(self, crippled=False, crippled_correction=True)

    def correct_skeleton_crew_status(self) -> "TacticalUnitState":
        return replace(self, skeleton_crew=False, skeleton_crew_correction=True)

    def set_crew_quality(self, crew_quality: str) -> "TacticalUnitState":
        return replace(self, crew_quality=crew_quality.strip())

    def set_vessel_name(self, vessel_name: str) -> "TacticalUnitState":
        if self.kind is not UnitKind.PLATFORM:
            raise ValueError("only platforms can be assigned a vessel name")
        return replace(self, vessel_name=str(vessel_name or "").strip())

    def set_special_action(self, action: str) -> "TacticalUnitState":
        return replace(self, special_action=action.strip())

    def set_craft_status(self, status: str) -> "TacticalUnitState":
        if self.kind is not UnitKind.CRAFT:
            raise ValueError("only craft can have a ready/launched status")
        resolved = status.strip().casefold()
        if resolved not in {"ready", "launched"}:
            raise ValueError("craft status must be 'ready' or 'launched'")
        return replace(self, craft_status=resolved)

    def set_notes(self, notes: str) -> "TacticalUnitState":
        return replace(self, notes=notes)

    def set_trait_disabled(self, trait_key: str, disabled: bool = True) -> "TacticalUnitState":
        return self._replace_trait(trait_key, disabled=bool(disabled))

    def set_trait_destroyed(self, trait_key: str, destroyed: bool = True) -> "TacticalUnitState":
        return self._replace_trait(trait_key, destroyed=bool(destroyed))

    def _replace_trait(self, trait_key: str, **changes: Any) -> "TacticalUnitState":
        found = False
        updated: list[TraitState] = []
        for trait in self.traits:
            if trait.trait_key == trait_key:
                updated.append(replace(trait, **changes))
                found = True
            else:
                updated.append(trait)
        if not found:
            raise KeyError(f"Unknown trait key: {trait_key}")
        return replace(self, traits=tuple(updated))

    def set_weapon_disabled(self, weapon_key: str, disabled: bool = True) -> "TacticalUnitState":
        return self._replace_weapon(weapon_key, disabled=bool(disabled))

    def set_weapon_destroyed(self, weapon_key: str, destroyed: bool = True) -> "TacticalUnitState":
        return self._replace_weapon(weapon_key, destroyed=bool(destroyed))

    def _replace_weapon(self, weapon_key: str, **changes: Any) -> "TacticalUnitState":
        found = False
        updated: list[WeaponState] = []
        for weapon in self.weapons:
            if weapon.weapon_key == weapon_key:
                updated.append(replace(weapon, **changes))
                found = True
            else:
                updated.append(weapon)
        if not found:
            raise KeyError(f"Unknown weapon key: {weapon_key}")
        return replace(self, weapons=tuple(updated))

    def add_critical(self, critical: CriticalHitState) -> "TacticalUnitState":
        updated = replace(self, critical_hits=(*self.critical_hits, critical))
        if critical.damage_loss and updated.damage.available:
            updated = updated.lose_damage(critical.damage_loss)
        if critical.crew_loss and updated.crew.available:
            updated = updated.lose_crew(critical.crew_loss)
        if critical.no_special_actions:
            updated = replace(updated, special_action="")
        return updated

    def set_critical_repaired(
        self,
        critical_id: str,
        repaired: bool = True,
        *,
        current_turn: int | None = None,
    ) -> "TacticalUnitState":
        found = False
        updated: list[CriticalHitState] = []
        for critical in self.critical_hits:
            if critical.critical_id == critical_id:
                if repaired and not critical.repairable:
                    raise ValueError("Vital Systems critical hits cannot be repaired")
                if (
                    repaired
                    and current_turn is not None
                    and not critical.can_repair_on_turn(current_turn)
                ):
                    raise ValueError(
                        "A critical hit cannot be repaired in the same turn it was suffered"
                    )
                updated.append(replace(critical, repaired=bool(repaired)))
                found = True
            else:
                updated.append(critical)
        if not found:
            raise KeyError(f"Unknown critical ID: {critical_id}")
        return replace(self, critical_hits=tuple(updated))

    def undo_last_critical(self) -> "TacticalUnitState":
        """Remove the most recently applied critical and restore its prior state.

        New criticals store an exact pre-application snapshot. Older saved-game
        criticals remain compatible and fall back to restoring their recorded
        Damage and Crew losses.
        """

        if not self.critical_hits:
            return self
        critical = self.critical_hits[-1]
        remaining = self.critical_hits[:-1]
        has_snapshot = critical.before_damage is not None or critical.before_crew is not None

        damage = self.damage
        crew = self.crew
        if damage.available:
            if critical.before_damage is not None:
                damage = replace(damage, current=min(critical.before_damage, damage.maximum or 0))
            elif damage.current is not None and damage.maximum is not None:
                damage = replace(damage, current=min(damage.maximum, damage.current + critical.damage_loss))
        if crew.available:
            if critical.before_crew is not None:
                crew = replace(crew, current=max(0, min(critical.before_crew, crew.maximum or 0)))
            elif crew.current is not None and crew.maximum is not None:
                crew = replace(crew, current=min(crew.maximum, crew.current + critical.crew_loss))

        return replace(
            self,
            damage=damage,
            crew=crew,
            critical_hits=remaining,
            crippled=(critical.before_crippled if has_snapshot else self.crippled),
            skeleton_crew=(
                critical.before_skeleton_crew if has_snapshot else self.skeleton_crew
            ),
            destroyed=(critical.before_destroyed if has_snapshot else self.destroyed),
            special_action=(
                critical.before_special_action if has_snapshot else self.special_action
            ),
        )


@dataclass(frozen=True, slots=True)
class TacticalGameState:
    schema_version: int
    game_id: str
    name: str
    game_system_id: str
    source_fleet_id: str
    source_fleet_name: str
    turn_number: int = 1
    phase: GamePhase = GamePhase.SETUP
    units: tuple[TacticalUnitState, ...] = ()
    notes: str = ""
    metadata: Mapping[str, Any] = field(default_factory=dict)
    scenario_key: str = ""
    scenario_priority: str = ""
    player_role: str = ""
    scenario_objectives: Mapping[str, Any] = field(default_factory=dict)
    victory_points: int = 0
    opponent_victory_points: int = 0
    battle_report_notes: str = ""
    ended_at: str = ""
    created_at: str = ""
    updated_at: str = ""

    CURRENT_SCHEMA_VERSION = 1

    @classmethod
    def create(
        cls,
        *,
        name: str,
        game_system_id: str,
        source_fleet_id: str,
        source_fleet_name: str,
        units: tuple[TacticalUnitState, ...] = (),
        metadata: Mapping[str, Any] | None = None,
    ) -> "TacticalGameState":
        now = _utc_now()
        return cls(
            schema_version=cls.CURRENT_SCHEMA_VERSION,
            game_id=str(uuid4()),
            name=name.strip() or f"{source_fleet_name} Battle",
            game_system_id=game_system_id,
            source_fleet_id=source_fleet_id,
            source_fleet_name=source_fleet_name,
            units=units,
            metadata=dict(metadata or {}),
            created_at=now,
            updated_at=now,
        )

    def get_unit(self, unit_id: str) -> TacticalUnitState:
        for unit in self.units:
            if unit.unit_id == unit_id:
                return unit
        raise KeyError(f"Unknown tactical unit ID: {unit_id}")

    def replace_unit(self, unit: TacticalUnitState) -> "TacticalGameState":
        found = False
        updated: list[TacticalUnitState] = []
        for existing in self.units:
            if existing.unit_id == unit.unit_id:
                updated.append(unit)
                found = True
            else:
                updated.append(existing)
        if not found:
            raise KeyError(f"Unknown tactical unit ID: {unit.unit_id}")
        return replace(self, units=tuple(updated), updated_at=_utc_now())

    def rename(self, name: str) -> "TacticalGameState":
        resolved = name.strip()
        if not resolved:
            raise ValueError("game name cannot be blank")
        return replace(self, name=resolved, updated_at=_utc_now())

    def set_turn_number(self, turn_number: int) -> "TacticalGameState":
        resolved = int(turn_number)
        if resolved < 1:
            raise ValueError("turn number must be at least 1")
        return replace(self, turn_number=resolved, updated_at=_utc_now())

    def set_phase(self, phase: GamePhase) -> "TacticalGameState":
        return replace(self, phase=phase, updated_at=_utc_now())

    def set_notes(self, notes: str) -> "TacticalGameState":
        return replace(self, notes=notes, updated_at=_utc_now())

    def set_scenario(
        self,
        scenario_key: str,
        *,
        priority_level: str | None = None,
        player_role: str | None = None,
    ) -> "TacticalGameState":
        return replace(
            self,
            scenario_key=str(scenario_key or "").strip(),
            scenario_priority=(
                self.scenario_priority if priority_level is None else str(priority_level).strip()
            ),
            player_role=(self.player_role if player_role is None else str(player_role).strip()),
            scenario_objectives={},
            updated_at=_utc_now(),
        )

    def set_scenario_priority(self, priority_level: str) -> "TacticalGameState":
        return replace(self, scenario_priority=str(priority_level).strip(), updated_at=_utc_now())

    def set_player_role(self, role: str) -> "TacticalGameState":
        return replace(self, player_role=str(role).strip(), updated_at=_utc_now())

    def set_scenario_objectives(self, objectives: Mapping[str, Any]) -> "TacticalGameState":
        return replace(self, scenario_objectives=dict(objectives), updated_at=_utc_now())

    def advance_turn(self) -> "TacticalGameState":
        cleared_units = tuple(replace(unit, special_action="") for unit in self.units)
        return replace(
            self,
            turn_number=self.turn_number + 1,
            phase=GamePhase.INITIATIVE,
            units=cleared_units,
            updated_at=_utc_now(),
        )

    def end_game(
        self,
        *,
        victory_points: int,
        opponent_victory_points: int,
        notes: str = "",
    ) -> "TacticalGameState":
        now = _utc_now()
        return replace(
            self,
            phase=GamePhase.END,
            victory_points=max(0, int(victory_points)),
            opponent_victory_points=max(0, int(opponent_victory_points)),
            battle_report_notes=notes,
            ended_at=now,
            updated_at=now,
        )

    @property
    def battle_result(self) -> str:
        if self.victory_points > self.opponent_victory_points:
            return "Victory"
        if self.victory_points < self.opponent_victory_points:
            return "Defeat"
        return "Draw"

    @property
    def craft_losses(self) -> int:
        return sum(1 for unit in self.units if unit.kind is UnitKind.CRAFT and unit.is_destroyed)
