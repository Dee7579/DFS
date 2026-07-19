"""Core Babylon 5 ACTA fleet rules used by the construction profile.

Fleet-specific alliances, fighter swaps, and platform restrictions are added in
subsequent rule-library sprints.  This module proves the single validation
pipeline by moving the existing core checks into rule objects.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass

from dfs.domain.fleet.models import ValidationSeverity
from dfs.domain.fleet.replacements import replacement_map, replacement_patrol_choices
from dfs.domain.fleet.grouped_purchases import purchased_choice_count
from dfs.domain.fleet.included_craft import parse_included_craft
from dfs.domain.fleet.priority import PRIORITIES, ancient_capacity, validate_priority_budget
from dfs.domain.fleet.rules import RuleCategory, RuleContext, RuleMessage, RuleSource
from dfs.domain.in_service import parse_in_service
from dfs.services.fleet.rule_engine import FleetRuleEngine
from dfs.services.fleet.b5_allied_contingents import AlliedContingentRule, permitted_profile
from dfs.services.fleet.b5_composite_fleets import source_fleet_id, source_fleet_name
from dfs.services.fleet.construction_rules import (
    EachPlatformUniqueRule, GroupedPurchaseRule, HighestPriorityMaximumQuantityRule, PlatformSelector,
)

FLEET_LISTS = RuleSource("A Call to Arms: Fleet Lists", "Fleet Lists")
UNIQUE_TRAIT_SOURCE = RuleSource(
    "A Call to Arms: Second Edition Fleet Lists",
    "Unique platform trait",
    None,
    "Second Edition",
)

ANCIENTS_SOURCE = RuleSource(
    "A Call to Arms: Second Edition Fleet Lists",
    "Using the Ancients",
    139,
    "Second Edition",
)

GAIM_QUEENS_SOURCE = RuleSource(
    "Powers & Principalities",
    "Revised Gaim Intelligence Fleet Special Rules - The Queens",
    19,
    "Second Edition update",
)

P_AND_P_PRIORITY = RuleSource(
    "Powers & Principalities",
    "New Rules — Fleet Allocation Point Breakdowns",
    12,
    "Second Edition update",
)


ISA_IN_SERVICE_SOURCE = RuleSource(
    "A Call to Arms: Second Edition Fleet Lists",
    "ISA Fleet Special Rules - In Service Dates",
    82,
    "Second Edition",
)




COMPOSITE_SOURCE = RuleSource(
    "Powers & Principalities", "New Rules — The Army of Light", 10, "Second Edition update"
)
DEPARTURE_SOURCE = RuleSource(
    "A Call to Arms: Second Edition Fleet Lists", "Fleet histories and In Service Dates", None, "Second Edition"
)


@dataclass(frozen=True, slots=True)
class FirstOnesDepartureRule:
    rule_id: str = "B5-FIRST-ONES-DATE-001"
    name: str = "First Ones departure"
    category: RuleCategory = RuleCategory.FLEET
    source: RuleSource = DEPARTURE_SOURCE
    description: str = "Ancients, Vorlons, and Shadows may not be selected in 2262 or later."

    def applies(self, context: RuleContext) -> bool:
        return context.fleet.fleet_list_id in {6, 18, 19} and context.fleet.selected_year is not None

    def evaluate(self, context: RuleContext):
        year = context.fleet.selected_year
        if year is None or year <= 2261:
            return ()
        return (RuleMessage(
            self.rule_id, ValidationSeverity.ERROR, self.name,
            f"This fleet is unavailable in {year}; the First Ones departed the galaxy after 2261.",
            self.source,
            remedies=("Set the scenario year to 2261 or earlier.", "Choose a younger-race fleet for 2262 or later."),
        ),)


@dataclass(frozen=True, slots=True)
class ArmyOfLightMinimumComponentsRule:
    rule_id: str = "B5-AOL-MIX-003"
    name: str = "Minimum two component fleets"
    category: RuleCategory = RuleCategory.FLEET
    source: RuleSource = COMPOSITE_SOURCE
    description: str = "An Army of Light must include ships from at least two different fleet lists."

    def applies(self, context: RuleContext) -> bool:
        return context.fleet.fleet_list_id == 28 and bool(context.fleet.entries)

    def evaluate(self, context: RuleContext):
        represented = {
            source_fleet_id(profile.source_book)
            for entry in context.fleet.entries
            if (profile := context.profile_for(entry)) is not None
        }
        represented.discard(None)
        if len(represented) >= 2:
            return ()
        return (RuleMessage(
            self.rule_id, ValidationSeverity.ERROR, self.name,
            "An Army of Light must include ships from at least two different published fleet lists.",
            self.source,
            remedy="Add a platform from a second component fleet.",
        ),)


@dataclass(frozen=True, slots=True)
class CombinedLeagueFighterPrerequisiteRule:
    rule_id: str = "B5-LEAGUE-FTR-003"
    name: str = "Component ship required for purchased fighters"
    category: RuleCategory = RuleCategory.FLEET
    source: RuleSource = RuleSource(
        "A Call to Arms: Second Edition Fleet Lists",
        "Combined Fleets of the Non-Aligned Worlds", 5, "Second Edition"
    )
    description: str = "Purchased fighters require a non-fighter ship from the same component fleet list."

    def applies(self, context: RuleContext) -> bool:
        return context.fleet.fleet_list_id == 27 and bool(context.fleet.entries)

    def evaluate(self, context: RuleContext):
        ship_sources = set()
        fighter_entries = []
        for entry in context.fleet.entries:
            profile = context.profile_for(entry)
            if profile is None:
                continue
            source = source_fleet_id(profile.source_book)
            if "Fighter" in profile.traits:
                fighter_entries.append((entry, profile, source))
            else:
                ship_sources.add(source)
        messages = []
        for entry, profile, source in fighter_entries:
            if source not in ship_sources:
                component_name = source_fleet_name(profile.source_book, "its component fleet")
                messages.append(RuleMessage(
                    self.rule_id, ValidationSeverity.ERROR, self.name,
                    f"This fighter was purchased without a non-fighter ship from {component_name}.",
                    self.source, entry_id=entry.entry_id, platform_name=component_name,
                    remedy=f"Add a non-fighter ship from {component_name}, or remove this fighter wing.",
                ))
        return tuple(messages)


@dataclass(frozen=True, slots=True)
class ISAFormationDateRule:
    rule_id: str = "B5-ISA-DATE-002"
    name: str = "ISA formation date"
    category: RuleCategory = RuleCategory.FLEET
    source: RuleSource = ISA_IN_SERVICE_SOURCE
    description: str = "The Interstellar Alliance fleet list may not be used before 2262."

    def applies(self, context: RuleContext) -> bool:
        return context.fleet.fleet_list_id == 10 and context.fleet.selected_year is not None

    def evaluate(self, context: RuleContext):
        year = context.fleet.selected_year
        if year is None or year >= 2262:
            return ()
        return (RuleMessage(
            self.rule_id, ValidationSeverity.ERROR, self.name,
            f"The Interstellar Alliance fleet list is unavailable in {year}; it may be used only from 2262 onward.",
            self.source,
            remedies=(
                "Set the scenario year to 2262 or later.",
                "Choose a fleet list appropriate to the earlier scenario year.",
            ),
        ),)


@dataclass(frozen=True, slots=True)
class GaimQueenRequirementRule:
    rule_id: str = "B5-GAIM-QUEEN-001"
    name: str = "A Queen must lead the fleet"
    category: RuleCategory = RuleCategory.FLEET
    source: RuleSource = GAIM_QUEENS_SOURCE
    description: str = "Every revised Gaim fleet must contain at least one Queen ship."

    def applies(self, context: RuleContext) -> bool:
        return context.fleet.fleet_list_id == 14 and bool(context.fleet.entries)

    def evaluate(self, context: RuleContext):
        queen_ids = {6441, 6458, 6459, 6464}
        queens = sum(
            entry.quantity for entry in context.fleet.entries
            if (profile := context.profile_for(entry)) is not None
            and profile.profile_id in queen_ids
        )
        if queens:
            return ()
        return (RuleMessage(
            self.rule_id, ValidationSeverity.ERROR, self.name,
            "Every Gaim fleet must be led by at least one Queen ship, but no Queen is selected.",
            self.source,
            remedies=(
                "Add a Shaakak, Shuuka, Shrutaa, or Sluuka Queen ship.",
                "Remove the non-Queen choices and rebuild the fleet with a Queen leader.",
            ),
        ),)


@dataclass(frozen=True, slots=True)
class FleetListRequiredRule:
    rule_id: str = "CORE_FLEET_LIST_REQUIRED"
    name: str = "Fleet list required"
    category: RuleCategory = RuleCategory.CORE
    source: RuleSource = FLEET_LISTS
    description: str = "A fleet must identify the fleet list or era used for construction."

    def applies(self, context: RuleContext) -> bool:
        return context.fleet.fleet_list_id is None

    def evaluate(self, context: RuleContext):
        return (RuleMessage(
            self.rule_id, ValidationSeverity.ERROR, self.name,
            "Select a fleet list or era before adding platforms.", self.source,
            remedy="Choose Fleet / Era in Fleet Setup.",
        ),)


@dataclass(frozen=True, slots=True)
class ProfileResolutionRule:
    rule_id: str = "CORE_PROFILE_RESOLUTION"
    name: str = "Platform profile resolution"
    category: RuleCategory = RuleCategory.CORE
    source: RuleSource = FLEET_LISTS
    description: str = "Every roster entry must resolve to a current database profile."

    def applies(self, context: RuleContext) -> bool:
        return True

    def evaluate(self, context: RuleContext):
        result = []
        for entry in context.fleet.entries:
            if context.profile_for(entry) is None:
                result.append(RuleMessage(
                    self.rule_id, ValidationSeverity.ERROR, self.name,
                    f"Profile {entry.profile_id} could not be resolved.", self.source,
                    entry_id=entry.entry_id,
                    remedy="Remove the stale entry and add the platform again.",
                ))
        return tuple(result)


@dataclass(frozen=True, slots=True)
class FleetListEligibilityRule:
    rule_id: str = "CORE_FLEET_LIST_ELIGIBILITY"
    name: str = "Fleet-list eligibility"
    category: RuleCategory = RuleCategory.CORE
    source: RuleSource = FLEET_LISTS
    description: str = "Purchased profiles must belong to the selected fleet list unless an alliance rule permits them."

    def applies(self, context: RuleContext) -> bool:
        return context.fleet.fleet_list_id is not None

    def evaluate(self, context: RuleContext):
        result = []
        for entry in context.fleet.entries:
            profile = context.profile_for(entry)
            if profile is not None and not permitted_profile(context.fleet, profile):
                result.append(RuleMessage(
                    self.rule_id, ValidationSeverity.ERROR, self.name,
                    f"{profile.fleet_name} is not the selected fleet list.", self.source,
                    entry_id=entry.entry_id, platform_name=str(getattr(profile, "platform_name", "") or f"Profile {profile.profile_id}"),
                    remedy="Remove the platform or use a permitted allied-contingent rule.",
                ))
        return tuple(result)


@dataclass(frozen=True, slots=True)
class YearAvailabilityRule:
    rule_id: str = "CORE_YEAR_AVAILABILITY"
    name: str = "In-service availability"
    category: RuleCategory = RuleCategory.CORE
    source: RuleSource = FLEET_LISTS
    description: str = "A platform must be in service during the selected scenario year."

    def applies(self, context: RuleContext) -> bool:
        return context.fleet.selected_year is not None

    def evaluate(self, context: RuleContext):
        result = []
        year = context.fleet.selected_year
        assert year is not None
        for entry in context.fleet.entries:
            profile = context.profile_for(entry)
            if profile is None:
                continue
            period = parse_in_service(profile.in_service)
            if not period.includes(year):
                result.append(RuleMessage(
                    self.rule_id, ValidationSeverity.ERROR, self.name,
                    f"{profile.platform_name} is not available in {year} ({profile.in_service}).",
                    self.source, entry_id=entry.entry_id, platform_name=str(getattr(profile, "platform_name", "") or f"Profile {profile.profile_id}"),
                    remedy="Change the year or remove the platform.",
                ))
        return tuple(result)


@dataclass(frozen=True, slots=True)
class SupportedPriorityRule:
    rule_id: str = "CORE_SUPPORTED_PRIORITY"
    name: str = "Supported priority level"
    category: RuleCategory = RuleCategory.CORE
    source: RuleSource = P_AND_P_PRIORITY
    description: str = "Standard construction accepts the six P&P priority levels; special levels require dedicated rules."

    def applies(self, context: RuleContext) -> bool:
        return True

    def evaluate(self, context: RuleContext):
        result = []
        for entry in context.fleet.entries:
            profile = context.profile_for(entry)
            if profile is None:
                continue
            priority = profile.priority_level.strip()
            if priority in PRIORITIES:
                continue
            if priority == "Ancient" and context.fleet.fleet_list_id == 19:
                continue
            if priority == "Ancient":
                severity = ValidationSeverity.WARNING
                message = "Ancient priority requires its fleet-specific equivalency rule."
            elif priority == "Special":
                severity = ValidationSeverity.WARNING
                message = "Special priority requires a fleet-specific or scenario rule."
            else:
                severity = ValidationSeverity.ERROR
                message = f"Unsupported priority level: {priority or '(blank)'}."
            result.append(RuleMessage(
                self.rule_id, severity, self.name, message, self.source,
                entry_id=entry.entry_id, platform_name=str(getattr(profile, "platform_name", "") or f"Profile {profile.profile_id}"),
            ))
        return tuple(result)


@dataclass(frozen=True, slots=True)
class PriorityBudgetRule:
    rule_id: str = "CORE_PRIORITY_BUDGET"
    name: str = "Fleet Allocation Point budget"
    category: RuleCategory = RuleCategory.CORE
    source: RuleSource = P_AND_P_PRIORITY
    description: str = "The fleet must fit one legal P&P priority-breakdown pattern."

    def applies(self, context: RuleContext) -> bool:
        return True

    def evaluate(self, context: RuleContext):
        scenario_priority = str(context.fleet.metadata.get("scenario_priority", "Raid"))
        fap = int(context.fleet.metadata.get("fleet_allocation_points", 1))

        if context.fleet.fleet_list_id == 19:
            ancient_count = 0
            for entry in context.fleet.entries:
                profile = context.profile_for(entry)
                if profile is not None and profile.priority_level == "Ancient":
                    ancient_count += entry.quantity
            capacity = ancient_capacity(scenario_priority, fap)
            if ancient_count <= capacity:
                return ()
            cost = {"Armageddon": 2, "War": 4, "Battle": 8, "Raid": 12, "Skirmish": 18, "Patrol": 30}[scenario_priority]
            return (RuleMessage(
                self.rule_id, ValidationSeverity.ERROR, self.name,
                f"{ancient_count} Ancient choices are selected, but {fap} {scenario_priority} FAP can purchase only {capacity} (one Ancient costs {cost} {scenario_priority} FAP).",
                ANCIENTS_SOURCE,
                remedy="Remove an Ancient or increase the scenario FAP allowance.",
            ),)

        counts: Counter[str] = Counter()
        for entry in context.fleet.entries:
            profile = context.profile_for(entry)
            if profile is not None and profile.priority_level in PRIORITIES:
                counts[profile.priority_level] += purchased_choice_count(entry.profile_id, entry.quantity, entry.options)
            patrol_cost = replacement_patrol_choices(entry.options)
            if patrol_cost:
                counts["Patrol"] += patrol_cost
        budget = validate_priority_budget(scenario_priority, fap, counts)
        if budget.valid:
            return ()
        return (RuleMessage(
            self.rule_id, ValidationSeverity.ERROR, self.name,
            budget.explanation, self.source,
            remedy="Remove choices or increase the scenario FAP allowance.",
        ),)




@dataclass(frozen=True, slots=True)
class FighterReplacementAllocationRule:
    rule_id: str = "CORE_FIGHTER_REPLACEMENT_ALLOCATION"
    name: str = "Fighter replacement allocation"
    category: RuleCategory = RuleCategory.REPLACEMENT
    source: RuleSource = FLEET_LISTS
    description: str = "Replacement craft may not exceed the flights included by their parent platform."

    def applies(self, context: RuleContext) -> bool:
        return any(replacement_map(entry.options) for entry in context.fleet.entries)

    def evaluate(self, context: RuleContext):
        result = []
        for entry in context.fleet.entries:
            profile = context.profile_for(entry)
            if profile is None:
                continue
            included = {craft.printed_name: craft.quantity * entry.quantity for craft in parse_included_craft(profile.craft)}
            for source_name, replacements in replacement_map(entry.options).items():
                allowed = included.get(source_name, 0)
                selected = sum(int(value) for value in replacements.values())
                if source_name not in included:
                    result.append(RuleMessage(
                        self.rule_id, ValidationSeverity.ERROR, self.name,
                        f"{profile.platform_name} does not include {source_name}.", self.source,
                        entry_id=entry.entry_id, platform_name=str(getattr(profile, "platform_name", "") or f"Profile {profile.profile_id}"),
                        remedy="Clear the stale replacement selection.",
                    ))
                elif selected > allowed:
                    result.append(RuleMessage(
                        self.rule_id, ValidationSeverity.ERROR, self.name,
                        f"{selected} replacements were selected for only {allowed} included {source_name} flights.", self.source,
                        entry_id=entry.entry_id, platform_name=str(getattr(profile, "platform_name", "") or f"Profile {profile.profile_id}"),
                        remedy=f"Reduce replacements to {allowed} or fewer.",
                    ))
        return tuple(result)

def build_b5_acta_core_rule_engine() -> FleetRuleEngine:
    return FleetRuleEngine((
        FleetListRequiredRule(),
        ProfileResolutionRule(),
        FleetListEligibilityRule(),
        YearAvailabilityRule(),
        SupportedPriorityRule(),
        PriorityBudgetRule(),
        FighterReplacementAllocationRule(),
        AlliedContingentRule(),
        ISAFormationDateRule(),
        FirstOnesDepartureRule(),
        ArmyOfLightMinimumComponentsRule(),
        CombinedLeagueFighterPrerequisiteRule(),
        GroupedPurchaseRule(
            rule_id="B5-GROUPED-PURCHASE-001",
            name="Two ships per Patrol choice",
            source=FLEET_LISTS,
            description="Platforms printed as Patrol (Two Ships) must be purchased in pairs.",
            category=RuleCategory.PLATFORM,
            selector=PlatformSelector.profiles(6318, 6456, 6457, 6481, 6482, 6483),
            group_size=2,
        ),
        GaimQueenRequirementRule(),
        EachPlatformUniqueRule(
            rule_id="B5-UNIQUE-TRAIT-001",
            name="Unique platform",
            source=UNIQUE_TRAIT_SOURCE,
            description="A platform with the Unique trait may appear only once in a fleet.",
            category=RuleCategory.PLATFORM,
            selector=PlatformSelector(traits=frozenset({"Unique"})),
        ),
        EachPlatformUniqueRule(
            rule_id="B5-ANCIENT-UNQ-001",
            name="Each Ancient is unique",
            source=ANCIENTS_SOURCE,
            description="Only one example of each Ancient platform may be selected.",
            category=RuleCategory.PLATFORM,
            selector=PlatformSelector(fleet_list_ids=frozenset({19})),
        ),
        HighestPriorityMaximumQuantityRule(
            rule_id="B5-GAIM-QUEEN-002",
            name="Highest Priority Queen Rule",
            source=GAIM_QUEENS_SOURCE,
            description=(
                "Only one Queen may be present at the highest Queen priority level "
                "represented in a Gaim fleet; lower-priority Queens are unrestricted."
            ),
            category=RuleCategory.PLATFORM,
            selector=PlatformSelector.profiles(6441, 6458, 6459, 6464),
            maximum=1,
        ),
    ))
