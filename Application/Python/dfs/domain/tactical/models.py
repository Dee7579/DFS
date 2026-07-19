"""Game-neutral live battle-state models for the DFS Tactical Assistant.

Canonical platform and fleet data are immutable inputs.  These models contain
only the mutable state of one played game and are persisted separately from the
DFS database and platform-data modules.
"""
from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import datetime, timezone
from enum import Enum
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


@dataclass(frozen=True, slots=True)
class TrackState:
    """One current/maximum tactical track.

    ``threshold`` stores a printed crippled or skeleton-crew threshold when the
    source profile provides one.  ``recovery`` stores non-numeric recovery text,
    such as a shield regeneration value of ``2D6``.
    """

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


@dataclass(frozen=True, slots=True)
class TraitState:
    trait_key: str
    name: str
    disabled: bool = False


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

    @classmethod
    def create(cls, label: str, effect: str = "", notes: str = "") -> "CriticalHitState":
        return cls(
            critical_id=str(uuid4()),
            label=label.strip() or "Critical hit",
            effect=effect.strip(),
            notes=notes,
        )


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
    notes: str = ""
    destroyed: bool = False

    @property
    def display_name(self) -> str:
        return self.vessel_name or self.platform_name

    @property
    def is_destroyed(self) -> bool:
        if self.destroyed:
            return True
        return bool(self.damage.maximum is not None and self.damage.current == 0)

    def lose_damage(self, amount: int) -> "TacticalUnitState":
        updated = self.damage.lose(amount)
        return replace(self, damage=updated, destroyed=self.destroyed or updated.current == 0)

    def restore_damage(self, amount: int) -> "TacticalUnitState":
        return replace(self, damage=self.damage.restore(amount))

    def lose_crew(self, amount: int) -> "TacticalUnitState":
        return replace(self, crew=self.crew.lose(amount))

    def restore_crew(self, amount: int) -> "TacticalUnitState":
        return replace(self, crew=self.crew.restore(amount))

    def lose_shields(self, amount: int) -> "TacticalUnitState":
        return replace(self, shields=self.shields.lose(amount))

    def restore_shields(self, amount: int) -> "TacticalUnitState":
        return replace(self, shields=self.shields.restore(amount))

    def mark_destroyed(self, destroyed: bool = True) -> "TacticalUnitState":
        return replace(self, destroyed=bool(destroyed))

    def set_special_action(self, action: str) -> "TacticalUnitState":
        return replace(self, special_action=action.strip())

    def set_trait_disabled(self, trait_key: str, disabled: bool = True) -> "TacticalUnitState":
        found = False
        updated: list[TraitState] = []
        for trait in self.traits:
            if trait.trait_key == trait_key:
                updated.append(replace(trait, disabled=bool(disabled)))
                found = True
            else:
                updated.append(trait)
        if not found:
            raise KeyError(f"Unknown trait key: {trait_key}")
        return replace(self, traits=tuple(updated))

    def set_weapon_disabled(self, weapon_key: str, disabled: bool = True) -> "TacticalUnitState":
        found = False
        updated: list[WeaponState] = []
        for weapon in self.weapons:
            if weapon.weapon_key == weapon_key:
                updated.append(replace(weapon, disabled=bool(disabled)))
                found = True
            else:
                updated.append(weapon)
        if not found:
            raise KeyError(f"Unknown weapon key: {weapon_key}")
        return replace(self, weapons=tuple(updated))

    def set_weapon_destroyed(self, weapon_key: str, destroyed: bool = True) -> "TacticalUnitState":
        found = False
        updated: list[WeaponState] = []
        for weapon in self.weapons:
            if weapon.weapon_key == weapon_key:
                updated.append(replace(weapon, destroyed=bool(destroyed)))
                found = True
            else:
                updated.append(weapon)
        if not found:
            raise KeyError(f"Unknown weapon key: {weapon_key}")
        return replace(self, weapons=tuple(updated))

    def add_critical(self, critical: CriticalHitState) -> "TacticalUnitState":
        return replace(self, critical_hits=(*self.critical_hits, critical))

    def set_critical_repaired(self, critical_id: str, repaired: bool = True) -> "TacticalUnitState":
        found = False
        updated: list[CriticalHitState] = []
        for critical in self.critical_hits:
            if critical.critical_id == critical_id:
                updated.append(replace(critical, repaired=bool(repaired)))
                found = True
            else:
                updated.append(critical)
        if not found:
            raise KeyError(f"Unknown critical ID: {critical_id}")
        return replace(self, critical_hits=tuple(updated))


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

    def set_phase(self, phase: GamePhase) -> "TacticalGameState":
        return replace(self, phase=phase, updated_at=_utc_now())

    def advance_turn(self) -> "TacticalGameState":
        return replace(
            self,
            turn_number=self.turn_number + 1,
            phase=GamePhase.INITIATIVE,
            updated_at=_utc_now(),
        )

    @property
    def craft_losses(self) -> int:
        return sum(1 for unit in self.units if unit.kind is UnitKind.CRAFT and unit.is_destroyed)
