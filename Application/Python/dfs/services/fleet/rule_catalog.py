"""Read-only ACTA rule implementation coverage catalog."""
from __future__ import annotations
import json
from dataclasses import dataclass
from pathlib import Path

@dataclass(frozen=True, slots=True)
class RuleCoverage:
    category: str
    status: str
    total: int

class B5RuleCatalog:
    def __init__(self, path: Path | None = None):
        self.path = path or Path(__file__).resolve().parents[2] / "rules" / "b5_acta" / "rule_catalog.json"
        self.data = json.loads(self.path.read_text(encoding="utf-8"))

    def rules(self) -> tuple[dict, ...]:
        return tuple(self.data.get("rules", ()))

    def coverage(self) -> tuple[RuleCoverage, ...]:
        counts: dict[tuple[str, str], int] = {}
        for rule in self.rules():
            key = (rule["category"], rule["status"])
            counts[key] = counts.get(key, 0) + 1
        return tuple(RuleCoverage(category, status, total) for (category, status), total in sorted(counts.items()))
