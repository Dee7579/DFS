"""Fleet print planning and sheet deduplication.

Ships remain individual fleet entries; fighter and reusable small-craft sheets are
collapsed to one reference sheet per stable profile ID across the selected fleet.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Mapping, Any

from dfs.domain.catalog import PlatformDetail, PlatformFilter, PlatformProfile
from dfs.domain.fleet import Fleet
from dfs.domain.fleet.included_craft import normalize_craft_name, parse_included_craft
from dfs.domain.fleet.replacements import replacement_map
from dfs.domain.fleet.huge_hangars import embarked_profile_ids


@dataclass(frozen=True, slots=True)
class FleetPrintItem:
    item_key: str
    kind: str  # ship | craft
    profile_id: int
    ship_id: int
    platform_name: str
    vessel_name: str
    fleet_name: str
    faction_name: str
    file_name: str
    quantity_represented: int
    copies: int
    already_printed: bool = False
    options: Mapping[str, Any] = field(default_factory=dict)

    @property
    def display_name(self) -> str:
        if self.vessel_name:
            return f"{self.platform_name} — {self.vessel_name}"
        return self.platform_name


class FleetPrintPlanner:
    """Build printable ship entries and deduplicated craft references."""

    def __init__(self, catalog, platform_details) -> None:
        self._catalog = catalog
        self._details = platform_details
        self._profile_platform_cache: dict[int, PlatformDetail | None] = {}
        self._craft_cache: dict[tuple[str, int | None, int | None], tuple[PlatformDetail, PlatformProfile] | None] = {}

    @staticmethod
    def _is_reusable_craft(profile: PlatformProfile) -> bool:
        return any(trait.casefold().startswith("fighter") for trait in profile.traits)

    def _platform_for_profile(self, profile_id: int) -> PlatformDetail | None:
        if profile_id in self._profile_platform_cache:
            return self._profile_platform_cache[profile_id]
        profile = self._details.get_profile(profile_id)
        if profile is None:
            self._profile_platform_cache[profile_id] = None
            return None
        result = None
        for summary in self._catalog.search(PlatformFilter(fleet_list_ids=(profile.fleet_list_id,), limit=1000)):
            detail = self._details.get(summary.ship_id)
            if detail and any(candidate.profile_id == profile_id for candidate in detail.profiles):
                result = detail
                break
        self._profile_platform_cache[profile_id] = result
        return result

    def _resolve_craft(
        self,
        printed_name: str,
        fleet_list_id: int | None,
        faction_id: int | None,
    ) -> tuple[PlatformDetail, PlatformProfile] | None:
        key = (normalize_craft_name(printed_name), fleet_list_id, faction_id)
        if key in self._craft_cache:
            return self._craft_cache[key]
        target = key[0]
        best = None
        best_score = -1

        # Search the owning faction first, then fall back to the complete catalog.
        # Several official craft are shared across factions (for example Earth
        # Alliance carriers use Aurora Starfuries whose canonical platform record
        # is shared with the Interstellar Alliance). Restricting resolution to the
        # parent faction therefore causes valid included craft to disappear from
        # fleet print plans.
        filter_passes = []
        if faction_id:
            filter_passes.append(PlatformFilter(faction_ids=(faction_id,), limit=1000))
        filter_passes.append(PlatformFilter(limit=1000))

        seen_ship_ids: set[int] = set()
        for search_pass, filters in enumerate(filter_passes):
            for summary in self._catalog.search(filters):
                if summary.ship_id in seen_ship_ids:
                    continue
                seen_ship_ids.add(summary.ship_id)

                normalized = normalize_craft_name(summary.name)
                if normalized == target:
                    score = 100
                elif target in normalized or normalized in target:
                    score = 60
                else:
                    score = len(set(target.split()) & set(normalized.split())) * 10

                detail = self._details.get(summary.ship_id)
                if detail is None or not detail.profiles:
                    continue

                profile = next(
                    (candidate for candidate in detail.profiles if candidate.fleet_list_id == fleet_list_id),
                    detail.profiles[0],
                )

                # Prefer a profile from the selected fleet list, then the owning
                # faction, while still allowing a canonical shared-craft record.
                if profile.fleet_list_id == fleet_list_id:
                    score += 8
                detail_faction_id = getattr(detail, "faction_id", None)
                if faction_id and detail_faction_id == faction_id:
                    score += 4
                if search_pass == 0:
                    score += 2

                if score <= best_score:
                    continue
                best = (detail, profile)
                best_score = score

        if best_score < 20:
            best = None
        self._craft_cache[key] = best
        return best

    def plan(self, fleet: Fleet) -> tuple[FleetPrintItem, ...]:
        history = dict(fleet.metadata.get("print_history", {}))
        roster_item = FleetPrintItem(
            item_key="roster",
            kind="roster",
            profile_id=0,
            ship_id=0,
            platform_name="Fleet Roster",
            vessel_name=fleet.name,
            fleet_name="",
            faction_name="",
            file_name="",
            quantity_represented=len(fleet.entries),
            copies=1,
            already_printed="roster" in history,
        )
        ships: list[FleetPrintItem] = []
        craft_totals: dict[int, tuple[PlatformDetail, PlatformProfile, int]] = {}

        for entry in fleet.entries:
            profile = self._details.get_profile(entry.profile_id)
            detail = self._platform_for_profile(entry.profile_id)
            if profile is None or detail is None:
                continue

            if self._is_reusable_craft(profile):
                previous = craft_totals.get(profile.profile_id)
                total = entry.quantity + (previous[2] if previous else 0)
                craft_totals[profile.profile_id] = (detail, profile, total)
            else:
                key = f"ship:{entry.entry_id}"
                ships.append(FleetPrintItem(
                    item_key=key,
                    kind="ship",
                    profile_id=profile.profile_id,
                    ship_id=detail.ship_id,
                    platform_name=detail.name,
                    vessel_name=entry.vessel_name,
                    fleet_name=profile.fleet_name,
                    faction_name=detail.faction_name,
                    file_name=detail.file_name,
                    quantity_represented=entry.quantity,
                    copies=entry.quantity,
                    already_printed=key in history,
                    options=dict(entry.options),
                ))

            selected_replacements = replacement_map(entry.options)
            for included in parse_included_craft(profile.craft):
                source_replacements = selected_replacements.get(included.printed_name, {})
                source_total = included.quantity * entry.quantity
                replaced_total = sum(int(value) for value in source_replacements.values())
                remaining = max(0, source_total - replaced_total)
                if remaining:
                    resolved = self._resolve_craft(included.printed_name, profile.fleet_list_id, fleet.faction_id)
                    if resolved is not None:
                        craft_detail, craft_profile = resolved
                        previous = craft_totals.get(craft_profile.profile_id)
                        total = remaining + (previous[2] if previous else 0)
                        craft_totals[craft_profile.profile_id] = (craft_detail, craft_profile, total)
                for raw_profile_id, quantity in source_replacements.items():
                    try:
                        replacement_profile_id = int(raw_profile_id)
                    except (TypeError, ValueError):
                        continue
                    replacement_profile = self._details.get_profile(replacement_profile_id)
                    replacement_detail = self._platform_for_profile(replacement_profile_id)
                    if replacement_profile is None or replacement_detail is None:
                        continue
                    previous = craft_totals.get(replacement_profile_id)
                    total = int(quantity) + (previous[2] if previous else 0)
                    craft_totals[replacement_profile_id] = (replacement_detail, replacement_profile, total)


            # Huge Hangars contents are individual, full ship instances. They do
            # not spend FAP, but each requires its own damage/crew sheet.
            name_counts: dict[str, int] = {}
            for index, embarked_profile_id in enumerate(embarked_profile_ids(entry.options), start=1):
                embarked_profile = self._details.get_profile(embarked_profile_id)
                embarked_detail = self._platform_for_profile(embarked_profile_id)
                if embarked_profile is None or embarked_detail is None:
                    continue
                name_counts[embarked_detail.name] = name_counts.get(embarked_detail.name, 0) + 1
                instance_number = name_counts[embarked_detail.name]
                key = f"embarked:{entry.entry_id}:{index}"
                ships.append(FleetPrintItem(
                    item_key=key,
                    kind="ship",
                    profile_id=embarked_profile.profile_id,
                    ship_id=embarked_detail.ship_id,
                    platform_name=embarked_detail.name,
                    vessel_name=f"Embarked #{instance_number}",
                    fleet_name=embarked_profile.fleet_name,
                    faction_name=embarked_detail.faction_name,
                    file_name=embarked_detail.file_name,
                    quantity_represented=1,
                    copies=1,
                    already_printed=key in history,
                    options={"embarked": True, "parent_entry_id": entry.entry_id},
                ))

        craft_items = []
        for profile_id, (detail, profile, total) in sorted(
            craft_totals.items(), key=lambda pair: pair[1][0].name.casefold()
        ):
            key = f"craft:{profile_id}"
            craft_items.append(FleetPrintItem(
                item_key=key,
                kind="craft",
                profile_id=profile_id,
                ship_id=detail.ship_id,
                platform_name=detail.name,
                vessel_name="",
                fleet_name=profile.fleet_name,
                faction_name=detail.faction_name,
                file_name=detail.file_name,
                quantity_represented=total,
                copies=1,
                already_printed=key in history,
            ))
        return tuple([roster_item, *ships, *craft_items])

    @staticmethod
    def mark_printed(fleet: Fleet, item_keys: Iterable[str], timestamp: str) -> Fleet:
        from dataclasses import replace
        history = dict(fleet.metadata.get("print_history", {}))
        for key in item_keys:
            history[str(key)] = timestamp
        metadata = dict(fleet.metadata)
        metadata["print_history"] = history
        return replace(fleet, metadata=metadata)
