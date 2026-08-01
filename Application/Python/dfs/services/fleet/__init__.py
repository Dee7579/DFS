"""Public fleet-service API.

The rules and construction services are intentionally importable without the
desktop-only PDF stack.  Android uses the same rule engine and fleet model but
does not ship pypdf, ReportLab, or the print composers.  Print types retain the
same public import names through the lazy loader below, so the desktop
composition root remains source-compatible.
"""

from .b5_acta_profile import B5ACTAAdvisoryPriorityProfile, B5ACTASandboxProfile, B5ACTAStandardPriorityProfile
from .construction_service import FleetConstructionService
from .rule_engine import FleetRuleEngine, RuleDiagnostic, RuleDiagnostics
from .b5_acta_rules import build_b5_acta_core_rule_engine
from .b5_fighter_replacements import B5FighterReplacementService, B5_FIGHTER_REPLACEMENTS
from .b5_missile_loadouts import B5MissileLoadoutService, EA_MISSILE_VARIANTS

__all__ = [
    "B5ACTAStandardPriorityProfile",
    "B5ACTAAdvisoryPriorityProfile",
    "B5ACTASandboxProfile",
    "FleetConstructionService",
    "FleetPrintItem",
    "FleetPrintPlanner",
    "FleetSheetGenerator",
    "GeneratedFleetSheet",
    "FleetPrintComposer",
    "PreparedFleetDocument",
    "FleetPrintPacket",
    "FleetRosterGenerator",
    "GeneratedFleetRoster",
    "FleetRuleEngine",
    "RuleDiagnostic",
    "RuleDiagnostics",
    "build_b5_acta_core_rule_engine",
    "B5FighterReplacementService",
    "B5_FIGHTER_REPLACEMENTS",
    "B5MissileLoadoutService",
    "EA_MISSILE_VARIANTS",
]


_LAZY_EXPORTS = {
    "FleetPrintItem": (".print_planner", "FleetPrintItem"),
    "FleetPrintPlanner": (".print_planner", "FleetPrintPlanner"),
    "FleetSheetGenerator": (".sheet_generator", "FleetSheetGenerator"),
    "GeneratedFleetSheet": (".sheet_generator", "GeneratedFleetSheet"),
    "FleetPrintComposer": (".print_composer", "FleetPrintComposer"),
    "PreparedFleetDocument": (".print_composer", "PreparedFleetDocument"),
    "FleetPrintPacket": (".print_composer", "FleetPrintPacket"),
    "FleetRosterGenerator": (".roster_generator", "FleetRosterGenerator"),
    "GeneratedFleetRoster": (".roster_generator", "GeneratedFleetRoster"),
}


def __getattr__(name: str):
    target = _LAZY_EXPORTS.get(name)
    if target is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    from importlib import import_module

    module_name, attribute_name = target
    value = getattr(import_module(module_name, __name__), attribute_name)
    globals()[name] = value
    return value

from .b5_allied_contingents import ALLIED_CONTINGENTS, AlliedContingentRule
from .rule_catalog import B5RuleCatalog

from .construction_rules import (
    ConstructionRuleBase,
    EachPlatformUniqueRule,
    FAPLimitedPlatformRule,
    GroupedPurchaseRule,
    MaximumQuantityRule,
    MinimumFleetRequirementRule,
    MutualExclusionRule,
    PlatformSelector,
    PurchaseRatioRule,
    RequiredPlatformRule,
    UniquePlatformRule,
    matching_entries,
    register_rules,
    selected_quantity,
)

from .b5_fleet_rule_catalog import (
    B5_FLEET_CONSTRUCTION_RULES,
    CatalogStatus,
    FleetConstructionRuleRecord,
    rule_by_id,
    rule_records,
)
