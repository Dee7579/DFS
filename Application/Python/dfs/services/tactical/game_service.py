"""Build independent Tactical Assistant game state from a saved DFS fleet."""
from __future__ import annotations

from dataclasses import dataclass, replace
import re
from typing import Protocol
from uuid import uuid4

from dfs.domain.catalog import PlatformFilter, PlatformProfile
from dfs.domain.fleet import Fleet, FleetEntry
from dfs.domain.fleet.huge_hangars import embarked_profile_ids
from dfs.domain.fleet.included_craft import (
    IncludedCraft,
    normalize_craft_name,
    parse_included_craft,
)
from dfs.domain.fleet.replacements import replacement_map
from dfs.domain.tactical import (
    TacticalGameState,
    TacticalUnitState,
    TrackState,
    TraitState,
    UnitDisposition,
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
_WING_OF_FLIGHTS_PATTERN = re.compile(
    r"\bWing\s+of\s+(?P<count>\d+|one|two|three|four|five|six|seven|eight|nine|ten)\s+Flights?\b",
    re.IGNORECASE,
)
_NUMBER_WORDS = {
    "one": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
    "six": 6,
    "seven": 7,
    "eight": 8,
    "nine": 9,
    "ten": 10,
}


def _purchased_craft_flights(notes: tuple[str, ...]) -> int:
    """Return the number of individual flights represented by one purchase.

    ACTA fighter entries are bought as wings. The canonical profile notes state
    the wing size (for example ``Wing of Four Flights``). Tactical Assistant
    tracks each flight independently, so one Fleet Builder purchase must expand
    to the printed number of flights rather than one representative row.
    """

    for note in notes:
        match = _WING_OF_FLIGHTS_PATTERN.search(str(note or ""))
        if match is None:
            continue
        token = match.group("count").casefold()
        value = int(token) if token.isdigit() else _NUMBER_WORDS.get(token, 1)
        return max(1, value)
    return 1


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
        self._craft_cache: dict[tuple[str, str, str], TacticalProfileTemplate | None] = {}

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

    def resolve_included_craft(
        self,
        printed_name: str,
        *,
        faction_name: str = "",
        fleet_name: str = "",
    ) -> TacticalProfileTemplate | None:
        """Resolve printed carried-craft text to its canonical craft profile.

        Fleet Builder already performs conservative normalized-name matching for
        included craft. Tactical Assistant mirrors that approach so ordinary
        carried fighters receive the same weapons and traits as purchased or
        replacement fighters.
        """

        key = (
            normalize_craft_name(printed_name),
            faction_name.casefold(),
            fleet_name.casefold(),
        )
        if key in self._craft_cache:
            return self._craft_cache[key]
        target = key[0]
        if not target:
            self._craft_cache[key] = None
            return None

        best: TacticalProfileTemplate | None = None
        best_score = -1
        for summary in self._catalog.search(PlatformFilter(limit=1000)):
            normalized = normalize_craft_name(summary.name)
            if normalized == target:
                score = 100
            elif target in normalized or normalized in target:
                score = 60
            else:
                score = len(set(target.split()) & set(normalized.split())) * 10
            if key[1] and summary.faction_name.casefold() == key[1]:
                score += 15
            if key[2] and any(name.casefold() == key[2] for name in summary.fleet_names):
                score += 10
            if score <= best_score:
                continue

            detail = self._details.get(summary.ship_id)
            if detail is None:
                continue
            ordered_profiles = sorted(
                detail.profiles,
                key=lambda item: bool(key[2]) and item.fleet_name.casefold() != key[2],
            )
            for profile in ordered_profiles:
                candidate = self.resolve(profile.profile_id)
                if candidate.kind is not UnitKind.CRAFT:
                    continue
                best = candidate
                best_score = score
                break

        if best_score < 20:
            best = None
        self._craft_cache[key] = best
        return best

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
            if template.kind is UnitKind.CRAFT:
                wing_size = _purchased_craft_flights(template.notes)
                primary_units = tuple(
                    self._create_profile_unit(
                        entry,
                        template,
                        ((wing_number - 1) * wing_size) + flight_number,
                        metadata={
                            "fleet_entry_options": dict(entry.options),
                            "purchased_craft_expanded": True,
                            "purchased_wing_size": wing_size,
                            "purchased_wing_number": wing_number,
                            "purchased_flight_number": flight_number,
                            "source_fleet_entry_quantity": entry.quantity,
                        },
                    )
                    for wing_number in range(1, entry.quantity + 1)
                    for flight_number in range(1, wing_size + 1)
                )
            else:
                primary_units = tuple(
                    self._create_profile_unit(
                        entry,
                        template,
                        instance_number,
                        metadata={
                            "fleet_entry_options": dict(entry.options),
                            "source_fleet_entry_quantity": entry.quantity,
                        },
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

    def hydrate_purchased_craft_wings(self, game: TacticalGameState) -> TacticalGameState:
        """Expand legacy purchased fighter-wing snapshots into individual flights.

        Sprint 001-005 created one tactical craft row for each Fleet Builder
        fighter-wing purchase. Canonical fighter notes define how many flights
        that purchase actually contains. Existing saved games are upgraded once
        on load; the first legacy row keeps its current state and additional
        flights begin Ready and Operational. The metadata flag makes the upgrade
        idempotent.
        """

        changed = False
        units: list[TacticalUnitState] = []
        purchase_numbers: dict[tuple[str, int | None, str], int] = {}
        for unit in game.units:
            metadata = dict(unit.metadata)
            if (
                unit.kind is not UnitKind.CRAFT
                or unit.parent_unit_id is not None
                or metadata.get("purchased_craft_expanded")
            ):
                units.append(unit)
                continue

            wing_size = _purchased_craft_flights(unit.source_notes)
            if wing_size <= 1:
                units.append(unit)
                continue

            key = (unit.source_entry_id, unit.profile_id, unit.platform_name)
            purchase_number = purchase_numbers.get(key, 0) + 1
            purchase_numbers[key] = purchase_number
            base = (purchase_number - 1) * wing_size

            for flight_number in range(1, wing_size + 1):
                expanded_metadata = {
                    **metadata,
                    "purchased_craft_expanded": True,
                    "purchased_wing_size": wing_size,
                    "purchased_wing_number": purchase_number,
                    "purchased_flight_number": flight_number,
                }
                if flight_number == 1:
                    expanded = replace(
                        unit,
                        instance_number=base + flight_number,
                        metadata=expanded_metadata,
                    )
                else:
                    expanded = replace(
                        unit,
                        unit_id=str(uuid4()),
                        vessel_name="",
                        instance_number=base + flight_number,
                        metadata=expanded_metadata,
                        traits=tuple(
                            replace(trait, disabled=False, destroyed=False)
                            for trait in unit.traits
                        ),
                        weapons=tuple(
                            replace(weapon, disabled=False, destroyed=False)
                            for weapon in unit.weapons
                        ),
                        critical_hits=(),
                        special_action="",
                        craft_status="ready",
                        disposition=UnitDisposition.OPERATIONAL,
                        notes="",
                        destroyed=False,
                        crippled=False,
                        skeleton_crew=False,
                        crippled_correction=False,
                        skeleton_crew_correction=False,
                    )
                units.append(expanded)
            changed = True

        return replace(game, units=tuple(units)) if changed else game

    def hydrate_missing_craft(self, game: TacticalGameState) -> TacticalGameState:
        """Populate legacy carried-craft snapshots that predate profile resolution.

        Sprint 001-003 game files stored printed carried craft with ``profile_id``
        set to ``None`` and no weapon/trait snapshot. Reopening those files now
        safely enriches only the independent game state from read-only catalog
        data; the saved fleet and certified sources remain untouched.
        """

        changed = False
        units: list[TacticalUnitState] = []
        for unit in game.units:
            source_name = str(unit.metadata.get("included_craft_source", "")).strip()
            if (
                unit.kind is not UnitKind.CRAFT
                or not source_name
                or unit.traits
                or unit.weapons
            ):
                units.append(unit)
                continue
            resolver = getattr(self._resolver, "resolve_included_craft", None)
            if not callable(resolver):
                units.append(unit)
                continue
            template = resolver(
                source_name,
                faction_name=unit.faction_name,
                fleet_name=unit.fleet_name,
            )
            if template is None:
                units.append(unit)
                continue
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
            units.append(
                replace(
                    unit,
                    profile_id=template.profile_id,
                    platform_name=template.platform_name,
                    priority_level=template.priority_level,
                    initiative=template.initiative,
                    speed=template.speed,
                    turn=template.turn,
                    hull=template.hull,
                    troops=template.troops,
                    source_notes=template.notes,
                    crew_quality=template.crew_quality,
                    traits=traits,
                    weapons=weapons,
                    metadata={**dict(unit.metadata), "legacy_snapshot_hydrated": True},
                )
            )
            changed = True
        return replace(game, units=tuple(units)) if changed else game

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
            source_template = self._resolve_printed_craft(group.printed_name, template)
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
                if source_template is not None:
                    craft_units.append(
                        self._create_profile_unit(
                            entry,
                            source_template,
                            original_instance,
                            parent_unit_id=parent.unit_id,
                            vessel_name="",
                            metadata={"included_craft_source": group.printed_name},
                        )
                    )
                else:
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

    def _resolve_printed_craft(
        self,
        printed_name: str,
        parent_template: TacticalProfileTemplate,
    ) -> TacticalProfileTemplate | None:
        resolver = getattr(self._resolver, "resolve_included_craft", None)
        if not callable(resolver):
            return None
        return resolver(
            printed_name,
            faction_name=parent_template.faction_name,
            fleet_name=parent_template.fleet_name,
        )

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

    def _create_plain_included_craft(
        self,
        entry: FleetEntry,
        parent: TacticalUnitState,
        template: TacticalProfileTemplate,
    ) -> list[TacticalUnitState]:
        result: list[TacticalUnitState] = []
        for group in template.included_craft:
            source_template = self._resolve_printed_craft(group.printed_name, template)
            for instance_number in range(1, group.quantity + 1):
                if source_template is not None:
                    result.append(
                        self._create_profile_unit(
                            entry,
                            source_template,
                            instance_number,
                            parent_unit_id=parent.unit_id,
                            vessel_name="",
                            metadata={"included_craft_source": group.printed_name},
                        )
                    )
                else:
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
