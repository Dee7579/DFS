"""Generated-sheet discovery for the DFS desktop application."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path


def _normalize(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", value.casefold()).strip("_")


@dataclass(frozen=True, slots=True)
class DocumentStyle:
    style_id: str
    label: str
    root: Path


@dataclass(frozen=True, slots=True)
class DocumentReference:
    style_id: str
    style_label: str
    path: Path


class DocumentService:
    """Locate generated PDFs without exposing filename rules to the GUI."""

    def __init__(self, styles: tuple[DocumentStyle, ...]):
        self._styles = styles
        self._index: dict[str, tuple[Path, ...]] = {}

    def list_styles(self) -> tuple[DocumentStyle, ...]:
        return tuple(style for style in self._styles if style.root.is_dir())

    def _files_for_style(self, style: DocumentStyle) -> tuple[Path, ...]:
        cached = self._index.get(style.style_id)
        if cached is None:
            cached = tuple(sorted(style.root.rglob("*.pdf"))) if style.root.is_dir() else ()
            self._index[style.style_id] = cached
        return cached

    def refresh(self) -> None:
        self._index.clear()

    def find_sheet(
        self,
        *,
        style_id: str,
        file_name: str,
        platform_name: str,
        faction_name: str,
        fleet_name: str,
    ) -> DocumentReference | None:
        style = next((item for item in self.list_styles() if item.style_id == style_id), None)
        if style is None:
            return None

        targets = {_normalize(file_name), _normalize(platform_name)} - {""}
        candidates: list[tuple[int, Path]] = []
        faction_token = _normalize(faction_name)
        fleet_token = _normalize(fleet_name)

        for path in self._files_for_style(style):
            stem = _normalize(path.stem)
            if not any(stem.endswith(target) or target in stem for target in targets):
                continue
            path_token = _normalize(str(path.parent))
            score = 0
            if faction_token and faction_token in path_token:
                score += 20
            if fleet_token and fleet_token in path_token:
                score += 30
            if any(stem.endswith(target) for target in targets):
                score += 10
            candidates.append((score, path))

        if not candidates:
            return None
        candidates.sort(key=lambda item: (-item[0], len(str(item[1])), str(item[1]).casefold()))
        return DocumentReference(style.style_id, style.label, candidates[0][1])
