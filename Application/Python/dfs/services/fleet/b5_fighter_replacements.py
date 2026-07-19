"""Official B5 ACTA fighter-replacement definitions and resolution service."""
from __future__ import annotations

from dataclasses import dataclass

from dfs.domain.catalog import PlatformDetail, PlatformFilter, PlatformProfile
from dfs.domain.fleet.included_craft import normalize_craft_name, parse_included_craft
from dfs.domain.fleet.replacements import (
    FighterReplacementDefinition,
    ReplacementOpportunity,
    ReplacementTarget,
    ResolvedReplacementTarget,
)
from dfs.domain.in_service import parse_in_service


FLEET_LISTS = "B5 ACTA Fleet Lists"


B5_FIGHTER_REPLACEMENTS: tuple[FighterReplacementDefinition, ...] = (
    FighterReplacementDefinition(
        "BRAKIRI_FIGHTER_REPLACEMENTS", ("Brakiri Syndicracy",), ("Falkosi",),
        (ReplacementTarget("Pikatos", "Pikatos Heavy Fighter Flight"), ReplacementTarget("Breaching Pod", "Breaching Pod", carries_parent_troop=True)),
        FLEET_LISTS, 99,
    ),
    FighterReplacementDefinition(
        "CENTAURI_FIGHTER_REPLACEMENTS", ("Centauri Republic",), ("Sentri",),
        (ReplacementTarget("Razik", "Razik Light Fighter Flight"), ReplacementTarget("Breaching Pod", "Centauri Breaching Pod", carries_parent_troop=True), ReplacementTarget("Rutarian", "Rutarian Strike Fighter", patrol_group_size=4)),
        FLEET_LISTS, 71,
    ),
    FighterReplacementDefinition(
        "DILGAR_FIGHTER_REPLACEMENTS", ("Dilgar Imperium",), ("Thorun Dartfighter",),
        (ReplacementTarget("Thorun Torpedofighter", "Thorun Torpedofighter"), ReplacementTarget("Breaching Pod", "Dilgar Breaching Pod", carries_parent_troop=True)),
        FLEET_LISTS, 40,
    ),
    FighterReplacementDefinition(
        "DRAZI_FIGHTER_REPLACEMENTS", ("Drazi Freehold",), ("Star Snake",),
        (ReplacementTarget("Breaching Pod", "Drazi Breaching Pod", carries_parent_troop=True),),
        FLEET_LISTS, 105,
    ),
    FighterReplacementDefinition(
        "EA_EARLY_YEARS_FIGHTER_REPLACEMENTS", ("Earth Alliance - The Early Years",), (),
        (ReplacementTarget("Tiger Starfury", "Tiger Starfury Flight"), ReplacementTarget("Nova Starfury", "Nova Starfury Flight"), ReplacementTarget("Breaching Pod", "EA Breaching Pod", carries_parent_troop=True)),
        FLEET_LISTS, 7, all_or_none=True, source_contains="Starfury",
    ),
    FighterReplacementDefinition(
        "EA_THIRD_AGE_FIGHTER_REPLACEMENTS", ("Earth Alliance - Third Age",), ("Aurora Starfury",),
        (ReplacementTarget("Badger Starfury", "Badger Starfury Flight"), ReplacementTarget("Thunderbolt Starfury", "Thunderbolt Starfury Flight", minimum_year=2259), ReplacementTarget("Breaching Pod", "EA Breaching Pod", carries_parent_troop=True)),
        FLEET_LISTS, 19,
    ),
    FighterReplacementDefinition(
        "EA_CRUSADE_FIGHTER_REPLACEMENTS", ("Earth Alliance - Crusade Era",), ("Aurora Starfury",),
        (ReplacementTarget("Badger Starfury", "Badger Starfury Flight"), ReplacementTarget("Thunderbolt Starfury", "Thunderbolt Starfury Flight"), ReplacementTarget("Breaching Pod", "EA Breaching Pod", carries_parent_troop=True), ReplacementTarget("Firebolt Starfury", "Firebolt Starfury Flight", minimum_year=2268, patrol_group_size=4)),
        FLEET_LISTS, 29,
    ),
    FighterReplacementDefinition(
        "ISA_STARFURY_REPLACEMENTS", ("Interstellar Alliance",), (),
        (ReplacementTarget("Thunderbolt Starfury", "Thunderbolt Starfury Flight"),),
        FLEET_LISTS, 82, source_contains="Starfury",
    ),
    FighterReplacementDefinition(
        "MINBARI_FIGHTER_REPLACEMENTS", ("Minbari Federation",), ("Nial",),
        (ReplacementTarget("Tishat", "Tishat Medium Fighter Flight", minimum_year=2231), ReplacementTarget("Breaching Pod", "Minbari Breaching Pod", carries_parent_troop=True)),
        FLEET_LISTS, 49,
    ),
    FighterReplacementDefinition(
        "NARN_FIGHTER_REPLACEMENTS", ("Narn Regime",), ("Frazi",),
        (ReplacementTarget("Gorith", "Gorith Flight"), ReplacementTarget("Breaching Pod", "Narn Breaching Pod", carries_parent_troop=True)),
        FLEET_LISTS, 59,
    ),
    FighterReplacementDefinition(
        "RAIDER_FIGHTER_REPLACEMENTS", ("Raiders",), ("Delta-V",),
        (ReplacementTarget("Breaching Pod", "Breaching Pod", carries_parent_troop=True), ReplacementTarget("Delta-V2", "Delta-V2 Fighter", minimum_year=2260, patrol_group_size=8)),
        FLEET_LISTS, 128,
    ),
)


