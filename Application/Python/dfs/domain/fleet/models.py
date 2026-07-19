"""Game-neutral fleet domain models.

The fleet domain stores player intent. Construction profiles interpret that
intent for a particular game system, tournament pack, campaign, or community
points system.
"""
from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
from typing import Any, Mapping
from uuid import uuid4


class CostMode(str, Enum):
    PRIORITY = "priority"
    POINTS = "points"
    NONE = "none"


class ValidationSeverity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


@dataclass(frozen=True, slots=True)
class FleetEntry:
    """A selected fleet-list profile and its quantity.

    `profile_id` deliberately identifies an ACTA profile rather than a
    canonical platform. The same hull can have different legal profiles in
    different fleets or eras.
    """

    entry_id: str
    profile_id: int
    quantity: int = 1
    options: Mapping[str, Any] = field(default_factory=dict)
    vessel_name: str = ""
    notes: str = ""

    @classmethod
    def create(
        cls,
        profile_id: int,
        quantity: int = 1,
        options: Mapping[str, Any] | None = None,
        vessel_name: str = "",
        notes: str = "",
    ) -> "FleetEntry":
        if profile_id <= 0:
            raise ValueError("profile_id must be positive")
        if quantity <= 0:
            raise ValueError("quantity must be positive")
        return cls(
            entry_id=str(uuid4()),
            profile_id=profile_id,
            quantity=quantity,
            options=dict(options or {}),
            vessel_name=vessel_name.strip(),
            notes=notes,
        )

    def with_quantity(self, quantity: int) -> "FleetEntry":
        if quantity <= 0:
            raise ValueError("quantity must be positive")
        return replace(self, quantity=quantity)

    def with_vessel_name(self, vessel_name: str) -> "FleetEntry":
        return replace(self, vessel_name=vessel_name.strip())


@dataclass(frozen=True, slots=True)
class Fleet:
    schema_version: int
    fleet_id: str
    name: str
    game_system_id: str
    construction_profile_id: str
    faction_id: int | None
    fleet_list_id: int | None
    selected_year: int | None
    entries: tuple[FleetEntry, ...] = ()
    notes: str = ""
    metadata: Mapping[str, Any] = field(default_factory=dict)
    created_at: str = ""
    updated_at: str = ""

    CURRENT_SCHEMA_VERSION = 1

    @classmethod
    def create(
        cls,
        name: str,
        game_system_id: str,
        construction_profile_id: str,
        faction_id: int | None = None,
        fleet_list_id: int | None = None,
        selected_year: int | None = None,
    ) -> "Fleet":
        now = datetime.now(timezone.utc).isoformat()
        return cls(
            schema_version=cls.CURRENT_SCHEMA_VERSION,
            fleet_id=str(uuid4()),
            name=name.strip() or "Untitled Fleet",
            game_system_id=game_system_id,
            construction_profile_id=construction_profile_id,
            faction_id=faction_id,
            fleet_list_id=fleet_list_id,
            selected_year=selected_year,
            created_at=now,
            updated_at=now,
        )

    def add_entry(self, entry: FleetEntry) -> "Fleet":
        return replace(
            self,
            entries=(*self.entries, entry),
            updated_at=datetime.now(timezone.utc).isoformat(),
        )

    def replace_entries(self, entries: tuple[FleetEntry, ...]) -> "Fleet":
        return replace(
            self,
            entries=entries,
            updated_at=datetime.now(timezone.utc).isoformat(),
        )


@dataclass(frozen=True, slots=True)
class FleetCost:
    mode: CostMode
    value: Decimal | None = None
    priority: str | None = None
    label: str = ""


@dataclass(frozen=True, slots=True)
class ValidationMessage:
    code: str
    severity: ValidationSeverity
    message: str
    entry_id: str | None = None


@dataclass(frozen=True, slots=True)
class ValidationResult:
    messages: tuple[ValidationMessage, ...] = ()

    @property
    def errors(self) -> tuple[ValidationMessage, ...]:
        return tuple(m for m in self.messages if m.severity is ValidationSeverity.ERROR)

    @property
    def warnings(self) -> tuple[ValidationMessage, ...]:
        return tuple(m for m in self.messages if m.severity is ValidationSeverity.WARNING)

    @property
    def is_valid(self) -> bool:
        return not self.errors


@dataclass(frozen=True, slots=True)
class FleetSummary:
    cost_mode: CostMode
    total_points: Decimal | None = None
    priority_counts: Mapping[str, int] = field(default_factory=dict)
    budget_label: str = ""
    remaining_label: str = ""
    validation: ValidationResult = field(default_factory=ValidationResult)
