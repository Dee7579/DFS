"""Resolve DFS application resources from one location."""
from __future__ import annotations
from pathlib import Path


class ResourceService:
    def __init__(self, project_root: Path) -> None:
        self.project_root = project_root.resolve()
        self.resources_root = self.project_root / "resources"

    def path(self, relative: str | Path) -> Path:
        return self.resources_root / Path(relative)

    def icon(self, name: str) -> Path:
        return self.path(Path("icons") / name)

    def logo(self, name: str = "dfs_logo.svg") -> Path:
        return self.path(Path("branding") / name)
