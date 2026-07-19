"""Fighter and small-craft replacement domain models.

Replacement selections are stored in ``FleetEntry.options`` so saved fleets remain
portable and the same information can drive Fleet Builder, printing, and the future
Tactical Assistant.
"""
from __future__ import annotations

from dataclasses import dataclass
from math import ceil
from typing import Mapping


REPLACEMENT_OPTION_KEY = "craft_replacements"
REPLACEMENT_COST_OPTION_KEY = "craft_replacement_patrol_costs"


@dataclass(frozen=True, slots=True)
class ReplacementTarget:
    search_name: str
    display_name: str
    minimum_year: int | None = None
    patrol_group_size: int | None = None
    carries_parent_troop: bool = False

    def patrol_choices(self, quantity: int) -> int:
        if not self.patrol_group_size or quantity <= 0:
            return 0
        return ceil(quantity / self.patrol_group_size)


@dataclass(frozen=True, slots=True)
class FighterReplacementDefinition:
    rule_id: str
    fleet_names: tuple[str, ...]
    source_search_names: tuple[str, ...]
    targets: tuple[ReplacementTarget, ...]
    source_book: str
    source_page: int
    all_or_none: bool = False
    source_contains: str = ""


@dataclass(frozen=True, slots=True)
class ResolvedReplacementTarget:
    profile_id: int
    platform_name: str
    profile_name: str
    target: ReplacementTarget


@dataclass(frozen=True, slots=True)
class ReplacementOpportunity:
    rule_id: str
    source_printed_name: str
    source_quantity: int
    targets: tuple[ResolvedReplacementTarget, ...]
    source_book: str
    source_page: int
    all_or_none: bool = False


def replacement_map(options: Mapping[str, object]) -> dict[str, dict[str, int]]:
    raw = options.get(REPLACEMENT_OPTION_KEY, {})
    if not isinstance(raw, Mapping):
        return {}
    result: dict[str, dict[str, int]] = {}
    for source_name, values in raw.items():
        if not isinstance(values, Mapping):
            continue
        clean: dict[str, int] = {}
        for profile_id, quantity in values.items():
            try:
                qty = int(quantity)
            except (TypeError, ValueError):
                continue
            if qty > 0:
                clean[str(profile_id)] = qty
        if clean:
            result[str(source_name)] = clean
    return result


def with_replacement_map(options: Mapping[str, object], values: Mapping[str, Mapping[str, int]]) -> dict[str, object]:
    updated = dict(options)
    cleaned = {
        str(source): {str(profile_id): int(quantity) for profile_id, quantity in targets.items() if int(quantity) > 0}
        for source, targets in values.items()
        if any(int(quantity) > 0 for quantity in targets.values())
    }
    if cleaned:
        updated[REPLACEMENT_OPTION_KEY] = cleaned
    else:
        updated.pop(REPLACEMENT_OPTION_KEY, None)
    return updated


def replacement_patrol_choices(options: Mapping[str, object]) -> int:
    raw = options.get(REPLACEMENT_COST_OPTION_KEY, {})
    if not isinstance(raw, Mapping):
        return 0
    total = 0
    for value in raw.values():
        try:
            total += max(0, int(value))
        except (TypeError, ValueError):
            pass
    return total


def with_replacement_cost(options: Mapping[str, object], source_name: str, patrol_choices: int) -> dict[str, object]:
    updated = dict(options)
    raw = updated.get(REPLACEMENT_COST_OPTION_KEY, {})
    costs = dict(raw) if isinstance(raw, Mapping) else {}
    if patrol_choices > 0:
        costs[source_name] = int(patrol_choices)
    else:
        costs.pop(source_name, None)
    if costs:
        updated[REPLACEMENT_COST_OPTION_KEY] = costs
    else:
        updated.pop(REPLACEMENT_COST_OPTION_KEY, None)
    return updated
