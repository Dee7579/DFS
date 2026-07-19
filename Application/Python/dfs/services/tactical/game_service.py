"""Build independent Tactical Assistant game state from a saved DFS fleet."""
from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Protocol
from uuid import uuid4

from dfs.domain.catalog import PlatformFilter, PlatformProfile
from dfs.domain.fleet import Fleet, FleetEntry
from dfs.domain.fleet.huge_hangars import embarked_profile_ids
from dfs.domain.fleet.included_craft import IncludedCraft, parse_included_craft
from dfs.domain.fleet.replacements import replacement_map
from dfs.domain.tactical import (
    TacticalGameState,
    TacticalUnitState,
    TrackState,
    TraitState,
    UnitKind,
    WeaponState,
)


class TacticalBuildError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class TacticalWeaponTemplate:
    name: str
    arc: str = ""
    range_value: str = ""
    attack_dice: str = ""
    traits: str = ""


@dataclass(frozen=True, slots=True)
class TacticalProfileTemplate:
    profile_id: int
    platform_name: str
    faction_name: str
    fleet_name: str
    priority_level: str
    damage_maximum: int | None
    crippled_threshold: int | None
    crew_maximum: int | None
    skeleton_threshold: int | None
    shield_maximum: int | None
    shield_recovery: str
    crew_quality: str
    notes: tuple[str, ...]
    traits: tuple[str, ...]
    weapons: tuple[TacticalWeaponTemplate, ...]
    included_craft: tuple[IncludedCraft, ...]
    kind: UnitKind
    initiative: str = ""
    speed: str = ""
    turn: str = ""
    hull: str = ""
    troops: str = ""


class TacticalProfileResolver(Protocol):
    def resolve(self, profile_id: int) -> TacticalProfileTemplate: ...


_TRACK_PATTERN = re.compile(r"^\s*(?P<maximum>\d+)(?:\s*/\s*(?P<threshold>\d+))?\s*$")
_SHIELD_PATTERN = re.compile(
    r"^\s*Shields\s+(?P<maximum>\d+)(?:\s*/\s*(?P<recovery>.+))?\s*$",
    re.IGNORECASE,
)


def _parse_track(value: str | None) -> tuple[int | None, int | None]:
    text = (value or "").strip()
    match = _TRACK_PATTERN.match(text)
    if match is None:
        return None, None
    maximum = int(match.group("maximum"))
    threshold = match.group("threshold")
    return maximum, int(threshold) if threshold is not None else None


def _parse_shields(traits: tuple[str, ...]) -> tuple[int | None, str]:
    for trait in traits:
        match = _SHIELD_PATTERN.match(trait)
        if match:
            return int(match.group("maximum")), (match.group("recovery") or "").strip()
    return None, ""


def _safe_key(prefix: str, index: int, name: str, suffix: str = "") -> str:
    normalized = re.sub(r"[^a-z0-9]+", "-", name.casefold()).strip("-") or "item"
    extra = re.sub(r"[^a-z0-9]+", "-", suffix.casefold()).strip("-")
    return f"{prefix}-{index}-{normalized}{('-' + extra) if extra else ''}"


class CatalogTacticalProfileResolver:
    """Resolve tactical snapshots through existing read-only catalog services.

    The resolver caches the profile-to-platform relationship after first use.
    No database or platform-data write operation is exposed here.
    """

    def __init__(self, catalog_service, platform_detail_service) -> None:
        self._catalog = catalog_service
        self._details = platform_detail_service
        self._cache: dict[int, TacticalProfileTemplate] = {}

    def resolve(self, profile_id: int) -> TacticalProfileTemplate:
        cached = self._cache.get(profile_id)
        if cached is not None:
            return cached

        profile = self._details.get_profile(profile_id)
        if profile is None:
            raise TacticalBuildError(f"No DFS platform profile exists with profile_id={profile_id}")

        detail = self._find_platform(profile)
        if detail is None:
            raise TacticalBuildError(
                f"Unable to resolve the canonical platform for profile_id={profile_id}"
            )

        damage_maximum, crippled_threshold = _parse_track(profile.damage)
        crew_maximum, skeleton_threshold = _parse_track(profile.crew)
        shield_maximum, shield_recovery = _parse_shields(profile.traits)
        kind = (
            UnitKind.CRAFT
            if damage_maximum is None and crew_maximum is None
            else UnitKind.PLATFORM
        )
        template = TacticalProfileTemplate(
            profile_id=profile.profile_id,
            platform_name=detail.name,
            faction_name=detail.faction_name,
            fleet_name=profile.fleet_name,
            priority_level=profile.priority_level,
            damage_maximum=damage_maximum,
            crippled_threshold=crippled_threshold,
            crew_maximum=crew_maximum,
            skeleton_threshold=skeleton_threshold,
            shield_maximum=shield_maximum,
            shield_recovery=shield_recovery,
            crew_quality=str(profile.crew_quality or ""),
            notes=profile.notes,
            traits=profile.traits,
            weapons=tuple(
                TacticalWeaponTemplate(
                    weapon.name,
                    weapon.arc,
                    weapon.range_value,
                    weapon.attack_dice,
                    weapon.traits,
                )
                for weapon in profile.weapons
            ),
            included_craft=parse_included_craft(profile.craft),
            kind=kind,
            initiative=str(profile.initiative or ""),
            speed=str(profile.speed or ""),
            turn=str(profile.turn or ""),
            hull=str(profile.hull or ""),
            troops=str(profile.troops or ""),
        )
        self._cache[profile_id] = template
        return template

    def _find_platform(self, profile: PlatformProfile):
        summaries = self._catalog.search(
            PlatformFilter(fleet_list_ids=(profile.fleet_list_id,), limit=1000)
        )
        for summary in summaries:
            detail = self._details.get(summary.ship_id)
            if any(candidate.profile_id == profile.profile_id for candidate in detail.profiles):
                return detail
        return None


