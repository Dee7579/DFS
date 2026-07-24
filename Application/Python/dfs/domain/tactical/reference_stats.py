"""Derived reference statistics for Tactical Assistant unit headers.

The canonical fighter profiles retain Dogfight in source notes and Dodge in the
trait list.  This module converts those existing immutable values into concise
header fields without changing platform data or live combat state.
"""
from __future__ import annotations

import re

from dfs.domain.tactical.models import TacticalUnitState, UnitKind


_DOGFIGHT_PATTERN = re.compile(r"^\s*dogfight\s*:?\s*(.*?)\s*$", re.IGNORECASE)
_DODGE_PATTERN = re.compile(r"^\s*dodge(?:\s*:?\s*(.*?))?\s*$", re.IGNORECASE)


def fighter_reference_stats(unit: TacticalUnitState) -> tuple[tuple[str, str], ...]:
    """Return Dogfight and Dodge header values for fighter-like craft.

    Older game files and some historical platform modules use either
    ``Dogfight: +2`` or ``Dogfight +2``.  Both forms are accepted.  Dodge is
    read from the canonical trait name so the displayed score matches the
    fighter profile already loaded into the game state.
    """

    if unit.kind is not UnitKind.CRAFT:
        return ()

    dogfight = ""
    for note in unit.source_notes:
        match = _DOGFIGHT_PATTERN.match(str(note or ""))
        if match:
            dogfight = match.group(1).strip()
            break

    dodge = ""
    for trait in unit.traits:
        match = _DODGE_PATTERN.match(str(trait.name or ""))
        if match:
            dodge = (match.group(1) or "").strip()
            break

    values: list[tuple[str, str]] = []
    if dogfight:
        values.append(("Dogfight", dogfight))
    if dodge:
        values.append(("Dodge", dodge))
    return tuple(values)
