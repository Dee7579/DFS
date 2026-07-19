"""Earth Alliance missile-variant rules from the B5 ACTA Fleet Lists."""
from __future__ import annotations

from dfs.domain.catalog import PlatformProfile
from dfs.domain.fleet.ordnance import MissileRackOpportunity, MissileVariant

FLEET_LISTS = "B5 ACTA Fleet Lists"

EA_MISSILE_VARIANTS: tuple[MissileVariant, ...] = (
    MissileVariant("standard", "Standard Anti-Ship Missile", "30", "Precise, Super AP", 2165),
    MissileVariant("flash", "Flash Missile", "20", "AP, Double Damage, Precise", 2229),
    MissileVariant("heavy", "Heavy Missile", "12", "Triple Damage, Super AP", 2225),
    MissileVariant(
        "anti_fighter", "Anti-Fighter Missile", "15", "", 2237,
        "A successful attack destroys one fighter flight with no Dodge roll allowed.",
    ),
    MissileVariant("long_range", "Long-Range Missile", "40", "AP, Precise", 2225),
    MissileVariant(
        "harm", "HARM Missile", "15", "Super AP", 2248,
        "A hit causes no damage. The target must pass a Crew Quality 10 check or count every target it attacks as Stealth 3+ until the end of the next turn; multiple HARM effects are not cumulative.",
    ),
)


class B5MissileLoadoutService:
    """Resolve configurable missile racks and legal year-gated variants."""

    _EXCLUDED_PLATFORM_TOKENS = ("hermes", "tethys-class missile boat")

    @classmethod
    def opportunities(
        cls,
        platform_name: str,
        profile: PlatformProfile,
        selected_year: int | None,
    ) -> tuple[MissileRackOpportunity, ...]:
        if not profile.fleet_name.startswith("Earth Alliance"):
            return ()
        if any(trait.casefold().startswith("fighter") for trait in profile.traits):
            return ()
        normalized_name = platform_name.casefold()
        if any(token in normalized_name for token in cls._EXCLUDED_PLATFORM_TOKENS):
            return ()

        legal_variants = tuple(
            variant for variant in EA_MISSILE_VARIANTS
            if selected_year is None or selected_year >= variant.minimum_year
        )
        opportunities: list[MissileRackOpportunity] = []
        rack_number = 0
        for weapon_index, weapon in enumerate(profile.weapons):
            normalized_weapon = weapon.name.casefold()
            if "missile rack" not in normalized_weapon:
                continue
            rack_number += 1
            rack_key = f"weapon:{weapon_index}"
            opportunities.append(MissileRackOpportunity(
                rack_key=rack_key,
                label=f"{weapon.name} {rack_number} - {weapon.arc} arc, {weapon.attack_dice} AD",
                weapon_index=weapon_index,
                arc=weapon.arc,
                attack_dice=weapon.attack_dice,
                standard_range=weapon.range_value,
                standard_traits=weapon.traits,
                variants=legal_variants,
                source_book=FLEET_LISTS,
                source_page=15,
            ))
        return tuple(opportunities)


    @staticmethod
    def short_label(variant_id: str) -> str:
        return {
            "standard": "Standard",
            "flash": "Flash",
            "heavy": "Heavy",
            "anti_fighter": "Anti-Fighter",
            "long_range": "Long-Range",
            "harm": "HARM",
        }.get(variant_id, variant_id.replace("_", " ").title())

    @staticmethod
    def variant(variant_id: str) -> MissileVariant | None:
        return next((variant for variant in EA_MISSILE_VARIANTS if variant.variant_id == variant_id), None)