class TacticalGameBuilder:
    """Expand one saved Fleet into independent per-unit battle state."""

    def __init__(self, resolver: TacticalProfileResolver) -> None:
        self._resolver = resolver

    def build(self, fleet: Fleet, *, game_name: str | None = None) -> TacticalGameState:
        units: list[TacticalUnitState] = []
        for entry in fleet.entries:
            template = self._resolver.resolve(entry.profile_id)
            primary_units = tuple(
                self._create_profile_unit(
                    entry,
                    template,
                    instance_number,
                    metadata={"fleet_entry_options": dict(entry.options)},
                )
                for instance_number in range(1, entry.quantity + 1)
            )
            units.extend(primary_units)

            if template.kind is UnitKind.PLATFORM:
                units.extend(self._create_included_craft(entry, primary_units, template))
                units.extend(self._create_embarked_platforms(entry, primary_units))

        return TacticalGameState.create(
            name=game_name or f"{fleet.name} Battle",
            game_system_id=fleet.game_system_id,
            source_fleet_id=fleet.fleet_id,
            source_fleet_name=fleet.name,
            units=tuple(units),
            metadata={
                "construction_profile_id": fleet.construction_profile_id,
                "faction_id": fleet.faction_id,
                "fleet_list_id": fleet.fleet_list_id,
                "selected_year": fleet.selected_year,
                "source_fleet_schema_version": fleet.schema_version,
            },
        )

    def _create_profile_unit(
        self,
        entry: FleetEntry,
        template: TacticalProfileTemplate,
        instance_number: int,
        *,
        parent_unit_id: str | None = None,
        vessel_name: str | None = None,
        metadata: dict[str, object] | None = None,
    ) -> TacticalUnitState:
        resolved_vessel_name = (
            entry.vessel_name if vessel_name is None and instance_number == 1 else vessel_name or ""
        )
        traits = tuple(
            TraitState(_safe_key("trait", index, name), name)
            for index, name in enumerate(template.traits, start=1)
        )
        weapons = tuple(
            WeaponState(
                weapon_key=_safe_key("weapon", index, weapon.name, weapon.arc),
                name=weapon.name,
                arc=weapon.arc,
                range_value=weapon.range_value,
                attack_dice=weapon.attack_dice,
                traits=weapon.traits,
            )
            for index, weapon in enumerate(template.weapons, start=1)
        )
        return TacticalUnitState(
            unit_id=str(uuid4()),
            source_entry_id=entry.entry_id,
            profile_id=template.profile_id,
            parent_unit_id=parent_unit_id,
            kind=template.kind,
            platform_name=template.platform_name,
            vessel_name=resolved_vessel_name,
            instance_number=instance_number,
            faction_name=template.faction_name,
            fleet_name=template.fleet_name,
            priority_level=template.priority_level,
            initiative=template.initiative,
            speed=template.speed,
            turn=template.turn,
            hull=template.hull,
            troops=template.troops,
            source_notes=template.notes,
            metadata=dict(metadata or {}),
            damage=TrackState.create(
                template.damage_maximum,
                threshold=template.crippled_threshold,
            ),
            crew=TrackState.create(
                template.crew_maximum,
                threshold=template.skeleton_threshold,
            ),
            shields=TrackState.create(
                template.shield_maximum,
                recovery=template.shield_recovery,
            ),
            crew_quality=template.crew_quality,
            traits=traits,
            weapons=weapons,
            notes=entry.notes,
        )

    def _create_included_craft(
        self,
        entry: FleetEntry,
        parents: tuple[TacticalUnitState, ...],
        template: TacticalProfileTemplate,
    ) -> list[TacticalUnitState]:
        craft_units: list[TacticalUnitState] = []
        selected_replacements = replacement_map(entry.options)
        known_sources = {group.printed_name for group in template.included_craft}
        unknown_sources = set(selected_replacements) - known_sources
        if unknown_sources:
            unknown = ", ".join(sorted(unknown_sources))
            raise TacticalBuildError(
                f"Fleet entry {entry.entry_id} contains craft replacements for unknown source: {unknown}"
            )

        for group in template.included_craft:
            # Round-robin slots keep partial replacements distributed predictably
            # across grouped carriers instead of assigning every replacement to
            # the first carrier.
            parent_slots = [
                parent
                for craft_index in range(group.quantity)
                for parent in parents
            ]
            replacements = selected_replacements.get(group.printed_name, {})
            replacement_total = sum(replacements.values())
            if replacement_total > len(parent_slots):
                raise TacticalBuildError(
                    f"Fleet entry {entry.entry_id} replaces {replacement_total} "
                    f"{group.printed_name}, but only {len(parent_slots)} are included."
                )

            slot_index = 0
            replacement_instance = 0
            for profile_id_text, quantity in replacements.items():
                try:
                    replacement_profile_id = int(profile_id_text)
                except (TypeError, ValueError) as exc:
                    raise TacticalBuildError(
                        f"Invalid replacement profile ID: {profile_id_text}"
                    ) from exc
                replacement_template = self._resolver.resolve(replacement_profile_id)
                if replacement_template.kind is not UnitKind.CRAFT:
                    raise TacticalBuildError(
                        f"Replacement profile {replacement_profile_id} is not a craft profile."
                    )
                for _ in range(quantity):
                    parent = parent_slots[slot_index]
                    slot_index += 1
                    replacement_instance += 1
                    craft_units.append(
                        self._create_profile_unit(
                            entry,
                            replacement_template,
                            replacement_instance,
                            parent_unit_id=parent.unit_id,
                            vessel_name="",
                            metadata={
                                "included_craft_source": group.printed_name,
                                "replacement_profile_id": replacement_profile_id,
                            },
                        )
                    )

            original_instance = 0
            for parent in parent_slots[slot_index:]:
                original_instance += 1
                craft_units.append(
                    TacticalUnitState(
                        unit_id=str(uuid4()),
                        source_entry_id=entry.entry_id,
                        profile_id=None,
                        parent_unit_id=parent.unit_id,
                        kind=UnitKind.CRAFT,
                        platform_name=group.printed_name,
                        instance_number=original_instance,
                        faction_name=template.faction_name,
                        fleet_name=template.fleet_name,
                        priority_level="Included",
                        metadata={"included_craft_source": group.printed_name},
                    )
                )
        return craft_units

    def _create_embarked_platforms(
        self,
        entry: FleetEntry,
        parents: tuple[TacticalUnitState, ...],
    ) -> list[TacticalUnitState]:
        profile_ids = embarked_profile_ids(entry.options)
        if not profile_ids:
            return []
        if not parents:
            raise TacticalBuildError("Embarked platforms require a parent platform.")

        result: list[TacticalUnitState] = []
        instance_counts: dict[int, int] = {}
        for index, profile_id in enumerate(profile_ids):
            template = self._resolver.resolve(profile_id)
            instance_counts[profile_id] = instance_counts.get(profile_id, 0) + 1
            parent = parents[index % len(parents)]
            embarked = self._create_profile_unit(
                entry,
                template,
                instance_counts[profile_id],
                parent_unit_id=parent.unit_id,
                vessel_name="",
                metadata={"embarked_via_huge_hangars": True},
            )
            result.append(embarked)
            if template.kind is UnitKind.PLATFORM and template.included_craft:
                # Embarked ships have no independent FleetEntry options, so only
                # their printed included craft are expanded here.
                result.extend(self._create_plain_included_craft(entry, embarked, template))
        return result

    @staticmethod
    def _create_plain_included_craft(
        entry: FleetEntry,
        parent: TacticalUnitState,
        template: TacticalProfileTemplate,
    ) -> list[TacticalUnitState]:
        result: list[TacticalUnitState] = []
        for group in template.included_craft:
            for instance_number in range(1, group.quantity + 1):
                result.append(
                    TacticalUnitState(
                        unit_id=str(uuid4()),
                        source_entry_id=entry.entry_id,
                        profile_id=None,
                        parent_unit_id=parent.unit_id,
                        kind=UnitKind.CRAFT,
                        platform_name=group.printed_name,
                        instance_number=instance_number,
                        faction_name=template.faction_name,
                        fleet_name=template.fleet_name,
                        priority_level="Included",
                        metadata={"included_craft_source": group.printed_name},
                    )
                )
        return result
