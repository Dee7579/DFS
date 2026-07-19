"""Drakh Huge Hangars option helpers.

Embarked ships are stored as individual profile IDs under their parent fleet
entry.  They are real ship instances for printing and later tactical/campaign
use, but do not spend Fleet Allocation Points.
"""
from __future__ import annotations

import re
from typing import Any, Mapping

OPTION_KEY = "huge_hangars"


def capacity_from_traits(traits) -> int:
    for trait in traits or ():
        match = re.match(r"^Huge Hangars\s+(\d+)$", str(trait).strip(), re.I)
        if match:
            return int(match.group(1))
    return 0


def embarked_profile_ids(options: Mapping[str, Any] | None) -> tuple[int, ...]:
    raw = dict(options or {}).get(OPTION_KEY, ())
    if isinstance(raw, Mapping):
        raw = raw.get("profile_ids", ())
    result: list[int] = []
    for value in raw or ():
        try:
            profile_id = int(value)
        except (TypeError, ValueError):
            continue
        if profile_id > 0:
            result.append(profile_id)
    return tuple(result)


def with_embarked_profile_ids(options: Mapping[str, Any], profile_ids) -> dict[str, Any]:
    updated = dict(options)
    clean = [int(value) for value in profile_ids if int(value) > 0]
    if clean:
        updated[OPTION_KEY] = {"profile_ids": clean}
    else:
        updated.pop(OPTION_KEY, None)
    return updated
