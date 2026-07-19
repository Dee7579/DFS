"""Fleet-rule domain contracts and source metadata.

Rules are first-class, inspectable objects.  The user interface consumes rule
results; it never contains construction logic.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Mapping, Protocol, Sequence

from dfs.domain.catalog import PlatformProfile
from dfs.domain.fleet.models import Fleet, FleetEntry, ValidationSeverity


class RuleCategory(str, Enum):
    CORE = "core"
    FLEET = "fleet"
    PLATFORM = "platform"
    REPLACEMENT = "replacement"
    ALLIANCE = "alliance"
    SCENARIO = "scenario"


@dataclass(frozen=True, slots=True)
class RuleSource:
    title: str
    section: str = ""
    page: int | None = None
    edition: str = ""

    @property
    def citation(self) -> str:
        parts = [self.title]
        if self.section:
            parts.append(self.section)
        if self.page is not None:
            parts.append(f"p. {self.page}")
        return ", ".join(parts)


@dataclass(frozen=True, slots=True)
class RuleContext:
    fleet: Fleet
    resolved_entries: Mapping[str, PlatformProfile | None]

    def profile_for(self, entry: FleetEntry) -> PlatformProfile | None:
        return self.resolved_entries.get(entry.entry_id)


@dataclass(frozen=True, slots=True)
class RuleMessage:
    rule_id: str
    severity: ValidationSeverity
    title: str
    message: str
    source: RuleSource
    entry_id: str | None = None
    platform_name: str = ""
    remedy: str = ""
    remedies: tuple[str, ...] = field(default_factory=tuple)

    @property
    def remedy_items(self) -> tuple[str, ...]:
        """Return structured remedies while preserving legacy single-text messages."""
        if self.remedies:
            return self.remedies
        if self.remedy:
            items: list[str] = []
            for index, part in enumerate(self.remedy.split("; or ")):
                text = part.strip().rstrip(".")
                if not text:
                    continue
                if index > 0:
                    text = text[:1].upper() + text[1:]
                items.append(text + ".")
            return tuple(items)
        return ()


class FleetRule(Protocol):
    rule_id: str
    name: str
    category: RuleCategory
    source: RuleSource
    description: str

    def applies(self, context: RuleContext) -> bool: ...
    def evaluate(self, context: RuleContext) -> Sequence[RuleMessage]: ...


@dataclass(frozen=True, slots=True)
class RuleDescriptor:
    rule_id: str
    name: str
    category: RuleCategory
    description: str
    source: RuleSource
    tags: tuple[str, ...] = field(default_factory=tuple)
