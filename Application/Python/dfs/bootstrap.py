"""Composition root for the DFS desktop application."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from dfs.app_paths import find_output_path
from dfs.game_systems.registry import GameSystemRegistry, build_default_registry
from dfs.infrastructure.sqlite.connection import SQLiteConnectionFactory
from dfs.infrastructure.sqlite.platform_repository import SQLitePlatformRepository
from dfs.services.document_service import DocumentService, DocumentStyle
from dfs.services.codex_service import CodexService
from dfs.services.platform_catalog_service import PlatformCatalogService
from dfs.services.platform_detail_service import PlatformDetailService


@dataclass(frozen=True, slots=True)
class ApplicationServices:
    catalog: PlatformCatalogService
    platform_details: PlatformDetailService
    documents: DocumentService
    game_systems: GameSystemRegistry
    codex: CodexService


def build_application_services(database_path: str | Path) -> ApplicationServices:
    connections = SQLiteConnectionFactory(database_path)
    platforms = SQLitePlatformRepository(connections)
    documents = DocumentService(
        styles=(
            DocumentStyle("dfs_standard", "DFS Standard", find_output_path(__file__)),
        )
    )
    return ApplicationServices(
        catalog=PlatformCatalogService(platforms),
        platform_details=PlatformDetailService(platforms),
        documents=documents,
        game_systems=build_default_registry(),
        codex=CodexService(),
    )
