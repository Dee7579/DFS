"""Auditable Babylon 5 ACTA fleet-construction rule inventory.

Sprint 002D.2 catalogues published construction restrictions before activation.
Entries are deliberately declarative and contain no UI logic.  ``implemented``
means the current rule engine already enforces the rule; ``catalogued`` means a
later activation sprint must bind the entry to database platform selectors.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from dfs.domain.fleet.rules import RuleCategory, RuleSource


class CatalogStatus(str, Enum):
    IMPLEMENTED = "implemented"
    CATALOGUED = "catalogued"
    REVIEW = "review"


@dataclass(frozen=True, slots=True)
class FleetConstructionRuleRecord:
    rule_id: str
    fleet: str
    name: str
    rule_family: str
    category: RuleCategory
    source: RuleSource
    summary: str
    remedy_hint: str
    status: CatalogStatus = CatalogStatus.CATALOGUED
    notes: str = ""


FLEET_LISTS = "A Call to Arms: Second Edition Fleet Lists"
PNP = "Powers & Principalities"


B5_FLEET_CONSTRUCTION_RULES: tuple[FleetConstructionRuleRecord, ...] = (
    FleetConstructionRuleRecord(
        "B5-LEAGUE-ALL-001", "Allied League of Non-Aligned Worlds",
        "Permitted component fleet lists", "allowed_fleet_lists", RuleCategory.ALLIANCE,
        RuleSource(FLEET_LISTS, "Combined Fleets of the Non-Aligned Worlds", 6, "Second Edition"),
        "An Allied League fleet may draw ships only from the listed League, Raiders, and selected Other Ships lists.",
        "Remove ships from an unlisted fleet list.",
    ),
    FleetConstructionRuleRecord(
        "B5-LEAGUE-FTR-002", "Allied League of Non-Aligned Worlds",
        "No cross-fleet carrier loading", "carrier_craft_affinity", RuleCategory.REPLACEMENT,
        RuleSource(FLEET_LISTS, "Combined Fleets of the Non-Aligned Worlds", 6, "Second Edition"),
        "Fighters from one component fleet list may not be placed in a carrier from another component fleet list.",
        "Return the craft to a carrier from its own fleet list or restore the carrier's standard craft.",
    ),
    FleetConstructionRuleRecord(
        "B5-LEAGUE-FTR-003", "Allied League of Non-Aligned Worlds",
        "Ship prerequisite for purchased fighters", "required_platform", RuleCategory.REPLACEMENT,
        RuleSource(FLEET_LISTS, "Combined Fleets of the Non-Aligned Worlds", 6, "Second Edition"),
        "Separately purchased fighters require at least one ship from the same component fleet list.",
        "Add a ship from the fighter's fleet list or remove the purchased fighter wing.",
    ),
    FleetConstructionRuleRecord(
        "B5-LEAGUE-DATE-004", "Allied League of Non-Aligned Worlds",
        "Combined League date limit", "fleet_year_limit", RuleCategory.FLEET,
        RuleSource(PNP, "Combined League Fleets and Army of Light", 11),
        "Combined League fleets may include only ships whose In Service Date extends no later than 2259.",
        "Choose ships valid for 2259 or earlier, or use an Army of Light fleet for a later battle.",
    ),
    FleetConstructionRuleRecord(
        "B5-AOL-LIST-001", "Army of Light", "Permitted fleet lists", "allowed_fleet_lists", RuleCategory.ALLIANCE,
        RuleSource(PNP, "Army of Light", 11),
        "Army of Light fleets may draw only from the published list of member fleet lists.",
        "Remove ships from an unlisted fleet list.",
    ),
    FleetConstructionRuleRecord(
        "B5-AOL-PLAT-002", "Army of Light", "Permitted platforms", "allowed_platforms", RuleCategory.PLATFORM,
        RuleSource(PNP, "Army of Light", 11),
        "Only the specifically listed ships, fighters, and variants may be selected.",
        "Replace the platform with one named in the Army of Light roster.",
    ),
    FleetConstructionRuleRecord(
        "B5-AOL-MIX-003", "Army of Light", "Minimum two component fleets", "minimum_distinct_fleets", RuleCategory.FLEET,
        RuleSource(PNP, "Army of Light", 11),
        "An Army of Light must include ships from at least two different fleet lists.",
        "Add a qualifying ship from a second permitted fleet list.",
    ),
    FleetConstructionRuleRecord(
        "B5-ISA-ALL-001", "Interstellar Alliance", "Allied contingent", "allied_contingent", RuleCategory.ALLIANCE,
        RuleSource(FLEET_LISTS, "ISA Fleet Special Rules - Allied Fleets", 82, "Second Edition"),
        "Up to one scenario-level FAP may be spent on one permitted allied fleet list.",
        "Reduce allied expenditure, or remove ships from additional allied fleet lists.",
        CatalogStatus.IMPLEMENTED,
    ),
    FleetConstructionRuleRecord(
        "B5-ISA-DATE-002", "Interstellar Alliance", "Fleet unavailable before 2262", "fleet_year_minimum", RuleCategory.FLEET,
        RuleSource(FLEET_LISTS, "ISA Fleet Special Rules - In Service Dates", 82, "Second Edition"),
        "The ISA fleet list may not be used in scenarios set before 2262.",
        "Set the scenario year to 2262 or later, or choose another fleet list.",
        CatalogStatus.IMPLEMENTED,
    ),
    FleetConstructionRuleRecord(
        "B5-RAID-ALL-001", "Raiders", "Allied contingent", "allied_contingent", RuleCategory.ALLIANCE,
        RuleSource(FLEET_LISTS, "Raiders Fleet Special Rules - Allied Fleets", 127, "Second Edition"),
        "Up to one scenario-level FAP may be spent on one permitted League allied fleet list.",
        "Reduce allied expenditure, or remove ships from additional allied fleet lists.",
        CatalogStatus.IMPLEMENTED,
    ),
    FleetConstructionRuleRecord(
        "B5-PSI-ALL-001", "Psi Corps", "EarthForce requisition", "allied_contingent", RuleCategory.ALLIANCE,
        RuleSource(FLEET_LISTS, "Psi Corps Fleet Special Rules - EarthForce Requisition", 149, "Second Edition"),
        "Up to two scenario-level FAP may be spent on ships from one Earth Alliance fleet list.",
        "Reduce Earth Alliance expenditure to the permitted allowance.",
        CatalogStatus.IMPLEMENTED,
    ),
    FleetConstructionRuleRecord(
        "B5-GAIM-QUEEN-001", "Gaim Intelligence", "At least one Queen", "minimum_fleet_requirement", RuleCategory.FLEET,
        RuleSource(PNP, "Revised Gaim Intelligence Fleet Special Rules - The Queens", 19),
        "Every revised Gaim fleet must contain at least one Queen ship.",
        "Add any Queen ship or remove all non-Queen choices and rebuild the fleet.",
        CatalogStatus.IMPLEMENTED,
    ),
    FleetConstructionRuleRecord(
        "B5-GAIM-QUEEN-002", "Gaim Intelligence", "One highest-priority Ruling Queen", "maximum_quantity_dynamic", RuleCategory.FLEET,
        RuleSource(PNP, "Revised Gaim Intelligence Fleet Special Rules - The Queens", 19),
        "Only one Queen of the highest Priority Level represented in the fleet may be present; lower-priority Queens are unrestricted.",
        "Remove duplicate Queens at the fleet's highest represented Queen priority.",
        CatalogStatus.IMPLEMENTED,
    ),
    FleetConstructionRuleRecord(
        "B5-ANCIENT-UNQ-001", "The Ancients", "Each Ancient is unique", "unique_platform", RuleCategory.PLATFORM,
        RuleSource(FLEET_LISTS, "Using the Ancients", 139, "Second Edition"),
        "Only one example of each Ancient platform may be selected.",
        "Reduce the fleet to one copy of each Ancient platform.",
        CatalogStatus.IMPLEMENTED,
    ),
    FleetConstructionRuleRecord(
        "B5-ANCIENT-DATE-002", "The Ancients", "Ancients depart in 2261", "fleet_year_maximum", RuleCategory.FLEET,
        RuleSource(FLEET_LISTS, "Using the Ancients", 139, "Second Edition"),
        "The five Ancient vessels disappear during the early part of 2261.",
        "Use the fleet only in a suitably dated special scenario.",
        CatalogStatus.REVIEW,
        "The text is narrative rather than a precise month boundary; activation should present an advisory unless scenario metadata is expanded.",
    ),
    FleetConstructionRuleRecord(
        "B5-DRAKH-HGR-001", "The Drakh", "Huge Hangar carried-ship capacity", "hangar_capacity", RuleCategory.REPLACEMENT,
        RuleSource(FLEET_LISTS, "Drakh Fleet Special Rules - Huge Hangars", 143, "Second Edition"),
        "Light Raiders, Heavy Raiders, and Scouts consume Huge Hangar slots; larger Amu-carried ships consume two or eight slots as printed.",
        "Reduce carried craft or replace them with craft that fit the remaining Huge Hangar capacity.",
    ),
)


def rule_records(*, status: CatalogStatus | None = None, fleet: str | None = None):
    records = B5_FLEET_CONSTRUCTION_RULES
    if status is not None:
        records = tuple(record for record in records if record.status is status)
    if fleet is not None:
        folded = fleet.casefold()
        records = tuple(record for record in records if record.fleet.casefold() == folded)
    return records


def rule_by_id(rule_id: str) -> FleetConstructionRuleRecord:
    for record in B5_FLEET_CONSTRUCTION_RULES:
        if record.rule_id == rule_id:
            return record
    raise KeyError(rule_id)
