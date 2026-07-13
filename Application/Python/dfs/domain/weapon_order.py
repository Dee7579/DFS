"""Canonical weapon ordering shared by DFS presentation and services.

ACTA weapons are displayed by firing arc in the established DFS order while
preserving the source/import order inside each arc.
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import TypeVar

from dfs.domain.catalog import WeaponDetail


ARC_ORDER: tuple[str, ...] = ("B", "F", "P", "S", "A", "B(a)", "T")
_ARC_RANK = {arc.casefold(): index for index, arc in enumerate(ARC_ORDER)}


def normalize_arc(value: str) -> str:
    """Normalize harmless formatting differences without changing display data."""

    compact = "".join(str(value or "").split())
    if compact.casefold() in {"b(a)", "ba", "b(aft)"}:
        return "B(a)"
    return compact.upper()


def weapon_sort_key(weapon: WeaponDetail, original_index: int = 0) -> tuple[int, int, int]:
    """Return the canonical DFS ordering key for one weapon.

    ``sort_order`` is retained as the first within-arc ordering signal. The
    original list index provides a deterministic fallback for older records.
    Unknown arcs are placed after known ACTA arcs rather than discarded.
    """

    arc = normalize_arc(weapon.arc)
    rank = _ARC_RANK.get(arc.casefold(), len(ARC_ORDER))
    return rank, int(weapon.sort_order or 0), original_index


def order_weapons(weapons: Iterable[WeaponDetail]) -> tuple[WeaponDetail, ...]:
    indexed = tuple(enumerate(weapons))
    return tuple(
        weapon
        for _, weapon in sorted(
            indexed,
            key=lambda pair: weapon_sort_key(pair[1], pair[0]),
        )
    )
