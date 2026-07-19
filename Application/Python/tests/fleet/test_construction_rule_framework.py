from dataclasses import replace

import pytest

from dfs.domain.catalog import PlatformProfile
from dfs.domain.fleet import Fleet, FleetEntry
from dfs.domain.fleet.rules import RuleSource
from dfs.services.fleet.construction_rules import (
    FAPLimitedPlatformRule, GroupedPurchaseRule, MaximumQuantityRule,
    MinimumFleetRequirementRule, MutualExclusionRule, PlatformSelector,
    PurchaseRatioRule, RequiredPlatformRule, UniquePlatformRule,
)
from dfs.services.fleet.rule_engine import FleetRuleEngine

SOURCE = RuleSource("Test Fleet Book", "Fleet Restrictions", 42)


def profile(pid, *, fleet=1, priority="Raid", traits=()):
    return PlatformProfile(pid, fleet, "Test Fleet", "+0", priority, "8", "1/45", "5", "10/3", "10/3", "0", "", "2250+", "Test", traits=traits)


def fleet_with(*items, fap=1):
    fleet = Fleet.create("Test", "b5_acta", "b5_acta_priority_standard", fleet_list_id=1)
    entries=[]; resolved={}
    for pid, qty in items:
        entry=FleetEntry.create(pid, qty)
        entries.append(entry); resolved[entry.entry_id]=profile(pid)
    return replace(fleet, entries=tuple(entries), metadata={"fleet_allocation_points": fap}), resolved


def validate(rule, fleet, resolved):
    return FleetRuleEngine((rule,)).validate(fleet, resolved)


def base_kwargs(rule_id):
    return dict(rule_id=rule_id, name=rule_id, source=SOURCE, description="Test rule")


def test_selector_uses_and_semantics_and_case_insensitive_traits():
    selector=PlatformSelector(fleet_list_ids=frozenset({1}), priority_levels=frozenset({"Raid"}), traits=frozenset({"Scout"}))
    assert selector.matches(profile(1, traits=("SCOUT",)))
    assert not selector.matches(profile(1, fleet=2, traits=("Scout",)))


def test_unique_and_maximum_quantity_rules():
    fleet,resolved=fleet_with((1,2),(2,2))
    unique=UniquePlatformRule(**base_kwargs("UNIQUE"), selector=PlatformSelector.profiles(1))
    maximum=MaximumQuantityRule(**base_kwargs("MAX"), selector=PlatformSelector.profiles(1,2), maximum=3)
    assert validate(unique,fleet,resolved).errors
    assert validate(maximum,fleet,resolved).errors


def test_required_and_mutual_exclusion_rules():
    fleet,resolved=fleet_with((1,1),(3,1))
    required=RequiredPlatformRule(**base_kwargs("REQ"), trigger=PlatformSelector.profiles(1), required=PlatformSelector.profiles(2))
    exclusion=MutualExclusionRule(**base_kwargs("EX"), first=PlatformSelector.profiles(1), second=PlatformSelector.profiles(3))
    assert validate(required,fleet,resolved).errors
    assert validate(exclusion,fleet,resolved).errors


def test_ratio_and_minimum_rules():
    fleet,resolved=fleet_with((1,2),(2,3))
    ratio=PurchaseRatioRule(**base_kwargs("RATIO"), limited=PlatformSelector.profiles(1), basis=PlatformSelector.profiles(2), allowed_per_basis=1, basis_block_size=2)
    minimum=MinimumFleetRequirementRule(**base_kwargs("MIN"), selector=PlatformSelector.profiles(3), minimum=1)
    assert validate(ratio,fleet,resolved).errors
    assert validate(minimum,fleet,resolved).errors


def test_fap_limited_and_grouped_purchase_rules():
    fleet,resolved=fleet_with((1,3), fap=1)
    fap_rule=FAPLimitedPlatformRule(**base_kwargs("FAP"), selector=PlatformSelector.profiles(1), allowed_per_fap=2)
    grouped=GroupedPurchaseRule(**base_kwargs("GROUP"), selector=PlatformSelector.profiles(1), group_size=2)
    assert validate(fap_rule,fleet,resolved).errors
    assert validate(grouped,fleet,resolved).errors


def test_valid_declarative_rules_are_silent():
    fleet,resolved=fleet_with((1,1),(2,2), fap=2)
    rules=(
        UniquePlatformRule(**base_kwargs("U"), selector=PlatformSelector.profiles(1)),
        RequiredPlatformRule(**base_kwargs("R"), trigger=PlatformSelector.profiles(1), required=PlatformSelector.profiles(2)),
        PurchaseRatioRule(**base_kwargs("P"), limited=PlatformSelector.profiles(1), basis=PlatformSelector.profiles(2), basis_block_size=2),
        GroupedPurchaseRule(**base_kwargs("G"), selector=PlatformSelector.profiles(2), group_size=2),
    )
    assert FleetRuleEngine(rules).validate(fleet,resolved).is_valid


def test_invalid_rule_configuration_is_rejected():
    with pytest.raises(ValueError):
        MaximumQuantityRule(**base_kwargs("BAD"), maximum=-1)
