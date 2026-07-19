"""Application service for loading a complete platform and all profiles."""

from __future__ import annotations

from dfs.domain.catalog import PlatformDetail, PlatformProfile
from dfs.repositories.platform_repository import PlatformRepository


class PlatformNotFoundError(LookupError):
    pass


class PlatformDetailService:
    def __init__(self, repository: PlatformRepository):
        self._repository = repository

    def get(self, ship_id: int) -> PlatformDetail:
        platform = self._repository.get_by_id(ship_id)
        if platform is None:
            raise PlatformNotFoundError(f"No DFS platform exists with ship_id={ship_id}")
        return platform
    def get_profile(self, profile_id: int) -> PlatformProfile | None:
        """Load one fleet-specific platform profile by its stable ID."""
        return self._repository.get_profile_by_id(profile_id)
