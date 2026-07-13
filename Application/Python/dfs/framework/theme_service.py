"""Live DFS appearance and accent theme service."""
from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QApplication

from dfs.framework.settings_service import SettingsService
from dfs.ui.theme import build_application_stylesheet


@dataclass(frozen=True, slots=True)
class AccentPalette:
    id: str
    label: str
    accent: str
    accent_hover: str
    accent_soft: str


ACCENTS: tuple[AccentPalette, ...] = (
    AccentPalette("teal", "Teal", "#0f766e", "#115e59", "#ccfbf1"),
    AccentPalette("blue", "Blue", "#2563eb", "#1d4ed8", "#dbeafe"),
    AccentPalette("green", "Green", "#15803d", "#166534", "#dcfce7"),
    AccentPalette("purple", "Purple", "#7e22ce", "#6b21a8", "#f3e8ff"),
    AccentPalette("amber", "Amber", "#b45309", "#92400e", "#fef3c7"),
    AccentPalette("crimson", "Crimson", "#be123c", "#9f1239", "#ffe4e6"),
)


class ThemeService(QObject):
    theme_changed = Signal(str, str)

    def __init__(self, settings: SettingsService) -> None:
        super().__init__()
        self._settings = settings

    def accents(self) -> tuple[AccentPalette, ...]:
        return ACCENTS

    def current_accent(self) -> AccentPalette:
        accent_id = self._settings.appearance.accent
        return next((item for item in ACCENTS if item.id == accent_id), ACCENTS[0])

    def current_mode(self) -> str:
        return self._settings.appearance.mode

    def apply(self, app: QApplication) -> None:
        palette = self.current_accent()
        app.setStyleSheet(build_application_stylesheet(
            mode=self.current_mode(),
            accent=palette.accent,
            accent_hover=palette.accent_hover,
            accent_soft=palette.accent_soft,
        ))

    def set_accent(self, accent_id: str, app: QApplication | None = None) -> None:
        if accent_id not in {item.id for item in ACCENTS}:
            raise ValueError(f"Unknown DFS accent: {accent_id}")
        self._settings.set_value("appearance/accent", accent_id)
        self._settings.sync()
        if app is not None:
            self.apply(app)
        self.theme_changed.emit(self.current_mode(), accent_id)

    def set_mode(self, mode: str, app: QApplication | None = None) -> None:
        if mode not in {"system", "light", "dark"}:
            raise ValueError(f"Unknown DFS appearance mode: {mode}")
        self._settings.set_value("appearance/mode", mode)
        self._settings.sync()
        if app is not None:
            self.apply(app)
        self.theme_changed.emit(mode, self.current_accent().id)
