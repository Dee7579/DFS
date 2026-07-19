"""Use-case service joining Fleet Builder files to Tactical Assistant files."""
from __future__ import annotations

from pathlib import Path

from dfs.domain.fleet import Fleet
from dfs.domain.tactical import TacticalGameState
from dfs.infrastructure.fleet import JSONFleetStore
from dfs.infrastructure.tactical import JSONTacticalGameStore
from dfs.services.tactical.game_service import TacticalGameBuilder


class TacticalGameService:
    """Create, save, and reopen independent tactical games.

    This service reads a Fleet Builder file and snapshots it into live game
    state.  Neither persistence adapter exposes a write path to canonical
    platform data or the DFS database.
    """

    def __init__(
        self,
        builder: TacticalGameBuilder,
        *,
        fleet_store: JSONFleetStore | None = None,
        game_store: JSONTacticalGameStore | None = None,
    ) -> None:
        self._builder = builder
        self._fleet_store = fleet_store or JSONFleetStore()
        self._game_store = game_store or JSONTacticalGameStore()

    def create_from_fleet(self, fleet: Fleet, *, game_name: str | None = None) -> TacticalGameState:
        return self._builder.build(fleet, game_name=game_name)

    def create_from_fleet_file(
        self,
        fleet_path: str | Path,
        *,
        game_name: str | None = None,
    ) -> TacticalGameState:
        fleet = self._fleet_store.load(fleet_path)
        return self.create_from_fleet(fleet, game_name=game_name)

    def create_and_save(
        self,
        fleet_path: str | Path,
        game_path: str | Path,
        *,
        game_name: str | None = None,
    ) -> TacticalGameState:
        game = self.create_from_fleet_file(fleet_path, game_name=game_name)
        self._game_store.save(game, game_path)
        return game

    def save(self, game: TacticalGameState, path: str | Path) -> Path:
        return self._game_store.save(game, path)

    def load(self, path: str | Path) -> TacticalGameState:
        return self._game_store.load(path)
