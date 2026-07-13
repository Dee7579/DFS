"""Read-only access to the active game's rules Codex."""
from __future__ import annotations

from dataclasses import dataclass

from dfs.codex.b5_acta_codex import (
    get_related_rules,
    get_rule,
    normalize_rule_name,
    search_rules,
    split_weapon_traits,
)


@dataclass(frozen=True, slots=True)
class CodexEntry:
    title: str
    category: str
    text: str
    source: str
    see_also: tuple[str, ...] = ()


class CodexService:
    def get(self, name: str) -> CodexEntry | None:
        rule = get_rule(name)
        if rule is None:
            return None
        return CodexEntry(
            title=str(rule.get("title", normalize_rule_name(name))),
            category=str(rule.get("category", "Rule")),
            text=str(rule.get("text", "")),
            source=str(rule.get("source", "")),
            see_also=tuple(get_related_rules(name)),
        )

    def first_for_weapon(self, weapon_name: str, traits: str) -> CodexEntry | None:
        for candidate in (weapon_name, *split_weapon_traits(traits)):
            entry = self.get(candidate)
            if entry is not None:
                return entry
        return None

    def search(self, query: str) -> tuple[CodexEntry, ...]:
        return tuple(
            CodexEntry(
                title=str(item.get("title", "")),
                category=str(item.get("category", "Rule")),
                text=str(item.get("text", "")),
                source=str(item.get("source", "")),
                see_also=tuple(item.get("see_also", ())),
            )
            for item in search_rules(query)
        )
