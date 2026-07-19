"""Read-only domain models used by the DFS application catalog."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class PlatformFilter:
    """User-selected catalog filters.

    Trait and weapon filters use AND semantics: every selected value must be
    present on at least one profile belonging to the returned platform.
    """

    search_text: str = ""
    faction_ids: tuple[int, ...] = ()
    fleet_list_ids: tuple[int, ...] = ()
    priority_levels: tuple[str, ...] = ()
    in_service_values: tuple[str, ...] = ()
    traits: tuple[str, ...] = ()
    weapons: tuple[str, ...] = ()
    available_year: int | None = None
    limit: int = 200
    offset: int = 0


@dataclass(frozen=True, slots=True)
class FilterOption:
    id: int | str
    label: str
    count: int = 0


@dataclass(frozen=True, slots=True)
class PlatformSummary:
    ship_id: int
    name: str
    ship_class: str
    faction_id: int
    faction_name: str
    profile_count: int
    fleet_names: tuple[str, ...] = ()
    priority_levels: tuple[str, ...] = ()
    in_service_values: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class WeaponDetail:
    name: str
    range_value: str
    arc: str
    attack_dice: str
    traits: str
    sort_order: int


@dataclass(frozen=True, slots=True)
class PlatformProfile:
    profile_id: int
    fleet_list_id: int
    fleet_name: str
    initiative: str
    priority_level: str
    speed: str
    turn: str
    hull: str
    damage: str
    crew: str
    troops: str
    craft: str
    in_service: str
    source_book: str
    crew_quality: str = ""
    notes: tuple[str, ...] = ()
    traits: tuple[str, ...] = ()
    weapons: tuple[WeaponDetail, ...] = ()


@dataclass(frozen=True, slots=True)
class PlatformDetail:
    ship_id: int
    name: str
    ship_class: str
    file_name: str
    faction_id: int
    faction_name: str
    profiles: tuple[PlatformProfile, ...] = field(default_factory=tuple)
