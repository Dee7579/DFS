"""Parsing and evaluation of DFS in-service date expressions.

This module is deliberately independent of SQLite and Qt so the same rules can
be reused by the Ship Viewer, Fleet Builder, Campaign Manager, import tools,
and validation.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

_DASHES = "-–—−"
_RANGE_RE = re.compile(rf"^\s*(\d{{3,4}})\s*[{re.escape(_DASHES)}]\s*(\d{{3,4}})\s*$", re.I)
_PLUS_RE = re.compile(r"^\s*(\d{3,4})\s*\+\s*$", re.I)
_YEAR_RE = re.compile(r"^\s*(\d{3,4})\s*$", re.I)
_UNTIL_RE = re.compile(r"^\s*(?:until|through|to)\s+(\d{3,4})\s*$", re.I)
_FROM_RE = re.compile(r"^\s*(?:from|since)\s+(\d{3,4})\s*$", re.I)
_ONLY_RE = re.compile(r"^\s*(\d{3,4})\s+only\s*$", re.I)


@dataclass(frozen=True, slots=True)
class ServiceRange:
    """Normalized interpretation of an official in-service label."""

    start: int | None
    end: int | None
    always: bool = False
    recognized: bool = True
    display_text: str = ""

    def includes(self, year: int) -> bool:
        if self.always:
            return True
        if not self.recognized:
            return False
        if self.start is not None and year < self.start:
            return False
        if self.end is not None and year > self.end:
            return False
        return True


def parse_in_service(value: object) -> ServiceRange:
    """Parse all official date forms currently used by the DFS database.

    Supported examples include ``All``, ``2246+``, ``2219-2242``,
    ``Until 2261``, ``From 2259``, ``2261 only``, and a single exact year.
    Unicode dash variants are accepted. Unknown values remain unrecognized
    instead of raising an exception.
    """

    text = "" if value is None else str(value).strip()
    if not text:
        return ServiceRange(None, None, recognized=False, display_text=text)

    if text.casefold() == "all":
        return ServiceRange(None, None, always=True, display_text=text)

    for pattern, resolver in (
        (_PLUS_RE, lambda m: (int(m.group(1)), None)),
        (_UNTIL_RE, lambda m: (None, int(m.group(1)))),
        (_FROM_RE, lambda m: (int(m.group(1)), None)),
        (_ONLY_RE, lambda m: (int(m.group(1)), int(m.group(1)))),
    ):
        match = pattern.match(text)
        if match:
            start, end = resolver(match)
            return ServiceRange(start, end, display_text=text)

    match = _RANGE_RE.match(text)
    if match:
        first, second = int(match.group(1)), int(match.group(2))
        return ServiceRange(min(first, second), max(first, second), display_text=text)

    match = _YEAR_RE.match(text)
    if match:
        year = int(match.group(1))
        return ServiceRange(year, year, display_text=text)

    return ServiceRange(None, None, recognized=False, display_text=text)


def is_available_in_year(value: object, year: object) -> bool:
    """Return whether *value* includes *year* without ever raising."""

    try:
        resolved_year = int(year)
    except (TypeError, ValueError):
        return False
    return parse_in_service(value).includes(resolved_year)
