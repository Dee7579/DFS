"""Reusable fleet editing, resolution, summarization, and validation service."""
from __future__ import annotations

from dataclasses import replace
from uuid import uuid4
from typing import Iterable

from dfs.domain.fleet import (
    Fleet,
    FleetConstructionProfile,
    FleetEntry,
    FleetSummary,
    NoValidationConstructionProfile,
    PointsConstructionProfile,
)
from dfs.repositories.platform_repository import PlatformRepository
from dfs.domain.fleet.replacements import replacement_map, with_replacement_map, with_replacement_cost
from dfs.domain.fleet.ordnance import with_missile_loadouts
from dfs.domain.fleet.huge_hangars import with_embarked_profile_ids
from dfs.domain.fleet.rules import RuleCategory, RuleContext, RuleMessage
from dfs.services.fleet.b5_acta_profile import (
    B5ACTAAdvisoryPriorityProfile, B5ACTASandboxProfile, B5ACTAStandardPriorityProfile,
)


class FleetConstructionService:
    def __init__(self, platforms: PlatformRepository):
        self._platforms = platforms
        built_ins: tuple[FleetConstructionProfile, ...] = (
            B5ACTAStandardPriorityProfile(),
            B5ACTAAdvisoryPriorityProfile(),
            B5ACTASandboxProfile(),
            PointsConstructionProfile(),
            NoValidationConstructionProfile(),
        )
        self._profiles = {p.profile_id: p for p in built_ins}

    def register_profile(self, profile: FleetConstructionProfile) -> None:
        if profile.profile_id in self._profiles:
            raise ValueError(f"Construction profile already registered: {profile.profile_id}")
        self._profiles[profile.profile_id] = profile

    def profiles(self) -> tuple[FleetConstructionProfile, ...]:
        return tuple(self._profiles.values())

    def create_fleet(
        self,
        name: str,
        game_system_id: str = "b5_acta",
        construction_profile_id: str = "b5_acta_priority_standard",
        faction_id: int | None = None,
        fleet_list_id: int | None = None,
        selected_year: int | None = None,
        scenario_priority: str = "Raid",
        fleet_allocation_points: int = 1,
    ) -> Fleet:
        if construction_profile_id not in self._profiles:
            raise KeyError(f"Unknown construction profile: {construction_profile_id}")
        fleet = Fleet.create(
            name=name,
            game_system_id=game_system_id,
            construction_profile_id=construction_profile_id,
            faction_id=faction_id,
            fleet_list_id=fleet_list_id,
            selected_year=selected_year,
        )
        return replace(fleet, metadata={
            "scenario_priority": scenario_priority,
            "fleet_allocation_points": fleet_allocation_points,
        })

    def add_profile(self, fleet: Fleet, profile_id: int, quantity: int = 1) -> Fleet:
        return fleet.add_entry(FleetEntry.create(profile_id=profile_id, quantity=quantity))

    def add_grouped_profile(self, fleet: Fleet, profile_id: int, group_size: int) -> Fleet:
        """Add one grouped purchase as separate vessel rows linked to one cost."""
        if group_size <= 1:
            return self.add_profile(fleet, profile_id)
        group_id = str(uuid4())
        updated = fleet
        for index in range(group_size):
            updated = updated.add_entry(FleetEntry.create(
                profile_id=profile_id,
                quantity=1,
                options={
                    "grouped_purchase_group_id": group_id,
                    "grouped_purchase_size": group_size,
                    "grouped_purchase_charge": 1 if index == 0 else 0,
                },
            ))
        return updated

    def preview_add_profile_rules(
        self,
        fleet: Fleet,
        profile_id: int,
        *,
        categories: tuple[RuleCategory, ...] = (RuleCategory.PLATFORM,),
    ) -> tuple[RuleMessage, ...]:
        """Return newly triggered rule messages for a hypothetical purchase.

        This keeps the Fleet Builder data-driven: the UI asks the active rule
        engine what adding a platform would do instead of embedding faction
        restrictions in widget code.
        """
        profile = self._profiles.get(fleet.construction_profile_id)
        engine = getattr(profile, "rule_engine", None)
        if engine is None:
            return ()
        current_resolved = self._resolve(fleet)
        current = engine.evaluate(fleet, current_resolved)
        hypothetical = self.add_profile(fleet, profile_id)
        future = engine.evaluate(hypothetical, self._resolve(hypothetical))
        allowed_rule_ids = {
            descriptor.rule_id
            for descriptor in engine.descriptors()
            if descriptor.category in categories
        }
        current_signatures = {
            (message.rule_id, message.message, message.platform_name)
            for message in current
        }
        return tuple(
            message for message in future
            if message.rule_id in allowed_rule_ids
            and (message.rule_id, message.message, message.platform_name) not in current_signatures
        )

    def inspect_rules(self, fleet: Fleet, profile_id: int | None = None):
        """Return rule descriptors and messages for the fleet or a hypothetical add.

        This is a read-only inspection API for the Knowledge Panel.  Rules remain
        owned by the active construction profile; the UI receives only metadata
        and evaluation results.
        """
        profile = self._profiles.get(fleet.construction_profile_id)
        engine = getattr(profile, "rule_engine", None)
        if engine is None:
            return (), ()
        inspected = self.add_profile(fleet, profile_id) if profile_id is not None else fleet
        messages = tuple(engine.evaluate(inspected, self._resolve(inspected)))
        return tuple(engine.descriptors()), messages

    def set_craft_replacements(
        self,
        fleet: Fleet,
        entry_id: str,
        source_name: str,
        replacements: dict[int, int],
        patrol_choices: int = 0,
    ) -> Fleet:
        """Persist one parent ship's replacement-craft allocation."""
        updated: list[FleetEntry] = []
        found = False
        for entry in fleet.entries:
            if entry.entry_id != entry_id:
                updated.append(entry)
                continue
            found = True
            values = replacement_map(entry.options)
            clean = {str(profile_id): int(quantity) for profile_id, quantity in replacements.items() if int(quantity) > 0}
            if clean:
                values[source_name] = clean
            else:
                values.pop(source_name, None)
            options = with_replacement_map(entry.options, values)
            options = with_replacement_cost(options, source_name, patrol_choices)
            updated.append(replace(entry, options=options))
        if not found:
            raise KeyError(f"Fleet entry not found: {entry_id}")
        return fleet.replace_entries(tuple(updated))


    def set_huge_hangars(
        self, fleet: Fleet, entry_id: str, embarked_profile_ids: tuple[int, ...]
    ) -> Fleet:
        """Persist individual embarked ship instances for one Huge Hangars parent."""
        updated: list[FleetEntry] = []
        found = False
        for entry in fleet.entries:
            if entry.entry_id != entry_id:
                updated.append(entry)
                continue
            found = True
            updated.append(replace(
                entry, options=with_embarked_profile_ids(entry.options, embarked_profile_ids)
            ))
        if not found:
            raise KeyError(f"Fleet entry not found: {entry_id}")
        return fleet.replace_entries(tuple(updated))

    def set_missile_loadouts(
        self, fleet: Fleet, entry_id: str, loadouts: dict[str, str]
    ) -> Fleet:
        """Persist configurable missile selections for one purchased ship."""
        updated: list[FleetEntry] = []
        found = False
        for entry in fleet.entries:
            if entry.entry_id != entry_id:
                updated.append(entry)
                continue
            found = True
            updated.append(replace(entry, options=with_missile_loadouts(entry.options, loadouts)))
        if not found:
            raise KeyError(f"Fleet entry not found: {entry_id}")
        return fleet.replace_entries(tuple(updated))

    def remove_entry(self, fleet: Fleet, entry_id: str) -> Fleet:
        return fleet.replace_entries(tuple(e for e in fleet.entries if e.entry_id != entry_id))

    def set_quantity(self, fleet: Fleet, entry_id: str, quantity: int) -> Fleet:
        entries = tuple(
            e.with_quantity(quantity) if e.entry_id == entry_id else e
            for e in fleet.entries
        )
        if entries == fleet.entries:
            raise KeyError(f"Fleet entry not found: {entry_id}")
        return fleet.replace_entries(entries)

    def reorder_entries(self, fleet: Fleet, ordered_entry_ids: Iterable[str]) -> Fleet:
        """Return *fleet* with purchased entries in the requested order.

        Included craft are derived presentation rows, so they always remain attached
        to their parent entry when the parent order changes.
        """
        requested = tuple(ordered_entry_ids)
        current_ids = tuple(entry.entry_id for entry in fleet.entries)
        if len(requested) != len(current_ids) or set(requested) != set(current_ids):
            raise ValueError("ordered_entry_ids must contain every fleet entry exactly once")
        by_id = {entry.entry_id: entry for entry in fleet.entries}
        return fleet.replace_entries(tuple(by_id[entry_id] for entry_id in requested))

    def move_entry(
        self,
        fleet: Fleet,
        entry_id: str,
        target_entry_id: str | None = None,
        *,
        before: bool = True,
    ) -> Fleet:
        """Move one purchased entry before or after another entry.

        A ``None`` target moves the entry to the end. This method deliberately
        operates on domain entries rather than table rows so included-craft child
        rows travel with their parent automatically.
        """
        entries = list(fleet.entries)
        source = next((entry for entry in entries if entry.entry_id == entry_id), None)
        if source is None:
            raise KeyError(f"Fleet entry not found: {entry_id}")
        entries.remove(source)
        if target_entry_id is None:
            entries.append(source)
            return fleet.replace_entries(tuple(entries))
        if target_entry_id == entry_id:
            return fleet
        target_index = next(
            (index for index, entry in enumerate(entries) if entry.entry_id == target_entry_id),
            None,
        )
        if target_index is None:
            raise KeyError(f"Target fleet entry not found: {target_entry_id}")
        entries.insert(target_index if before else target_index + 1, source)
        return fleet.replace_entries(tuple(entries))

    def set_vessel_name(self, fleet: Fleet, entry_id: str, vessel_name: str) -> Fleet:
        """Name an individual vessel, splitting grouped quantities when needed.

        A named roster entry must represent one physical vessel so Tactical Assistant,
        campaign records, and named PDF generation can address it independently.
        """
        updated: list[FleetEntry] = []
        found = False
        for entry in fleet.entries:
            if entry.entry_id != entry_id:
                updated.append(entry)
                continue
            found = True
            clean_name = vessel_name.strip()
            if clean_name and entry.quantity > 1:
                updated.append(replace(entry, quantity=1, vessel_name=clean_name))
                updated.append(FleetEntry.create(
                    profile_id=entry.profile_id,
                    quantity=entry.quantity - 1,
                    options=entry.options,
                    notes=entry.notes,
                ))
            else:
                updated.append(entry.with_vessel_name(clean_name))
        if not found:
            raise KeyError(f"Fleet entry not found: {entry_id}")
        return fleet.replace_entries(tuple(updated))

    def _resolve(self, fleet: Fleet):
        resolved = {}
        for entry in fleet.entries:
            resolved[entry.entry_id] = self._platforms.get_profile_by_id(entry.profile_id)
        return resolved

    def summarize(self, fleet: Fleet) -> FleetSummary:
        try:
            profile = self._profiles[fleet.construction_profile_id]
        except KeyError as exc:
            raise KeyError(f"Unknown construction profile: {fleet.construction_profile_id}") from exc
        return profile.summarize(fleet, self._resolve(fleet))
