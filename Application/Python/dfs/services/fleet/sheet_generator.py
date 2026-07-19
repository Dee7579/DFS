"""Fleet-specific PDF generation without modifying master reference sheets."""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from dfs.pdf import ACTAAncientGenerator, ACTAClassicGenerator, ACTAFighterGenerator
from dfs.ship import Ship, Weapon
from dfs.services.fleet.print_planner import FleetPrintItem
from dfs.domain.fleet.ordnance import missile_loadout_map
from dfs.services.fleet.b5_missile_loadouts import B5MissileLoadoutService


def _safe_name(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "_", str(value).strip()).strip("._")
    return cleaned or "sheet"


@dataclass(frozen=True, slots=True)
class GeneratedFleetSheet:
    item_key: str
    path: Path
    generated: bool


class FleetSheetGenerator:
    """Generate named fleet copies while leaving output/ master PDFs untouched."""

    def __init__(self, platform_details, documents) -> None:
        self._details = platform_details
        self._documents = documents

    def _ship_for(self, item: FleetPrintItem) -> Ship:
        detail = self._details.get(item.ship_id)
        profile = self._details.get_profile(item.profile_id)
        if detail is None or profile is None:
            raise LookupError(f"Platform profile {item.profile_id} is unavailable.")
        configured_weapons = []
        selected_missiles = missile_loadout_map(item.options)
        missile_notes: list[str] = []
        for weapon_index, weapon in enumerate(profile.weapons):
            variant_id = selected_missiles.get(f"weapon:{weapon_index}", "standard")
            variant = B5MissileLoadoutService.variant(variant_id)
            if variant is not None and "missile rack" in weapon.name.casefold():
                traits = variant.traits
                if "slow-loading" in weapon.traits.casefold() and "slow-loading" not in traits.casefold():
                    traits = (traits + ", Slow-Loading").strip(", ")
                configured_weapons.append(Weapon(
                    name=f"{weapon.name} ({B5MissileLoadoutService.short_label(variant_id)})",
                    range=variant.range_value,
                    arc=weapon.arc,
                    attack_dice=weapon.attack_dice,
                    traits=traits,
                ))
                if variant.special_rule:
                    missile_notes.append(f"{weapon.name} ({B5MissileLoadoutService.short_label(variant_id)}): {variant.special_rule}")
            else:
                configured_weapons.append(Weapon(
                    name=weapon.name,
                    range=weapon.range_value,
                    arc=weapon.arc,
                    attack_dice=weapon.attack_dice,
                    traits=weapon.traits,
                ))

        ship = Ship(
            name=detail.name,
            ship_class=detail.ship_class,
            faction=detail.faction_name,
            fleet=profile.fleet_name,
            priority=profile.priority_level,
            speed=profile.speed,
            turn=profile.turn,
            hull=profile.hull,
            damage=profile.damage,
            crew=profile.crew,
            troops=profile.troops,
            craft=profile.craft,
            initiative=profile.initiative,
            in_service=profile.in_service,
            crew_quality=profile.crew_quality,
            traits=list(profile.traits),
            weapons=configured_weapons,
            notes=[*profile.notes, *missile_notes],
        )
        ship.file_name = detail.file_name
        return ship

    def generate(
        self,
        item: FleetPrintItem,
        *,
        style_id: str,
        output_folder: Path,
    ) -> GeneratedFleetSheet:
        if item.kind != "ship":
            reference = self._documents.find_sheet(
                style_id=style_id, file_name=item.file_name,
                platform_name=item.platform_name, faction_name=item.faction_name,
                fleet_name=item.fleet_name,
            )
            if reference is None:
                raise FileNotFoundError(item.display_name)
            return GeneratedFleetSheet(item.item_key, reference.path, False)
        if style_id != "dfs_standard":
            raise ValueError("Fleet-specific generation currently supports DFS Standard only.")

        output_folder.mkdir(parents=True, exist_ok=True)
        vessel_token = item.vessel_name or "Unnamed"
        filename = f"{_safe_name(vessel_token)}__{_safe_name(item.platform_name)}__{_safe_name(item.item_key)}.pdf"
        path = output_folder / filename
        ship = self._ship_for(item)
        if "Fighter" in ship.traits or "Breaching Pod" in ship.traits:
            generator = ACTAFighterGenerator(path)
            generator.generate_ship_sheet(ship)
        elif ship.faction == "The Ancients":
            generator = ACTAAncientGenerator(path)
            generator.generate_ship_sheet(ship, vessel_name=item.vessel_name)
        else:
            generator = ACTAClassicGenerator(path)
            generator.generate_ship_sheet(ship, vessel_name=item.vessel_name)
        return GeneratedFleetSheet(item.item_key, path, True)
