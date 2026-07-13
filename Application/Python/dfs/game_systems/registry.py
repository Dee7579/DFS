"""Game-system registry for the DFS desktop application.

The registry separates application identity from game-specific data.  Babylon 5
ACTA is the first active provider; future systems can register their own data,
Codex, fleet rules and presentation resources without changing the shell.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class GameSystemDefinition:
    id: str
    display_name: str
    short_name: str
    description: str
    enabled: bool = True


class GameSystemRegistry:
    def __init__(self, systems: tuple[GameSystemDefinition, ...], default_id: str) -> None:
        if not systems:
            raise ValueError("At least one game system must be registered")
        self._systems = systems
        self._by_id = {system.id: system for system in systems}
        if default_id not in self._by_id:
            raise ValueError(f"Unknown default game system: {default_id}")
        self.default_id = default_id

    def list_systems(self) -> tuple[GameSystemDefinition, ...]:
        return self._systems

    def get(self, system_id: str) -> GameSystemDefinition:
        return self._by_id[system_id]


def build_default_registry() -> GameSystemRegistry:
    return GameSystemRegistry(
        systems=(
            GameSystemDefinition(
                id="b5_acta_2e",
                display_name="Babylon 5: A Call to Arms",
                short_name="Babylon 5 ACTA",
                description="A Call to Arms, Second Edition",
                enabled=True,
            ),
            GameSystemDefinition(
                id="victory_at_sea",
                display_name="Victory at Sea",
                short_name="Victory at Sea",
                description="Admiralty Edition — coming later",
                enabled=False,
            ),
        ),
        default_id="b5_acta_2e",
    )
