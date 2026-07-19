"""Standard Babylon 5 ACTA construction profile."""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from typing import Mapping

from dfs.domain.catalog import PlatformProfile
from dfs.domain.fleet.models import CostMode, Fleet, FleetSummary, ValidationMessage, ValidationResult, ValidationSeverity
from dfs.domain.fleet.priority import PRIORITIES, format_ancient_remaining, format_remaining_choices
from dfs.domain.fleet.replacements import replacement_patrol_choices
from dfs.domain.fleet.grouped_purchases import purchased_choice_count
from dfs.services.fleet.b5_acta_rules import build_b5_acta_core_rule_engine
from dfs.services.fleet.rule_engine import FleetRuleEngine


@dataclass(frozen=True, slots=True)
class B5ACTAStandardPriorityProfile:
    profile_id: str = "b5_acta_priority_standard"
    display_name: str = "B5 ACTA Standard Priority"
    cost_mode: CostMode = CostMode.PRIORITY
    rule_engine: FleetRuleEngine = field(default_factory=build_b5_acta_core_rule_engine, compare=False)

    def _budget_settings(self, fleet: Fleet) -> tuple[str, int]:
        priority = str(fleet.metadata.get("scenario_priority", "Raid"))
        points = int(fleet.metadata.get("fleet_allocation_points", 1))
        return priority, points

    def validate(
        self,
        fleet: Fleet,
        resolved_entries: Mapping[str, PlatformProfile | None],
    ) -> ValidationResult:
        return self.rule_engine.validate(fleet, resolved_entries)

    def summarize(
        self,
        fleet: Fleet,
        resolved_entries: Mapping[str, PlatformProfile | None],
    ) -> FleetSummary:
        counts: Counter[str] = Counter()
        for entry in fleet.entries:
            profile = resolved_entries.get(entry.entry_id)
            if profile is not None and profile.priority_level in PRIORITIES:
                counts[profile.priority_level] += purchased_choice_count(entry.profile_id, entry.quantity, entry.options)
            patrol_cost = replacement_patrol_choices(entry.options)
            if patrol_cost:
                counts["Patrol"] += patrol_cost
        scenario_priority, fap = self._budget_settings(fleet)
        validation = self.validate(fleet, resolved_entries)
        ancient_count = sum(
            entry.quantity for entry in fleet.entries
            if (resolved_entries.get(entry.entry_id) is not None
                and resolved_entries[entry.entry_id].priority_level == "Ancient")
        )
        if fleet.fleet_list_id == 19:
            counts["Ancient"] = ancient_count
            remaining_label = format_ancient_remaining(scenario_priority, fap, ancient_count)
        else:
            remaining_label = format_remaining_choices(scenario_priority, fap, counts)
        return FleetSummary(
            cost_mode=self.cost_mode,
            priority_counts=dict(counts),
            budget_label=f"{fap} {scenario_priority} FAP",
            remaining_label=remaining_label,
            validation=validation,
        )


@dataclass(frozen=True, slots=True)
class B5ACTAAdvisoryPriorityProfile:
    """Official ACTA accounting with all rule failures reported as advice."""

    profile_id: str = "b5_acta_priority_advisory"
    display_name: str = "B5 ACTA Advisory"
    cost_mode: CostMode = CostMode.PRIORITY
    rule_engine: FleetRuleEngine = field(default_factory=build_b5_acta_core_rule_engine, compare=False)

    def _budget_settings(self, fleet: Fleet) -> tuple[str, int]:
        return (
            str(fleet.metadata.get("scenario_priority", "Raid")),
            int(fleet.metadata.get("fleet_allocation_points", 1)),
        )

    def validate(self, fleet: Fleet, resolved_entries: Mapping[str, PlatformProfile | None]) -> ValidationResult:
        official = self.rule_engine.validate(fleet, resolved_entries)
        return ValidationResult(tuple(
            ValidationMessage(
                code=message.code,
                severity=(ValidationSeverity.WARNING if message.severity is ValidationSeverity.ERROR else message.severity),
                message=message.message,
                entry_id=message.entry_id,
            )
            for message in official.messages
        ))

    def summarize(self, fleet: Fleet, resolved_entries: Mapping[str, PlatformProfile | None]) -> FleetSummary:
        counts: Counter[str] = Counter()
        for entry in fleet.entries:
            profile = resolved_entries.get(entry.entry_id)
            if profile is not None and profile.priority_level in PRIORITIES:
                counts[profile.priority_level] += purchased_choice_count(entry.profile_id, entry.quantity, entry.options)
            patrol_cost = replacement_patrol_choices(entry.options)
            if patrol_cost:
                counts["Patrol"] += patrol_cost
        scenario_priority, fap = self._budget_settings(fleet)
        ancient_count = sum(
            entry.quantity for entry in fleet.entries
            if (resolved_entries.get(entry.entry_id) is not None
                and resolved_entries[entry.entry_id].priority_level == "Ancient")
        )
        if fleet.fleet_list_id == 19:
            counts["Ancient"] = ancient_count
            remaining_label = format_ancient_remaining(scenario_priority, fap, ancient_count)
        else:
            remaining_label = format_remaining_choices(scenario_priority, fap, counts)
        return FleetSummary(
            cost_mode=self.cost_mode,
            priority_counts=dict(counts),
            budget_label=f"{fap} {scenario_priority} FAP — advisory",
            remaining_label=remaining_label,
            validation=self.validate(fleet, resolved_entries),
        )


@dataclass(frozen=True, slots=True)
class B5ACTASandboxProfile:
    """Unrestricted B5 construction for scenarios, testing, and wild combinations."""

    profile_id: str = "b5_acta_sandbox"
    display_name: str = "B5 ACTA Open / Sandbox"
    cost_mode: CostMode = CostMode.PRIORITY

    def validate(self, fleet: Fleet, resolved_entries: Mapping[str, PlatformProfile | None]) -> ValidationResult:
        return ValidationResult()

    def summarize(self, fleet: Fleet, resolved_entries: Mapping[str, PlatformProfile | None]) -> FleetSummary:
        counts: Counter[str] = Counter()
        for entry in fleet.entries:
            profile = resolved_entries.get(entry.entry_id)
            if profile is not None and profile.priority_level in PRIORITIES:
                counts[profile.priority_level] += purchased_choice_count(entry.profile_id, entry.quantity, entry.options)
        return FleetSummary(
            cost_mode=self.cost_mode,
            priority_counts=dict(counts),
            budget_label="Rules disabled",
            remaining_label="Any platform combination is permitted.",
            validation=ValidationResult(),
        )
