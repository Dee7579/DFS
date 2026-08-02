"""Resolve DFS application resources from one location."""
from __future__ import annotations
from pathlib import Path

from dfs.app_paths import (
    ApplicationPaths,
    build_application_paths,
    ensure_writable_folder,
)


class ResourceService:
    def __init__(self, paths: ApplicationPaths | Path) -> None:
        if isinstance(paths, ApplicationPaths):
            resolved = paths
        else:
            resolved = build_application_paths(paths)

        # project_root is retained for compatibility and is always read-only.
        self.project_root = resolved.application_root
        self.application_root = resolved.application_root
        self.resources_root = resolved.resources_root
        self.reference_sheets_root = resolved.reference_sheets_root
        self.user_data_root = resolved.user_data_root
        self.logs_root = resolved.logs_root
        self.documents_root = resolved.documents_root
        self.fleet_files_root = resolved.fleets_root
        self.game_files_root = resolved.games_root
        self.generated_sheets_root = resolved.generated_sheets_root

    def path(self, relative: str | Path) -> Path:
        return self.resources_root / Path(relative)

    def icon(self, name: str) -> Path:
        return self.path(Path("icons") / name)

    def logo(self, name: str = "dfs_logo.svg") -> Path:
        return self.path(Path("branding") / name)

    def writable_folder(self, configured: str, fallback: Path) -> Path:
        """Resolve a user-selected folder without falling back into app files."""

        return ensure_writable_folder(
            configured,
            fallback,
            self.application_root,
        )
