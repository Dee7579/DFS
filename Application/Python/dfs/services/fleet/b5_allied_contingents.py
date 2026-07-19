"""Official B5 ACTA allied-contingent construction definitions."""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import Mapping

from dfs.domain.catalog import PlatformProfile
from dfs.domain.fleet.models import Fleet, ValidationSeverity
from dfs.domain.fleet.priority import PRIORITIES, validate_priority_budget
from dfs.domain.fleet.rules import RuleCategory, RuleContext, RuleMessage, RuleSource

FLEET_LISTS = RuleSource("A Call to Arms: Fleet Lists", "Fleet Special Rules")


@dataclass(frozen=True, slots=True)
class AlliedContingentDefinition:
    primary_fleet_list_id: int
    display_name: str
    allowed_fleet_list_ids: tuple[int, ...]
    max_allied_source_lists: int = 1
    max_scenario_fap: int = 1


ALLIED_CONTINGENTS: dict[int, AlliedContingentDefinition] = {
    10: AlliedContingentDefinition(
        10,
        "Interstellar Alliance Allied Fleets",
        (3, 4, 5, 8, 11, 12, 13, 14, 15, 16),
    ),
    17: AlliedContingentDefinition(
        17,
        "Raiders Allied Fleets",
        (11, 12, 13, 14, 15, 16),
    ),
    21: AlliedContingentDefinition(
        21,
        "Psi Corps EarthForce Requisition",
        (1, 3, 4),
        max_scenario_fap=2,
    ),
}


def definition_for(fleet: Fleet) -> AlliedContingentDefinition | None:
    if fleet.fleet_list_id is None:
        return None
    return ALLIED_CONTINGENTS.get(fleet.fleet_list_id)


def is_allied_profile(fleet: Fleet, profile: PlatformProfile) -> bool:
    definition = definition_for(fleet)
    return bool(definition and profile.fleet_list_id in definition.allowed_fleet_list_ids)


def permitted_profile(fleet: Fleet, profile: PlatformProfile) -> bool:
    return profile.fleet_list_id == fleet.fleet_list_id or is_allied_profile(fleet, profile)


def allied_profiles_by_entry(context: RuleContext) -> dict[str, PlatformProfile]:
    return {
        entry.entry_id: profile
        for entry in context.fleet.entries
        if (profile := context.profile_for(entry)) is not None
        and profile.fleet_list_id != context.fleet.fleet_list_id
    }


@dataclass(frozen=True, slots=True)
class AlliedContingentRule:
    rule_id: str = "CORE_ALLIED_CONTINGENT"
    name: str = "Allied contingent"
    category: RuleCategory = RuleCategory.ALLIANCE
    source: RuleSource = FLEET_LISTS
    description: str = (
        "Fleets with an official allied or requisition rule may spend the published "
        "scenario-level allowance on ships from one permitted source fleet list."
    )

    def applies(self, context: RuleContext) -> bool:
        return bool(allied_profiles_by_entry(context))

    def evaluate(self, context: RuleContext):
        definition = definition_for(context.fleet)
        allied = allied_profiles_by_entry(context)
        if not allied:
            return ()
        if definition is None:
            return tuple(
                RuleMessage(
                    self.rule_id,
                    ValidationSeverity.ERROR,
                    self.name,
                    f"{profile.fleet_name} is not permitted as an allied contingent.",
                    self.source,
                    entry_id=entry_id,
                    remedy="Remove the allied platform or choose a fleet with an allied-fleet rule.",
                )
                for entry_id, profile in allied.items()
            )

        messages: list[RuleMessage] = []
        invalid = {
            entry_id: profile
            for entry_id, profile in allied.items()
            if profile.fleet_list_id not in definition.allowed_fleet_list_ids
        }
        for entry_id, profile in invalid.items():
            messages.append(RuleMessage(
                self.rule_id,
                ValidationSeverity.ERROR,
                self.name,
                f"{profile.fleet_name} is not a permitted ally for {definition.display_name}.",
                self.source,
                entry_id=entry_id,
                remedy="Remove the platform or select a permitted allied fleet list.",
            ))

        valid_profiles = [p for eid, p in allied.items() if eid not in invalid]
        source_lists = {p.fleet_list_id for p in valid_profiles}
        if len(source_lists) > definition.max_allied_source_lists:
            messages.append(RuleMessage(
                self.rule_id,
                ValidationSeverity.ERROR,
                self.name,
                "Allied ships were selected from more than one allied fleet list.",
                self.source,
                remedy="Choose all allied ships from a single allied fleet list.",
            ))

        counts: Counter[str] = Counter()
        for entry in context.fleet.entries:
            profile = context.profile_for(entry)
            if profile is not None and profile.fleet_list_id in source_lists and profile.priority_level in PRIORITIES:
                counts[profile.priority_level] += entry.quantity
        scenario = str(context.fleet.metadata.get("scenario_priority", "Raid"))
        budget = validate_priority_budget(scenario, definition.max_scenario_fap, counts)
        if not budget.valid:
            messages.append(RuleMessage(
                self.rule_id,
                ValidationSeverity.ERROR,
                self.name,
                f"The allied contingent exceeds {definition.max_scenario_fap} {scenario} Fleet Allocation "
                f"Point{'s' if definition.max_scenario_fap != 1 else ''}. {budget.explanation}",
                self.source,
                remedy=(
                    f"Reduce the allied contingent to {definition.max_scenario_fap} "
                    f"Fleet Allocation Point{'s' if definition.max_scenario_fap != 1 else ''}."
                ),
            ))
        return tuple(messages)
