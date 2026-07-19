"""Reusable fleet-construction rule primitives.

These rules contain no Babylon 5 faction data.  Sprint 002D.2 can catalogue
published fleet-list restrictions as declarative instances of these classes,
while the Fleet Builder and Tactical Assistant remain free of rules logic.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from math import floor
from typing import Iterable

from dfs.domain.catalog import PlatformProfile
from dfs.domain.fleet.models import ValidationSeverity
from dfs.domain.fleet.rules import RuleCategory, RuleContext, RuleMessage, RuleSource


def _profile_name(profile: PlatformProfile) -> str:
    """Return the best available human-readable platform label.

    Current database profile models do not formally expose the parent platform
    name, but repository implementations may attach it.  Rule messages remain
    useful when that label is unavailable.
    """
    return str(getattr(profile, "platform_name", "") or f"Profile {profile.profile_id}")


@dataclass(frozen=True, slots=True)
class PlatformSelector:
    """Declaratively identifies profiles affected by a construction rule.

    Empty fields are ignored.  Populated fields use AND semantics between
    fields and membership semantics within a field.  This makes selectors safe
    to store in future JSON rule catalogues without embedding Python callbacks.
    """

    profile_ids: frozenset[int] = field(default_factory=frozenset)
    fleet_list_ids: frozenset[int] = field(default_factory=frozenset)
    priority_levels: frozenset[str] = field(default_factory=frozenset)
    traits: frozenset[str] = field(default_factory=frozenset)
    source_books: frozenset[str] = field(default_factory=frozenset)

    @classmethod
    def profiles(cls, *profile_ids: int) -> "PlatformSelector":
        return cls(profile_ids=frozenset(profile_ids))

    def matches(self, profile: PlatformProfile | None) -> bool:
        if profile is None:
            return False
        if self.profile_ids and profile.profile_id not in self.profile_ids:
            return False
        if self.fleet_list_ids and profile.fleet_list_id not in self.fleet_list_ids:
            return False
        if self.priority_levels and profile.priority_level not in self.priority_levels:
            return False
        if self.source_books and profile.source_book not in self.source_books:
            return False
        if self.traits:
            available = {trait.casefold() for trait in profile.traits}
            if not {trait.casefold() for trait in self.traits}.issubset(available):
                return False
        return True


def matching_entries(context: RuleContext, selector: PlatformSelector):
    return tuple(
        (entry, profile)
        for entry in context.fleet.entries
        if (profile := context.profile_for(entry)) is not None and selector.matches(profile)
    )


def selected_quantity(context: RuleContext, selector: PlatformSelector) -> int:
    return sum(entry.quantity for entry, _profile in matching_entries(context, selector))


@dataclass(frozen=True, slots=True)
class ConstructionRuleBase:
    rule_id: str
    name: str
    source: RuleSource
    description: str
    category: RuleCategory = RuleCategory.FLEET
    severity: ValidationSeverity = ValidationSeverity.ERROR

    def applies(self, context: RuleContext) -> bool:
        return True

    def _message(
        self,
        message: str,
        *,
        remedy: str = "",
        remedies: tuple[str, ...] = (),
        entry_id: str | None = None,
        platform_name: str = "",
    ) -> RuleMessage:
        return RuleMessage(
            self.rule_id,
            self.severity,
            self.name,
            message,
            self.source,
            entry_id=entry_id,
            platform_name=platform_name,
            remedy=remedy,
            remedies=remedies,
        )


@dataclass(frozen=True, slots=True)
class UniquePlatformRule(ConstructionRuleBase):
    selector: PlatformSelector = field(default_factory=PlatformSelector)

    def evaluate(self, context: RuleContext):
        entries = matching_entries(context, self.selector)
        total = sum(entry.quantity for entry, _ in entries)
        if total <= 1:
            return ()
        first_entry, first_profile = entries[0]
        return (self._message(
            f"{_profile_name(first_profile)} is unique, but {total} copies are selected.",
            remedy="Reduce the fleet to one copy of this platform.",
            entry_id=first_entry.entry_id,
            platform_name=_profile_name(first_profile),
        ),)


@dataclass(frozen=True, slots=True)
class MaximumQuantityRule(ConstructionRuleBase):
    selector: PlatformSelector = field(default_factory=PlatformSelector)
    maximum: int = 1

    def __post_init__(self):
        if self.maximum < 0:
            raise ValueError("maximum must be zero or greater")

    def evaluate(self, context: RuleContext):
        total = selected_quantity(context, self.selector)
        if total <= self.maximum:
            return ()
        return (self._message(
            f"{total} matching choices are selected; the maximum is {self.maximum}.",
            remedy=f"Remove {total - self.maximum} matching choice(s).",
        ),)


@dataclass(frozen=True, slots=True)
class HighestPriorityMaximumQuantityRule(ConstructionRuleBase):
    """Limits only the highest-priority matching group currently represented.

    Matching choices at lower priority levels are unrestricted. This models
    rules such as the revised Gaim Queens restriction without embedding any
    faction-specific logic in the Fleet Builder.
    """

    selector: PlatformSelector = field(default_factory=PlatformSelector)
    maximum: int = 1
    priority_order: tuple[str, ...] = (
        "Patrol", "Skirmish", "Raid", "Battle", "War", "Armageddon", "Ancient"
    )

    def __post_init__(self):
        if self.maximum < 0:
            raise ValueError("maximum must be zero or greater")
        if not self.priority_order:
            raise ValueError("priority_order cannot be empty")

    def applies(self, context: RuleContext) -> bool:
        return selected_quantity(context, self.selector) > 0

    def evaluate(self, context: RuleContext):
        rows = matching_entries(context, self.selector)
        if not rows:
            return ()
        rank = {priority: index for index, priority in enumerate(self.priority_order)}
        represented = [profile.priority_level for _entry, profile in rows]
        highest = max(represented, key=lambda value: rank.get(value, -1))
        highest_rows = [(entry, profile) for entry, profile in rows if profile.priority_level == highest]
        total = sum(entry.quantity for entry, _profile in highest_rows)
        if total <= self.maximum:
            return ()
        first_entry, first_profile = highest_rows[0]
        higher = [value for value in self.priority_order if rank.get(value, -1) > rank.get(highest, -1)]
        remedies = [f"Remove {total - self.maximum} existing {highest} Queen choice(s)."]
        if higher:
            remedies.append(
                f"Add a higher-priority Queen ({', '.join(higher)}) so {highest} becomes a lower-priority Queen level."
            )
        return (self._message(
            f"Only {self.maximum} {highest} Queen may be present while {highest} is the highest Queen priority represented in the fleet; {total} are selected.",
            remedies=tuple(remedies),
            entry_id=first_entry.entry_id,
            platform_name=_profile_name(first_profile),
        ),)


@dataclass(frozen=True, slots=True)
class RequiredPlatformRule(ConstructionRuleBase):
    trigger: PlatformSelector = field(default_factory=PlatformSelector)
    required: PlatformSelector = field(default_factory=PlatformSelector)
    required_quantity: int = 1

    def __post_init__(self):
        if self.required_quantity < 1:
            raise ValueError("required_quantity must be at least one")

    def applies(self, context: RuleContext) -> bool:
        return selected_quantity(context, self.trigger) > 0

    def evaluate(self, context: RuleContext):
        found = selected_quantity(context, self.required)
        if found >= self.required_quantity:
            return ()
        trigger_entry, trigger_profile = matching_entries(context, self.trigger)[0]
        missing = self.required_quantity - found
        return (self._message(
            f"{_profile_name(trigger_profile)} requires {self.required_quantity} qualifying supporting platform(s); {found} are selected.",
            remedies=(
                f"Add {missing} qualifying supporting platform(s).",
                "Remove the dependent choice.",
            ),
            entry_id=trigger_entry.entry_id,
            platform_name=_profile_name(trigger_profile),
        ),)


@dataclass(frozen=True, slots=True)
class MutualExclusionRule(ConstructionRuleBase):
    first: PlatformSelector = field(default_factory=PlatformSelector)
    second: PlatformSelector = field(default_factory=PlatformSelector)

    def applies(self, context: RuleContext) -> bool:
        return selected_quantity(context, self.first) > 0 and selected_quantity(context, self.second) > 0

    def evaluate(self, context: RuleContext):
        if not self.applies(context):
            return ()
        return (self._message(
            "The two restricted platform groups may not be selected in the same fleet.",
            remedy="Remove every platform from either one of the conflicting groups.",
        ),)


@dataclass(frozen=True, slots=True)
class PurchaseRatioRule(ConstructionRuleBase):
    limited: PlatformSelector = field(default_factory=PlatformSelector)
    basis: PlatformSelector = field(default_factory=PlatformSelector)
    allowed_per_basis: int = 1
    basis_block_size: int = 1
    minimum_allowance: int = 0

    def __post_init__(self):
        if self.allowed_per_basis < 1 or self.basis_block_size < 1 or self.minimum_allowance < 0:
            raise ValueError("ratio values must be positive and minimum_allowance cannot be negative")

    def applies(self, context: RuleContext) -> bool:
        return selected_quantity(context, self.limited) > 0

    def evaluate(self, context: RuleContext):
        limited = selected_quantity(context, self.limited)
        basis = selected_quantity(context, self.basis)
        allowance = max(self.minimum_allowance, floor(basis / self.basis_block_size) * self.allowed_per_basis)
        if limited <= allowance:
            return ()
        return (self._message(
            f"{limited} restricted choice(s) are selected, but {basis} qualifying choice(s) permit only {allowance}.",
            remedy=(
                f"Remove {limited - allowance} restricted choice(s), or add enough qualifying choices "
                f"to satisfy the {self.allowed_per_basis}:{self.basis_block_size} purchase ratio."
            ),
        ),)


@dataclass(frozen=True, slots=True)
class MinimumFleetRequirementRule(ConstructionRuleBase):
    selector: PlatformSelector = field(default_factory=PlatformSelector)
    minimum: int = 1

    def __post_init__(self):
        if self.minimum < 1:
            raise ValueError("minimum must be at least one")

    def evaluate(self, context: RuleContext):
        total = selected_quantity(context, self.selector)
        if total >= self.minimum:
            return ()
        return (self._message(
            f"The fleet requires at least {self.minimum} qualifying choice(s); {total} are selected.",
            remedy=f"Add {self.minimum - total} qualifying choice(s).",
        ),)


@dataclass(frozen=True, slots=True)
class FAPLimitedPlatformRule(ConstructionRuleBase):
    selector: PlatformSelector = field(default_factory=PlatformSelector)
    allowed_per_fap: int = 1
    minimum_allowance: int = 0

    def __post_init__(self):
        if self.allowed_per_fap < 0 or self.minimum_allowance < 0:
            raise ValueError("allowances cannot be negative")

    def evaluate(self, context: RuleContext):
        fap = max(0, int(context.fleet.metadata.get("fleet_allocation_points", 1)))
        allowance = max(self.minimum_allowance, fap * self.allowed_per_fap)
        total = selected_quantity(context, self.selector)
        if total <= allowance:
            return ()
        return (self._message(
            f"{total} restricted choice(s) are selected; {fap} FAP permits {allowance}.",
            remedy=f"Remove {total - allowance} restricted choice(s) or increase the scenario FAP.",
        ),)


@dataclass(frozen=True, slots=True)
class GroupedPurchaseRule(ConstructionRuleBase):
    selector: PlatformSelector = field(default_factory=PlatformSelector)
    group_size: int = 1
    minimum_groups: int = 0
    maximum_groups: int | None = None

    def __post_init__(self):
        if self.group_size < 1 or self.minimum_groups < 0:
            raise ValueError("group_size must be positive and minimum_groups cannot be negative")
        if self.maximum_groups is not None and self.maximum_groups < self.minimum_groups:
            raise ValueError("maximum_groups cannot be smaller than minimum_groups")

    def applies(self, context: RuleContext) -> bool:
        return selected_quantity(context, self.selector) > 0 or self.minimum_groups > 0

    def evaluate(self, context: RuleContext):
        total = selected_quantity(context, self.selector)
        minimum = self.minimum_groups * self.group_size
        maximum = None if self.maximum_groups is None else self.maximum_groups * self.group_size
        problems: list[str] = []
        remedies: list[str] = []
        if total < minimum:
            problems.append(f"at least {minimum} are required")
            remedies.append(f"add {minimum - total}")
        if total % self.group_size:
            next_group = ((total // self.group_size) + 1) * self.group_size
            problems.append(f"choices must be purchased in groups of {self.group_size}")
            remedies.append(f"change the quantity to {next_group} or {next_group - self.group_size}")
        if maximum is not None and total > maximum:
            problems.append(f"no more than {maximum} are permitted")
            remedies.append(f"remove {total - maximum}")
        if not problems:
            return ()
        return (self._message(
            f"{total} matching choice(s) are selected; " + "; ".join(problems) + ".",
            remedy="; or ".join(remedies).capitalize() + ".",
        ),)


def register_rules(engine, rules: Iterable[ConstructionRuleBase]):
    """Register a declarative rule library and return the engine for chaining."""
    for rule in rules:
        engine.register(rule)
    return engine

@dataclass(frozen=True, slots=True)
class EachPlatformUniqueRule(ConstructionRuleBase):
    """Limits every individual profile matched by *selector* to one copy.

    Unlike :class:`UniquePlatformRule`, which treats a selector as one unique
    choice group, this rule is intended for fleet lists where every platform is
    independently unique (for example, The Ancients).
    """

    selector: PlatformSelector = field(default_factory=PlatformSelector)

    def evaluate(self, context: RuleContext):
        grouped: dict[int, list[tuple[object, PlatformProfile]]] = {}
        for entry, profile in matching_entries(context, self.selector):
            grouped.setdefault(profile.profile_id, []).append((entry, profile))

        messages = []
        for rows in grouped.values():
            total = sum(entry.quantity for entry, _profile in rows)
            if total <= 1:
                continue
            first_entry, first_profile = rows[0]
            messages.append(self._message(
                f"{_profile_name(first_profile)} is unique, but {total} copies are selected.",
                remedy="Reduce this platform to one copy.",
                entry_id=first_entry.entry_id,
                platform_name=_profile_name(first_profile),
            ))
        return tuple(messages)
