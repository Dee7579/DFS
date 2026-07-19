"""Babylon 5 ACTA Fleet Allocation Point arithmetic.

Powers & Principalities page 12 is authoritative. Its mixed-breakdown table is
encoded explicitly rather than approximated with binary fractions. This is
important because one point buys 3, 5, 8, or 12 vessels at deeper levels and
because only one branch of a split may be split again.

Unused choices may be discarded. A fleet therefore remains legal while it uses
only part of a legal split; it does not have to consume every choice generated
by a Fleet Allocation Point.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from functools import lru_cache
from itertools import product
from typing import Mapping


PRIORITIES: tuple[str, ...] = (
    "Patrol",
    "Skirmish",
    "Raid",
    "Battle",
    "War",
    "Armageddon",
)
PRIORITY_INDEX = {name: index for index, name in enumerate(PRIORITIES)}


# Fleet Lists, "Using the Ancients": one Ancient is equivalent to the
# following number of ships/FAP choices at each standard priority.  When an
# Ancient fleet is built against a standard scenario allowance, these values
# are the exact cost of one Ancient.
ANCIENT_FAP_COST: dict[str, int] = {
    "Armageddon": 2,
    "War": 4,
    "Battle": 8,
    "Raid": 12,
    "Skirmish": 18,
    "Patrol": 30,
}


def ancient_capacity(scenario_priority: str, fleet_allocation_points: int) -> int:
    """Return how many Ancient choices fit the standard scenario budget."""
    priority = normalize_priority(scenario_priority)
    points = max(0, int(fleet_allocation_points))
    return points // ANCIENT_FAP_COST[priority]


def can_add_ancient(
    scenario_priority: str,
    fleet_allocation_points: int,
    selected_ancients: int,
) -> bool:
    return int(selected_ancients) + 1 <= ancient_capacity(
        scenario_priority, fleet_allocation_points
    )


def format_ancient_remaining(
    scenario_priority: str,
    fleet_allocation_points: int,
    selected_ancients: int,
) -> str:
    capacity = ancient_capacity(scenario_priority, fleet_allocation_points)
    remaining = max(0, capacity - int(selected_ancients))
    if remaining <= 0:
        return "no legal Ancient choices"
    suffix = "choice" if remaining == 1 else "choices"
    return f"{remaining} Ancient {suffix}"


class PriorityError(ValueError):
    pass


def normalize_priority(value: str) -> str:
    token = value.strip().casefold()
    for priority in PRIORITIES:
        if priority.casefold() == token:
            return priority
    raise PriorityError(f"Unsupported standard priority level: {value!r}")


Vector = tuple[int, ...]


def _vector(**counts: int) -> Vector:
    return tuple(int(counts.get(priority, 0)) for priority in PRIORITIES)


# Exact legal breakdowns for a single FAP from P&P page 12. The point itself
# (one ship at the same priority) is included because it is always legal.
_SINGLE_POINT_PATTERNS: dict[str, tuple[Vector, ...]] = {
    "Patrol": (_vector(Patrol=1),),
    "Skirmish": (
        _vector(Skirmish=1),
        _vector(Patrol=2),
    ),
    "Raid": (
        _vector(Raid=1),
        _vector(Skirmish=2),
        _vector(Skirmish=1, Patrol=2),
        _vector(Patrol=3),
    ),
    "Battle": (
        _vector(Battle=1),
        _vector(Raid=2),
        _vector(Raid=1, Skirmish=2),
        _vector(Raid=1, Skirmish=1, Patrol=2),
        _vector(Raid=1, Patrol=3),
        _vector(Skirmish=3),
        _vector(Skirmish=2, Patrol=2),
        _vector(Patrol=5),
    ),
    "War": (
        _vector(War=1),
        _vector(Battle=2),
        _vector(Battle=1, Raid=2),
        _vector(Battle=1, Raid=1, Skirmish=2),
        _vector(Battle=1, Raid=1, Skirmish=1, Patrol=2),
        _vector(Battle=1, Raid=1, Patrol=3),
        _vector(Battle=1, Skirmish=3),
        _vector(Battle=1, Skirmish=2, Patrol=2),
        _vector(Battle=1, Patrol=5),
        _vector(Raid=3),
        _vector(Raid=2, Skirmish=2),
        _vector(Raid=2, Skirmish=1, Patrol=2),
        _vector(Raid=2, Patrol=3),
        _vector(Skirmish=5),
        _vector(Skirmish=4, Patrol=2),
        _vector(Patrol=8),
    ),
    "Armageddon": (
        _vector(Armageddon=1),
        _vector(War=2),
        _vector(War=1, Battle=2),
        _vector(War=1, Battle=1, Raid=2),
        _vector(War=1, Battle=1, Raid=1, Skirmish=2),
        _vector(War=1, Battle=1, Raid=1, Skirmish=1, Patrol=2),
        _vector(War=1, Battle=1, Raid=1, Patrol=3),
        _vector(War=1, Battle=1, Skirmish=3),
        _vector(War=1, Battle=1, Skirmish=2, Patrol=2),
        _vector(War=1, Battle=1, Patrol=5),
        _vector(War=1, Raid=3),
        _vector(War=1, Raid=2, Skirmish=2),
        _vector(War=1, Raid=2, Skirmish=1, Patrol=2),
        _vector(War=1, Raid=2, Patrol=3),
        _vector(War=1, Skirmish=5),
        _vector(War=1, Skirmish=4, Patrol=2),
        _vector(War=1, Patrol=8),
        _vector(Battle=3),
        _vector(Battle=2, Raid=2),
        _vector(Battle=2, Raid=1, Skirmish=2),
        _vector(Battle=2, Raid=1, Skirmish=1, Patrol=2),
        _vector(Battle=2, Raid=1, Patrol=3),
        _vector(Battle=2, Skirmish=3),
        _vector(Battle=2, Skirmish=2, Patrol=2),
        _vector(Battle=2, Patrol=5),
        _vector(Raid=5),
        _vector(Raid=4, Skirmish=2),
        _vector(Raid=4, Skirmish=1, Patrol=2),
        _vector(Raid=4, Patrol=3),
        _vector(Skirmish=8),
        _vector(Skirmish=7, Patrol=2),
        _vector(Patrol=12),
    ),
}

# P&P page 12: purchasing above the scenario priority costs 2/4/8/16/32 FAP.
_HIGHER_LEVEL_COST = {1: 2, 2: 4, 3: 8, 4: 16, 5: 32}


def _all_nonzero_subpatterns(pattern: Vector) -> set[Vector]:
    """Return every non-empty subset of a legal one-point breakdown.

    Players may discard unused choices. Generating subpatterns preserves the
    P&P one-branch splitting restriction while allowing partially spent FAP.
    """
    values: set[Vector] = set()
    ranges = [range(count + 1) for count in pattern]
    for candidate in product(*ranges):
        vector = tuple(int(value) for value in candidate)
        if any(vector):
            values.add(vector)
    return values


_USABLE_POINT_PATTERNS: dict[str, tuple[Vector, ...]] = {
    priority: tuple(
        sorted(
            {subset for pattern in patterns for subset in _all_nonzero_subpatterns(pattern)},
            key=lambda vector: (sum(vector), vector),
            reverse=True,
        )
    )
    for priority, patterns in _SINGLE_POINT_PATTERNS.items()
}


@dataclass(frozen=True, slots=True)
class PriorityBudgetResult:
    valid: bool
    scenario_priority: str
    fleet_allocation_points: int
    spent_whole_points: int
    selected_counts: Mapping[str, int]
    explanation: str
    minimum_fap_required: int = 0
    remaining_fap: int = 0
    exceeded_by_fap: int = 0


def counts_to_vector(counts: Mapping[str, int]) -> Vector:
    normalized = Counter()
    for raw_priority, count in counts.items():
        if count < 0:
            raise PriorityError("Priority quantities cannot be negative")
        normalized[normalize_priority(raw_priority)] += int(count)
    return tuple(normalized[p] for p in PRIORITIES)


def vector_to_counts(vector: Vector) -> dict[str, int]:
    return {p: vector[i] for i, p in enumerate(PRIORITIES) if vector[i]}


def _subtract(a: Vector, b: Vector) -> Vector | None:
    result = tuple(x - y for x, y in zip(a, b))
    return result if all(x >= 0 for x in result) else None


@lru_cache(maxsize=None)
def _can_cover_with_points(priority: str, points: int, target: Vector) -> bool:
    if not any(target):
        return True
    if points <= 0:
        return False
    for pattern in _USABLE_POINT_PATTERNS[priority]:
        remainder = _subtract(target, pattern)
        if remainder is not None and _can_cover_with_points(priority, points - 1, remainder):
            return True
    return False


def _split_selected_counts(
    scenario_priority: str,
    selected_counts: Mapping[str, int],
) -> tuple[int, Counter[str]]:
    target_counts = Counter(vector_to_counts(counts_to_vector(selected_counts)))
    scenario_index = PRIORITY_INDEX[scenario_priority]
    higher_cost = 0

    for priority in PRIORITIES[scenario_index + 1 :]:
        quantity = target_counts.pop(priority, 0)
        distance = PRIORITY_INDEX[priority] - scenario_index
        higher_cost += quantity * _HIGHER_LEVEL_COST[distance]
    return higher_cost, target_counts


def minimum_fap_required(
    scenario_priority: str,
    selected_counts: Mapping[str, int],
) -> int:
    """Return the fewest FAP needed to legally contain the selection."""
    scenario_priority = normalize_priority(scenario_priority)
    higher_cost, target_counts = _split_selected_counts(scenario_priority, selected_counts)
    target = counts_to_vector(target_counts)
    if not any(target):
        return higher_cost

    # One FAP per remaining selected platform is a safe upper bound because a
    # same-level choice can always be purchased without splitting.
    upper_bound = sum(target_counts.values())
    for points in range(1, upper_bound + 1):
        if _can_cover_with_points(scenario_priority, points, target):
            return higher_cost + points
    return higher_cost + upper_bound


def validate_priority_budget(
    scenario_priority: str,
    fleet_allocation_points: int,
    selected_counts: Mapping[str, int],
) -> PriorityBudgetResult:
    scenario_priority = normalize_priority(scenario_priority)
    if fleet_allocation_points < 0:
        raise PriorityError("Fleet Allocation Points cannot be negative")

    minimum_required = minimum_fap_required(scenario_priority, selected_counts)
    higher_cost, _ = _split_selected_counts(scenario_priority, selected_counts)
    valid = minimum_required <= fleet_allocation_points
    remaining = max(0, fleet_allocation_points - minimum_required)
    exceeded = max(0, minimum_required - fleet_allocation_points)

    if valid:
        explanation = (
            f"{remaining} FAP remaining."
            if remaining
            else "Fleet Allocation Point allowance is fully used."
        )
    else:
        explanation = (
            f"Fleet exceeds its allowance by {exceeded} FAP "
            f"({minimum_required} required; {fleet_allocation_points} available)."
        )

    return PriorityBudgetResult(
        valid=valid,
        scenario_priority=scenario_priority,
        fleet_allocation_points=fleet_allocation_points,
        spent_whole_points=higher_cost,
        selected_counts=dict(selected_counts),
        explanation=explanation,
        minimum_fap_required=minimum_required,
        remaining_fap=remaining,
        exceeded_by_fap=exceeded,
    )


def single_point_patterns(priority: str) -> tuple[Mapping[str, int], ...]:
    """Return the authoritative complete legal breakdowns for one point."""
    normalized = normalize_priority(priority)
    return tuple(vector_to_counts(v) for v in _SINGLE_POINT_PATTERNS[normalized])


def affordable_priority_quantities(
    scenario_priority: str,
    fleet_allocation_points: int,
    selected_counts: Mapping[str, int],
) -> dict[str, int]:
    """Return the maximum additional quantity affordable at each standard level.

    Results include every standard priority that can be purchased with the
    current allowance, including priorities above the scenario level. Each
    quantity is evaluated independently from the current legal selection, so
    the UI can explain the alternative ways the remaining split branch may be
    spent without flattening the P&P tree into a misleading scalar value.
    """
    scenario_priority = normalize_priority(scenario_priority)
    base = Counter({normalize_priority(k): int(v) for k, v in selected_counts.items() if int(v)})
    affordable: dict[str, int] = {}
    for priority in PRIORITIES:
        quantity = 0
        while True:
            candidate = Counter(base)
            candidate[priority] += quantity + 1
            if not validate_priority_budget(
                scenario_priority,
                fleet_allocation_points,
                candidate,
            ).valid:
                break
            quantity += 1
            # Defensive limit for malformed future rules or extreme settings.
            if quantity >= 999:
                break
        if quantity:
            affordable[priority] = quantity
    return affordable


def can_add_priority(
    scenario_priority: str,
    fleet_allocation_points: int,
    selected_counts: Mapping[str, int],
    priority: str,
    quantity: int = 1,
) -> bool:
    """Return whether the requested choice can be added to the current fleet."""
    if quantity <= 0:
        raise PriorityError("quantity must be positive")
    scenario_priority = normalize_priority(scenario_priority)
    priority = normalize_priority(priority)
    candidate = Counter({normalize_priority(k): int(v) for k, v in selected_counts.items() if int(v)})
    candidate[priority] += quantity
    return validate_priority_budget(
        scenario_priority,
        fleet_allocation_points,
        candidate,
    ).valid



def format_unaffordable_choice(
    scenario_priority: str,
    fleet_allocation_points: int,
    selected_counts: Mapping[str, int],
    desired_priority: str,
    *,
    allowance_label: str = "fleet budget",
) -> str:
    """Explain an unaffordable choice using scenario-level FAP wording.

    The full legality decision still comes from ``validate_priority_budget``.
    This helper only translates that result into player-facing guidance.
    """
    scenario_priority = normalize_priority(scenario_priority)
    desired_priority = normalize_priority(desired_priority)
    total = max(0, int(fleet_allocation_points))
    base = Counter({
        normalize_priority(key): int(value)
        for key, value in selected_counts.items()
        if int(value)
    })
    current_required = minimum_fap_required(scenario_priority, base)
    candidate = Counter(base)
    candidate[desired_priority] += 1
    candidate_required = minimum_fap_required(scenario_priority, candidate)
    incremental = max(1, candidate_required - current_required)
    remaining = max(0, total - current_required)
    point_word = "Fleet Allocation Point" if incremental == 1 else "Fleet Allocation Points"
    remaining_word = "Fleet Allocation Point" if remaining == 1 else "Fleet Allocation Points"
    return (
        f"Purchasing this {desired_priority} choice would exceed the remaining {allowance_label}. "
        f"It requires {incremental} {scenario_priority} {point_word}. "
        f"Remaining {allowance_label}: {remaining} {scenario_priority} {remaining_word}"
    )

def format_remaining_choices(
    scenario_priority: str,
    fleet_allocation_points: int,
    selected_counts: Mapping[str, int],
) -> str:
    """Human-readable alternatives for spending the current remaining branch."""
    budget = validate_priority_budget(
        scenario_priority,
        fleet_allocation_points,
        selected_counts,
    )
    if not budget.valid:
        return f"INVALID — exceeded by {budget.exceeded_by_fap} FAP"
    choices = affordable_priority_quantities(
        scenario_priority,
        fleet_allocation_points,
        selected_counts,
    )
    if not choices:
        return "Remaining: no legal choices"
    parts = [
        f"{quantity} {priority} choice{'s' if quantity != 1 else ''}"
        for priority, quantity in reversed(tuple(choices.items()))
    ]
    return "Remaining: " + " or ".join(parts)
