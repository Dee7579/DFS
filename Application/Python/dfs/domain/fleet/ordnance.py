"""Configurable ordnance loadouts stored on fleet entries."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

MISSILE_LOADOUT_OPTION_KEY = "missile_loadouts"


@dataclass(frozen=True, slots=True)
class MissileVariant:
    variant_id: str
    display_name: str
    range_value: str
    traits: str
    minimum_year: int
    special_rule: str = ""


@dataclass(frozen=True, slots=True)
class MissileRackOpportunity:
    rack_key: str
    label: str
    weapon_index: int
    arc: str
    attack_dice: str
    standard_range: str
    standard_traits: str
    variants: tuple[MissileVariant, ...]
    source_book: str
    source_page: int


def missile_loadout_map(options: Mapping[str, object]) -> dict[str, str]:
    raw = options.get(MISSILE_LOADOUT_OPTION_KEY, {})
    if not isinstance(raw, Mapping):
        return {}
    result: dict[str, str] = {}
    for rack_key, variant_id in raw.items():
        value = str(variant_id).strip()
        if value:
            result[str(rack_key)] = value
    return result


def with_missile_loadouts(options: Mapping[str, object], values: Mapping[str, str]) -> dict[str, object]:
    updated = dict(options)
    clean = {str(key): str(value) for key, value in values.items() if str(value).strip() and str(value) != "standard"}
    if clean:
        updated[MISSILE_LOADOUT_OPTION_KEY] = clean
    else:
        updated.pop(MISSILE_LOADOUT_OPTION_KEY, None)
    return updated
