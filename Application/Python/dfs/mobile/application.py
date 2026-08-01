"""Lean composition root for the Android/tablet companion.

This boundary deliberately excludes document lookup, PDF generation, printing,
desktop settings, and desktop widgets.  It reuses the certified SQLite catalog,
fleet rule engine, save formats, Codex, and Tactical Assistant domain services.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from dfs.infrastructure.fleet.json_store import JSONFleetStore
from dfs.infrastructure.sqlite.connection import SQLiteConnectionFactory
from dfs.infrastructure.sqlite.platform_repository import SQLitePlatformRepository
from dfs.runtime_database import prepare_runtime_database
from dfs.services.codex_service import CodexService
from dfs.services.fleet.construction_service import FleetConstructionService
from dfs.services.platform_catalog_service import PlatformCatalogService
from dfs.services.platform_detail_service import PlatformDetailService
from dfs.services.tactical.game_file_service import TacticalGameService
from dfs.services.tactical.game_service import (
    CatalogTacticalProfileResolver,
    TacticalGameBuilder,
)


@dataclass(frozen=True, slots=True)
class MobileApplicationContext:
    """Services needed by the focused tablet companion."""

    catalog: PlatformCatalogService
    platform_details: PlatformDetailService
    codex: CodexService
    fleets: FleetConstructionService
    fleet_files: JSONFleetStore
    tactical_games: TacticalGameService
    runtime_database_path: Path


def build_mobile_context(database_path: str | Path) -> MobileApplicationContext:
    """Build the Android service graph without importing desktop/PDF modules."""

    runtime_database = prepare_runtime_database(Path(database_path).resolve())
    connections = SQLiteConnectionFactory(runtime_database)
    platforms = SQLitePlatformRepository(connections)
    catalog = PlatformCatalogService(platforms)
    details = PlatformDetailService(platforms)
    fleet_store = JSONFleetStore()
    tactical = TacticalGameService(
        TacticalGameBuilder(CatalogTacticalProfileResolver(catalog, details)),
        fleet_store=fleet_store,
    )
    return MobileApplicationContext(
        catalog=catalog,
        platform_details=details,
        codex=CodexService(),
        fleets=FleetConstructionService(platforms),
        fleet_files=fleet_store,
        tactical_games=tactical,
        runtime_database_path=runtime_database,
    )
