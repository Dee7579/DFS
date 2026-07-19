from dataclasses import dataclass

import pytest

from dfs.domain.fleet import Fleet, FleetEntry, ValidationSeverity
from dfs.domain.fleet.rules import RuleCategory, RuleContext, RuleMessage, RuleSource
from dfs.services.fleet.b5_acta_rules import build_b5_acta_core_rule_engine
from dfs.services.fleet.rule_engine import FleetRuleEngine


@dataclass(frozen=True)
class DummyRule:
    rule_id: str = "TEST_RULE"
    name: str = "Test rule"
    category: RuleCategory = RuleCategory.CORE
    source: RuleSource = RuleSource("Test Source", "Test Section", 1)
    description: str = "Used to verify the rule engine."

    def applies(self, context):
        return True

    def evaluate(self, context):
        return (RuleMessage(
            self.rule_id, ValidationSeverity.WARNING, self.name,
            "Test warning.", self.source,
        ),)


def test_rule_engine_registers_and_evaluates_rules():
    engine = FleetRuleEngine((DummyRule(),))
    fleet = Fleet.create("Test", "b5_acta", "b5_acta_priority_standard")
    result = engine.validate(fleet, {})
    assert len(result.warnings) == 1
    assert "Test Source" in result.warnings[0].message


def test_duplicate_rule_ids_are_rejected():
    engine = FleetRuleEngine((DummyRule(),))
    with pytest.raises(ValueError, match="Duplicate"):
        engine.register(DummyRule())


def test_core_rule_library_has_unique_source_backed_rules():
    engine = build_b5_acta_core_rule_engine()
    assert len(engine.rules()) == 9
    diagnostics = engine.diagnostics()
    assert diagnostics.is_valid
    assert all(d.source.title for d in engine.descriptors())


def test_fleet_list_required_is_explained_by_rule_engine():
    engine = build_b5_acta_core_rule_engine()
    fleet = Fleet.create("Test", "b5_acta", "b5_acta_priority_standard")
    result = engine.validate(fleet, {})
    assert any(m.code == "CORE_FLEET_LIST_REQUIRED" for m in result.errors)
    assert any("Source:" in m.message for m in result.errors)
