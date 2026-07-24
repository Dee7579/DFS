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

    def all_for_weapon(self, weapon_name: str, traits: str) -> tuple[CodexEntry, ...]:
        """Return the weapon rule and every recognized printed weapon trait."""

        entries: list[CodexEntry] = []
        seen: set[str] = set()
        for candidate in (weapon_name, *split_weapon_traits(traits)):
            entry = self.get(candidate)
            if entry is None:
                continue
            identity = entry.title.casefold()
            if identity in seen:
                continue
            seen.add(identity)
            entries.append(entry)
        return tuple(entries)

    def first_for_weapon(self, weapon_name: str, traits: str) -> CodexEntry | None:
        entries = self.all_for_weapon(weapon_name, traits)
        return entries[0] if entries else None

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
