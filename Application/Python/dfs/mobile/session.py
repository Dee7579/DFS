"""Pure-Python state facade for the touch-first DFS companion."""

from __future__ import annotations

from collections import Counter
from dataclasses import replace
from pathlib import Path
import re
from typing import Any

from dfs.domain.catalog import PlatformDetail, PlatformFilter, PlatformProfile
from dfs.domain.fleet import Fleet, ValidationSeverity
from dfs.domain.fleet.grouped_purchases import (
    grouped_purchase_size,
    purchased_choice_count,
)
from dfs.domain.fleet.priority import (
    PRIORITIES,
    PRIORITY_INDEX,
    can_add_ancient,
    can_add_priority,
    format_unaffordable_choice,
)
from dfs.domain.in_service import parse_in_service
from dfs.domain.tactical import TacticalGameState, TacticalUnitState, UnitKind
from dfs.mobile.application import MobileApplicationContext
from dfs.services.fleet.b5_allied_contingents import permitted_profile


def _safe_stem(value: str, fallback: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9 _-]+", "_", value).strip(" ._")
    return cleaned or fallback


class MobileSession:
    """Own mobile UI state while delegating rules to shared DFS services."""

    def __init__(self, context: MobileApplicationContext, data_root: str | Path) -> None:
        self.context = context
        self.data_root = Path(data_root).expanduser().resolve()
        self.fleet_root = self.data_root / "Fleets"
        self.game_root = self.data_root / "Games"
        self.fleet_root.mkdir(parents=True, exist_ok=True)
        self.game_root.mkdir(parents=True, exist_ok=True)
        self.fleet: Fleet | None = None
        self.game: TacticalGameState | None = None
        self._profile_index: dict[int, tuple[int, str, PlatformProfile]] = {}
        self._platform_index: dict[int, PlatformDetail] = {}

    # Catalog -----------------------------------------------------------------

    def factions(self) -> list[dict[str, Any]]:
        return [
            {"id": int(option.id), "label": option.label, "count": option.count}
            for option in self.context.catalog.list_factions()
            if self.context.catalog.list_fleets(int(option.id))
        ]

    def fleet_lists(self, faction_id: int) -> list[dict[str, Any]]:
        return [
            {"id": int(option.id), "label": option.label, "count": option.count}
            for option in self.context.catalog.list_fleets(int(faction_id))
            if self.context.catalog.search(
                PlatformFilter(fleet_list_ids=(int(option.id),), limit=1)
            )
        ]

    def search_platforms(
        self,
        query: str = "",
        faction_id: int | None = None,
        *,
        limit: int = 500,
    ) -> list[dict[str, Any]]:
        filters = PlatformFilter(
            search_text=query,
            faction_ids=(int(faction_id),) if faction_id else (),
            limit=limit,
        )
        return [
            {
                "shipId": summary.ship_id,
                "name": summary.name,
                "shipClass": summary.ship_class,
                "faction": summary.faction_name,
                "fleets": " • ".join(summary.fleet_names),
                "priorities": " • ".join(summary.priority_levels),
                "profileCount": summary.profile_count,
            }
            for summary in self.context.catalog.search(filters)
        ]

    def platform_detail(self, ship_id: int) -> dict[str, Any]:
        detail = self.context.platform_details.get(int(ship_id))
        self._platform_index[detail.ship_id] = detail
        return {
            "shipId": detail.ship_id,
            "name": detail.name,
            "shipClass": detail.ship_class,
            "faction": detail.faction_name,
            "profiles": [self._profile_payload(profile) for profile in detail.profiles],
        }

    @staticmethod
    def _profile_payload(profile: PlatformProfile) -> dict[str, Any]:
        return {
            "profileId": profile.profile_id,
            "fleetListId": profile.fleet_list_id,
            "fleet": profile.fleet_name,
            "priority": profile.priority_level,
            "initiative": profile.initiative or "—",
            "speed": profile.speed or "—",
            "turn": profile.turn or "—",
            "hull": profile.hull or "—",
            "damage": profile.damage or "—",
            "crew": profile.crew or "—",
            "troops": profile.troops or "—",
            "craft": profile.craft or "None",
            "inService": profile.in_service or "—",
            "source": profile.source_book or "—",
            "traits": list(profile.traits),
            "traitsText": ", ".join(profile.traits) if profile.traits else "None",
            "notes": list(profile.notes),
            "weapons": [
                {
                    "arc": weapon.arc,
                    "name": weapon.name,
                    "range": weapon.range_value,
                    "attackDice": weapon.attack_dice,
                    "traits": weapon.traits,
                }
                for weapon in profile.weapons
            ],
        }

    def _ensure_profile_index(self) -> None:
        if self._profile_index:
            return
        for summary in self.context.catalog.search(PlatformFilter(limit=1000)):
            detail = self.context.platform_details.get(summary.ship_id)
            self._platform_index[summary.ship_id] = detail
            for profile in detail.profiles:
                self._profile_index[profile.profile_id] = (
                    summary.ship_id,
                    summary.name,
                    profile,
                )

    # Fleet Builder -----------------------------------------------------------

    def create_fleet(
        self,
        name: str,
        faction_id: int,
        fleet_list_id: int,
        scenario_priority: str = "Raid",
        fleet_allocation_points: int = 1,
        selected_year: int | None = None,
    ) -> dict[str, Any]:
        scenario = scenario_priority if scenario_priority in PRIORITY_INDEX else "Raid"
        self.fleet = self.context.fleets.create_fleet(
            name=name,
            construction_profile_id="b5_acta_priority_standard",
            faction_id=int(faction_id),
            fleet_list_id=int(fleet_list_id),
            selected_year=int(selected_year) if selected_year else None,
            scenario_priority=scenario,
            fleet_allocation_points=max(1, int(fleet_allocation_points)),
        )
        self.game = None
        self.save_fleet()
        return self.fleet_state()

    def available_profiles(self, query: str = "") -> list[dict[str, Any]]:
        if self.fleet is None or self.fleet.fleet_list_id is None:
            return []
        scenario = str(self.fleet.metadata.get("scenario_priority", "Raid"))
        scenario_index = PRIORITY_INDEX.get(scenario, PRIORITY_INDEX["Raid"])
        filters = PlatformFilter(
            search_text=query,
            fleet_list_ids=(self.fleet.fleet_list_id,),
            limit=1000,
        )
        results: list[dict[str, Any]] = []
        for summary in self.context.catalog.search(filters):
            detail = self.context.platform_details.get(summary.ship_id)
            for profile in detail.profiles:
                if profile.fleet_list_id != self.fleet.fleet_list_id:
                    continue
                if (
                    profile.priority_level in PRIORITY_INDEX
                    and PRIORITY_INDEX[profile.priority_level] > scenario_index
                ):
                    continue
                allowed, reason = self._can_add_profile(profile)
                results.append(
                    {
                        "shipId": summary.ship_id,
                        "profileId": profile.profile_id,
                        "name": summary.name,
                        "priority": profile.priority_level,
                        "fleet": profile.fleet_name,
                        "inService": profile.in_service,
                        "allowed": allowed,
                        "reason": reason,
                    }
                )
        return results

    def _selected_priority_counts(self) -> Counter[str]:
        counts: Counter[str] = Counter()
        if self.fleet is None:
            return counts
        for entry in self.fleet.entries:
            profile = self.context.platform_details.get_profile(entry.profile_id)
            if profile is not None and profile.priority_level in PRIORITIES:
                counts[profile.priority_level] += purchased_choice_count(
                    entry.profile_id,
                    entry.quantity,
                    entry.options,
                )
        return counts

    def _can_add_profile(self, profile: PlatformProfile) -> tuple[bool, str]:
        if self.fleet is None or self.fleet.fleet_list_id is None:
            return False, "Select a fleet / era first."
        reasons: list[str] = []
        if not permitted_profile(self.fleet, profile):
            reasons.append("This fleet list does not permit that platform")
        scenario = str(self.fleet.metadata.get("scenario_priority", "Raid"))
        fap = int(self.fleet.metadata.get("fleet_allocation_points", 1))
        if profile.priority_level == "Ancient" and self.fleet.fleet_list_id == 19:
            selected = sum(
                entry.quantity
                for entry in self.fleet.entries
                if (
                    self.context.platform_details.get_profile(entry.profile_id) is not None
                    and self.context.platform_details.get_profile(entry.profile_id).priority_level
                    == "Ancient"
                )
            )
            if not can_add_ancient(scenario, fap, selected):
                reasons.append("No Ancient choice remains in the fleet budget")
        elif profile.priority_level in PRIORITIES:
            counts = self._selected_priority_counts()
            if not can_add_priority(scenario, fap, counts, profile.priority_level):
                reasons.append(
                    format_unaffordable_choice(
                        scenario,
                        fap,
                        counts,
                        profile.priority_level,
                    )
                )
        if self.fleet.selected_year is not None:
            if not parse_in_service(profile.in_service).includes(self.fleet.selected_year):
                reasons.append(
                    f"The platform is not in service in {self.fleet.selected_year}"
                )
        for message in self.context.fleets.preview_add_profile_rules(
            self.fleet,
            profile.profile_id,
        ):
            if (
                message.rule_id == "B5-GROUPED-PURCHASE-001"
                and grouped_purchase_size(profile.profile_id) > 1
            ):
                continue
            reasons.append(f"{message.title}: {message.message}")
        if not reasons:
            return True, ""
        return False, "\n\n".join(reasons)

    def add_profile(self, profile_id: int) -> dict[str, Any]:
        if self.fleet is None:
            raise ValueError("Create a fleet before adding platforms.")
        profile = self.context.platform_details.get_profile(int(profile_id))
        if profile is None:
            raise KeyError(f"Unknown profile ID: {profile_id}")
        allowed, reason = self._can_add_profile(profile)
        if not allowed:
            raise ValueError(reason)
        self.fleet = self.context.fleets.add_grouped_profile(
            self.fleet,
            profile.profile_id,
            grouped_purchase_size(profile.profile_id),
        )
        self.save_fleet()
        return self.fleet_state()

    def remove_entry(self, entry_id: str) -> dict[str, Any]:
        if self.fleet is None:
            raise ValueError("No fleet is active.")
        self.fleet = self.context.fleets.remove_entry(self.fleet, str(entry_id))
        self.save_fleet()
        return self.fleet_state()

    def fleet_state(self) -> dict[str, Any]:
        if self.fleet is None:
            return {
                "active": False,
                "name": "No fleet",
                "roster": [],
                "validation": [],
            }
        self._ensure_profile_index()
        roster: list[dict[str, Any]] = []
        for entry in self.fleet.entries:
            ship_id, platform_name, profile = self._profile_index.get(
                entry.profile_id,
                (0, f"Profile {entry.profile_id}", None),
            )
            roster.append(
                {
                    "entryId": entry.entry_id,
                    "shipId": ship_id,
                    "profileId": entry.profile_id,
                    "name": entry.vessel_name or platform_name,
                    "platformName": platform_name,
                    "priority": profile.priority_level if profile else "",
                    "fleet": profile.fleet_name if profile else "",
                    "quantity": entry.quantity,
                }
            )
        summary = self.context.fleets.summarize(self.fleet)
        validation = [
            {
                "severity": message.severity.value,
                "label": {
                    ValidationSeverity.ERROR: "INVALID",
                    ValidationSeverity.WARNING: "WARNING",
                    ValidationSeverity.INFO: "INFO",
                }[message.severity],
                "message": message.message,
            }
            for message in summary.validation.messages
        ]
        selected = ", ".join(
            f"{count} {priority}"
            for priority, count in summary.priority_counts.items()
        ) or "No selections"
        return {
            "active": True,
            "fleetId": self.fleet.fleet_id,
            "name": self.fleet.name,
            "factionId": self.fleet.faction_id or 0,
            "fleetListId": self.fleet.fleet_list_id or 0,
            "year": self.fleet.selected_year or 0,
            "scenarioPriority": str(
                self.fleet.metadata.get("scenario_priority", "Raid")
            ),
            "fleetAllocationPoints": int(
                self.fleet.metadata.get("fleet_allocation_points", 1)
            ),
            "budget": summary.budget_label,
            "selected": selected,
            "remaining": summary.remaining_label,
            "isValid": summary.validation.is_valid,
            "roster": roster,
            "validation": validation,
        }

    def save_fleet(self) -> str:
        if self.fleet is None:
            raise ValueError("No fleet is active.")
        filename = _safe_stem(self.fleet.name, "Untitled Fleet")
        path = self.fleet_root / f"{filename}{self.context.fleet_files.FILE_EXTENSION}"
        return str(self.context.fleet_files.save(self.fleet, path))

    def saved_fleets(self) -> list[dict[str, str]]:
        return [
            {"name": path.name.removesuffix(self.context.fleet_files.FILE_EXTENSION), "path": str(path)}
            for path in sorted(self.fleet_root.glob(f"*{self.context.fleet_files.FILE_EXTENSION}"))
        ]

    def load_fleet(self, path: str) -> dict[str, Any]:
        source = Path(path).expanduser().resolve()
        if self.fleet_root not in source.parents:
            raise ValueError("Fleet file must be inside the DFS mobile fleet folder.")
        self.fleet = self.context.fleet_files.load(source)
        self.game = None
        return self.fleet_state()

    # Tactical Assistant ------------------------------------------------------

    def start_battle(self, name: str = "") -> dict[str, Any]:
        if self.fleet is None or not self.fleet.entries:
            raise ValueError("Add at least one platform before starting a battle.")
        self.game = self.context.tactical_games.create_from_fleet(
            self.fleet,
            game_name=name.strip() or None,
        )
        self.save_game()
        return self.game_state()

    @staticmethod
    def _track_payload(track) -> dict[str, Any]:
        return {
            "available": track.available,
            "current": track.current if track.current is not None else 0,
            "maximum": track.maximum if track.maximum is not None else 0,
            "threshold": track.threshold if track.threshold is not None else 0,
        }

    @classmethod
    def _unit_payload(cls, unit: TacticalUnitState) -> dict[str, Any]:
        status_parts = []
        if unit.is_destroyed:
            status_parts.append("Destroyed")
        else:
            if unit.is_crippled:
                status_parts.append("Crippled")
            if unit.is_skeleton_crew:
                status_parts.append("Skeleton Crew")
            if unit.is_adrift:
                status_parts.append("Adrift")
        if not status_parts:
            status_parts.append("Operational")
        return {
            "unitId": unit.unit_id,
            "name": unit.display_name,
            "platformName": unit.platform_name,
            "kind": unit.kind.value,
            "priority": unit.priority_level,
            "status": " • ".join(status_parts),
            "destroyed": unit.is_destroyed,
            "crippled": unit.is_crippled,
            "skeletonCrew": unit.is_skeleton_crew,
            "speed": unit.effective_speed,
            "turn": unit.effective_turn,
            "hull": unit.hull,
            "troops": unit.effective_troops,
            "damage": cls._track_payload(unit.damage),
            "crew": cls._track_payload(unit.crew),
            "shields": cls._track_payload(unit.shields),
            "traits": [
                {
                    "key": trait.trait_key,
                    "name": trait.name,
                    "status": unit.trait_status(trait.trait_key),
                }
                for trait in unit.traits
            ],
            "weapons": [
                {
                    "key": weapon.weapon_key,
                    "arc": weapon.arc,
                    "name": weapon.name,
                    "range": weapon.range_value,
                    "attackDice": unit.effective_attack_dice(weapon),
                    "traits": weapon.traits,
                    "status": unit.weapon_status(weapon.weapon_key),
                }
                for weapon in unit.weapons
            ],
            "notes": list(unit.source_notes),
        }

    def game_state(self) -> dict[str, Any]:
        if self.game is None:
            return {"active": False, "name": "No active battle", "turn": 0, "units": []}
        return {
            "active": True,
            "gameId": self.game.game_id,
            "name": self.game.name,
            "turn": self.game.turn_number,
            "phase": self.game.phase.value,
            "units": [self._unit_payload(unit) for unit in self.game.units],
        }

    def unit_detail(self, unit_id: str) -> dict[str, Any]:
        if self.game is None:
            return {}
        return self._unit_payload(self.game.get_unit(str(unit_id)))

    def adjust_track(self, unit_id: str, track_name: str, delta: int) -> dict[str, Any]:
        if self.game is None:
            raise ValueError("No tactical game is active.")
        unit = self.game.get_unit(str(unit_id))
        amount = abs(int(delta))
        if track_name == "damage":
            unit = unit.restore_damage(amount) if delta > 0 else unit.lose_damage(amount)
        elif track_name == "crew":
            unit = unit.restore_crew(amount) if delta > 0 else unit.lose_crew(amount)
        elif track_name == "shields":
            unit = unit.restore_shields(amount) if delta > 0 else unit.lose_shields(amount)
        else:
            raise ValueError(f"Unknown tactical track: {track_name}")
        self.game = self.game.replace_unit(unit)
        self.save_game()
        return self._unit_payload(unit)

    def set_destroyed(self, unit_id: str, destroyed: bool) -> dict[str, Any]:
        if self.game is None:
            raise ValueError("No tactical game is active.")
        unit = self.game.get_unit(str(unit_id)).mark_destroyed(bool(destroyed))
        self.game = self.game.replace_unit(unit)
        self.save_game()
        return self._unit_payload(unit)

    def advance_turn(self) -> dict[str, Any]:
        if self.game is None:
            raise ValueError("No tactical game is active.")
        self.game = self.game.advance_turn()
        self.save_game()
        return self.game_state()

    def save_game(self) -> str:
        if self.game is None:
            raise ValueError("No tactical game is active.")
        filename = _safe_stem(self.game.name, "DFS Battle")
        path = self.game_root / f"{filename}{self.context.tactical_games.FILE_EXTENSION}"
        return str(self.context.tactical_games.save(self.game, path))

    # Rules -------------------------------------------------------------------

    def search_rules(self, query: str) -> list[dict[str, Any]]:
        return [
            {
                "title": entry.title,
                "category": entry.category,
                "text": entry.text,
                "source": entry.source,
                "seeAlso": list(entry.see_also),
            }
            for entry in self.context.codex.search(query)
        ]
