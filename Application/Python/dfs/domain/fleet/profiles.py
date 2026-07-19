"""Construction-profile contracts and built-in generic profiles."""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Mapping, Protocol

from dfs.domain.fleet.models import (
    CostMode,
    Fleet,
    FleetCost,
    FleetSummary,
    ValidationResult,
)


class FleetConstructionProfile(Protocol):
    profile_id: str
    display_name: str
    cost_mode: CostMode

    def summarize(self, fleet: Fleet, resolved_entries: Mapping[str, object]) -> FleetSummary: ...

    def validate(self, fleet: Fleet, resolved_entries: Mapping[str, object]) -> ValidationResult: ...


@dataclass(frozen=True, slots=True)
class PointsConstructionProfile:
    profile_id: str = "generic_points"
    display_name: str = "Points — Generic"
    cost_mode: CostMode = CostMode.POINTS

    def validate(self, fleet: Fleet, resolved_entries: Mapping[str, object]) -> ValidationResult:
        return ValidationResult()

    def summarize(self, fleet: Fleet, resolved_entries: Mapping[str, object]) -> FleetSummary:
        total = Decimal("0")
        for entry in fleet.entries:
            value = entry.options.get("points")
            if value is not None:
                total += Decimal(str(value)) * entry.quantity
        return FleetSummary(
            cost_mode=self.cost_mode,
            total_points=total,
            budget_label=f"{total:g} points",
            validation=self.validate(fleet, resolved_entries),
        )


@dataclass(frozen=True, slots=True)
class NoValidationConstructionProfile:
    profile_id: str = "no_validation"
    display_name: str = "No Validation"
    cost_mode: CostMode = CostMode.NONE

    def validate(self, fleet: Fleet, resolved_entries: Mapping[str, object]) -> ValidationResult:
        return ValidationResult()

    def summarize(self, fleet: Fleet, resolved_entries: Mapping[str, object]) -> FleetSummary:
        return FleetSummary(cost_mode=self.cost_mode, validation=ValidationResult())
