"""Composition root and application context for DFS desktop."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from dfs.app_paths import find_output_path
from dfs.framework import (
    CommandService,
    LoggingService,
    NotificationService,
    ResourceService,
    SettingsService,
    StatusService,
    ThemeService,
)
from dfs.game_systems.registry import GameSystemRegistry, build_default_registry
from dfs.infrastructure.sqlite.connection import SQLiteConnectionFactory
from dfs.infrastructure.sqlite.platform_repository import SQLitePlatformRepository
from dfs.services.fleet.b5_composite_fleets import ensure_b5_composite_fleets
from dfs.infrastructure.fleet import JSONFleetStore
from dfs.services.codex_service import CodexService
from dfs.services.document_service import DocumentService, DocumentStyle
from dfs.services.platform_catalog_service import PlatformCatalogService
from dfs.services.platform_detail_service import PlatformDetailService
from dfs.services.fleet import (
    FleetConstructionService, FleetPrintPlanner, FleetSheetGenerator, FleetPrintComposer,
    FleetRosterGenerator, B5FighterReplacementService, B5MissileLoadoutService,
)


@dataclass(frozen=True, slots=True)
class ApplicationContext:
    """The dependency boundary supplied to DFS desktop modules."""
    catalog: PlatformCatalogService
    platform_details: PlatformDetailService
    documents: DocumentService
    game_systems: GameSystemRegistry
    codex: CodexService
    settings: SettingsService
    theme: ThemeService
    status: StatusService
    notifications: NotificationService
    logging: LoggingService
    commands: CommandService
    resources: ResourceService
    fleets: FleetConstructionService
    fleet_files: JSONFleetStore
    fleet_prints: FleetPrintPlanner
    fleet_sheets: FleetSheetGenerator
    fleet_composer: FleetPrintComposer
    fleet_rosters: FleetRosterGenerator
    fighter_replacements: B5FighterReplacementService
    missile_loadouts: B5MissileLoadoutService


# Compatibility name used by existing UI modules while they migrate gradually.
ApplicationServices = ApplicationContext


def build_application_context(
    database_path: str | Path,
    settings: SettingsService | None = None,
) -> ApplicationContext:
    database_path = Path(database_path).resolve()
    ensure_b5_composite_fleets(database_path)
    project_root = Path(__file__).resolve().parents[1]
    settings_service = settings or SettingsService()
    connections = SQLiteConnectionFactory(database_path)
    platforms = SQLitePlatformRepository(connections)
    documents = DocumentService(
        styles=(DocumentStyle("dfs_standard", "DFS Standard", find_output_path(__file__)),)
    )
    logging_service = LoggingService(project_root / "logs" / "dfs.log")
    return ApplicationContext(
        catalog=PlatformCatalogService(platforms),
        platform_details=PlatformDetailService(platforms),
        documents=documents,
        game_systems=build_default_registry(),
        codex=CodexService(),
        settings=settings_service,
        theme=ThemeService(settings_service),
        status=StatusService(),
        notifications=NotificationService(),
        logging=logging_service,
        commands=CommandService(),
        resources=ResourceService(project_root),
        fleets=FleetConstructionService(platforms),
        fleet_files=JSONFleetStore(),
        fleet_prints=FleetPrintPlanner(PlatformCatalogService(platforms), PlatformDetailService(platforms)),
        fleet_sheets=FleetSheetGenerator(PlatformDetailService(platforms), documents),
        fleet_composer=FleetPrintComposer(),
        fighter_replacements=B5FighterReplacementService(PlatformCatalogService(platforms), PlatformDetailService(platforms)),
        missile_loadouts=B5MissileLoadoutService(),
        fleet_rosters=FleetRosterGenerator(
            PlatformCatalogService(platforms),
            PlatformDetailService(platforms),
            FleetConstructionService(platforms),
        ),
    )


def build_application_services(database_path: str | Path) -> ApplicationContext:
    """Compatibility composition function retained for external callers."""
    return build_application_context(database_path)
