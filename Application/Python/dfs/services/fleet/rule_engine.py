"""Reusable fleet-rule registry, evaluator, browser, and diagnostics."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping, Sequence

from dfs.domain.catalog import PlatformProfile
from dfs.domain.fleet.models import Fleet, ValidationMessage, ValidationResult
from dfs.domain.fleet.rules import FleetRule, RuleContext, RuleDescriptor, RuleMessage


@dataclass(frozen=True, slots=True)
class RuleDiagnostic:
    severity: str
    code: str
    message: str
    rule_id: str = ""


@dataclass(frozen=True, slots=True)
class RuleDiagnostics:
    rule_count: int
    diagnostics: tuple[RuleDiagnostic, ...]

    @property
    def is_valid(self) -> bool:
        return not any(d.severity == "error" for d in self.diagnostics)


class FleetRuleEngine:
    def __init__(self, rules: Iterable[FleetRule] = ()):
        self._rules: dict[str, FleetRule] = {}
        for rule in rules:
            self.register(rule)

    def register(self, rule: FleetRule) -> None:
        if not rule.rule_id or rule.rule_id.strip() != rule.rule_id:
            raise ValueError("Rule IDs must be non-empty and trimmed")
        if rule.rule_id in self._rules:
            raise ValueError(f"Duplicate fleet rule ID: {rule.rule_id}")
        self._rules[rule.rule_id] = rule

    def extend(self, rules: Iterable[FleetRule]) -> "FleetRuleEngine":
        """Register several rules and return this engine for composition."""
        for rule in rules:
            self.register(rule)
        return self

    def rules(self) -> tuple[FleetRule, ...]:
        return tuple(self._rules.values())

    def descriptors(self) -> tuple[RuleDescriptor, ...]:
        return tuple(
            RuleDescriptor(
                rule_id=r.rule_id,
                name=r.name,
                category=r.category,
                description=r.description,
                source=r.source,
            )
            for r in self._rules.values()
        )

    def evaluate(
        self,
        fleet: Fleet,
        resolved_entries: Mapping[str, PlatformProfile | None],
    ) -> tuple[RuleMessage, ...]:
        context = RuleContext(fleet=fleet, resolved_entries=resolved_entries)
        messages: list[RuleMessage] = []
        for rule in self._rules.values():
            if rule.applies(context):
                messages.extend(rule.evaluate(context))
        return tuple(messages)

    def validate(
        self,
        fleet: Fleet,
        resolved_entries: Mapping[str, PlatformProfile | None],
    ) -> ValidationResult:
        messages = self.evaluate(fleet, resolved_entries)
        return ValidationResult(tuple(
            ValidationMessage(
                code=m.rule_id,
                severity=m.severity,
                message=self.format_message(m),
                entry_id=m.entry_id,
            )
            for m in messages
        ))

    @staticmethod
    def format_message(message: RuleMessage) -> str:
        text = f"{message.title}: {message.message}"
        if message.remedy:
            text += f" Remedy: {message.remedy}"
        if message.source.title:
            text += f" Source: {message.source.citation}."
        return text

    def diagnostics(self) -> RuleDiagnostics:
        diagnostics: list[RuleDiagnostic] = []
        for rule in self._rules.values():
            if not rule.name.strip():
                diagnostics.append(RuleDiagnostic("error", "missing_name", "Rule has no name.", rule.rule_id))
            if not rule.description.strip():
                diagnostics.append(RuleDiagnostic("warning", "missing_description", "Rule has no description.", rule.rule_id))
            if not rule.source.title.strip():
                diagnostics.append(RuleDiagnostic("error", "missing_source", "Rule has no source title.", rule.rule_id))
        return RuleDiagnostics(len(self._rules), tuple(diagnostics))
