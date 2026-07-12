"""Application service for browsing and filtering DFS platforms."""

from __future__ import annotations

from dataclasses import replace

from dfs.domain.catalog import FilterOption, PlatformFilter, PlatformSummary
from dfs.repositories.platform_repository import PlatformRepository


class PlatformCatalogService:
    def __init__(self, repository: PlatformRepository):
        self._repository = repository

    def search(self, filters: PlatformFilter | None = None) -> list[PlatformSummary]:
        resolved = filters or PlatformFilter()
        if resolved.limit < 1:
            resolved = replace(resolved, limit=1)
        return self._repository.search(resolved)

    def count(self, filters: PlatformFilter | None = None) -> int:
        return self._repository.count(filters or PlatformFilter())

    def list_factions(self) -> list[FilterOption]:
        return self._repository.list_factions()

    def list_fleets(self, faction_id: int | None = None) -> list[FilterOption]:
        return self._repository.list_fleets(faction_id)

    def list_priorities(self) -> list[FilterOption]:
        return self._repository.list_priorities()

    def list_traits(self) -> list[FilterOption]:
        return self._repository.list_traits()

    def list_weapons(self) -> list[FilterOption]:
        return self._repository.list_weapons()