class B5FighterReplacementService:
    def __init__(self, catalog, platform_details) -> None:
        self._catalog = catalog
        self._details = platform_details
        self._resolution_cache: dict[tuple[str, int | None], tuple[PlatformDetail, PlatformProfile] | None] = {}

    def _resolve_target(self, search_name: str, fleet_list_id: int | None) -> tuple[PlatformDetail, PlatformProfile] | None:
        key = (normalize_craft_name(search_name), fleet_list_id)
        if key in self._resolution_cache:
            return self._resolution_cache[key]
        target = key[0]
        best = None
        best_score = -1
        for summary in self._catalog.search(PlatformFilter(limit=1000)):
            normalized = normalize_craft_name(summary.name)
            if normalized == target:
                score = 100
            elif target in normalized or normalized in target:
                score = 65
            else:
                score = len(set(target.split()) & set(normalized.split())) * 10
            if score <= best_score:
                continue
            detail = self._details.get(summary.ship_id)
            if detail is None or not detail.profiles:
                continue
            profile = next((p for p in detail.profiles if p.fleet_list_id == fleet_list_id), detail.profiles[0])
            if profile.fleet_list_id == fleet_list_id:
                score += 8
            if score > best_score:
                best = (detail, profile)
                best_score = score
        if best_score < 20:
            best = None
        self._resolution_cache[key] = best
        return best

    @staticmethod
    def _definition_matches_source(definition: FighterReplacementDefinition, printed_name: str) -> bool:
        normalized = normalize_craft_name(printed_name)
        if definition.source_contains and normalize_craft_name(definition.source_contains) in normalized:
            return True
        return any(normalize_craft_name(name) in normalized for name in definition.source_search_names)

    def opportunities(self, profile: PlatformProfile, selected_year: int | None) -> tuple[ReplacementOpportunity, ...]:
        opportunities: list[ReplacementOpportunity] = []
        included = parse_included_craft(profile.craft)
        for definition in B5_FIGHTER_REPLACEMENTS:
            if profile.fleet_name not in definition.fleet_names:
                continue
            for craft in included:
                if not self._definition_matches_source(definition, craft.printed_name):
                    continue
                targets: list[ResolvedReplacementTarget] = []
                for target in definition.targets:
                    if target.minimum_year is not None and selected_year is not None and selected_year < target.minimum_year:
                        continue
                    resolved = self._resolve_target(target.search_name, profile.fleet_list_id)
                    if resolved is None:
                        continue
                    detail, target_profile = resolved
                    if selected_year is not None and not parse_in_service(target_profile.in_service).includes(selected_year):
                        continue
                    # Do not offer a no-op replacement back into the printed source type.
                    if normalize_craft_name(detail.name) == normalize_craft_name(craft.printed_name):
                        continue
                    targets.append(ResolvedReplacementTarget(target_profile.profile_id, detail.name, target_profile.fleet_name, target))
                if targets:
                    opportunities.append(ReplacementOpportunity(
                        definition.rule_id,
                        craft.printed_name,
                        craft.quantity,
                        tuple(targets),
                        definition.source_book,
                        definition.source_page,
                        definition.all_or_none,
                    ))
        return tuple(opportunities)

    def resolve_profile(self, profile_id: int) -> tuple[PlatformDetail, PlatformProfile] | None:
        profile = self._details.get_profile(profile_id)
        if profile is None:
            return None
        for summary in self._catalog.search(PlatformFilter(limit=1000)):
            detail = self._details.get(summary.ship_id)
            if detail and any(p.profile_id == profile_id for p in detail.profiles):
                return detail, profile
        return None
