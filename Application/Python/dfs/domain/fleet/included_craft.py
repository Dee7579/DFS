"""Parsing helpers for platform craft complements.

This module intentionally does not decide replacement legality. It extracts the
printed included craft so Fleet Builder and future Tactical Assistant can present child
units without charging fleet-construction cost.
"""
from __future__ import annotations

from dataclasses import dataclass
import re


@dataclass(frozen=True, slots=True)
class IncludedCraft:
    quantity: int
    printed_name: str


_CRAFT_PATTERN = re.compile(
    r"(?P<quantity>\d+)\s+(?P<name>.+?)(?=(?:\s*,\s*|\s+and\s+)\d+\s+|$)",
    re.IGNORECASE,
)


def parse_included_craft(value: str | None) -> tuple[IncludedCraft, ...]:
    """Return included craft groups from a profile's printed Craft field."""
    text = (value or "").strip()
    if not text or text.lower() in {"none", "-", "—"}:
        return ()
    matches = tuple(
        IncludedCraft(int(match.group("quantity")), match.group("name").strip(" ,;"))
        for match in _CRAFT_PATTERN.finditer(text)
    )
    return matches


def normalize_craft_name(value: str) -> str:
    """Normalize printed craft text for conservative platform-name matching."""
    text = value.casefold().replace("’", "'")
    text = re.sub(r"[^a-z0-9']+", " ", text)
    words = []
    for word in text.split():
        if word in {"flight", "flights", "wing", "wings"}:
            continue
        if word == "fighters":
            word = "fighter"
        words.append(word)
    return " ".join(words)
