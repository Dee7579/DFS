"""Centralized, versioned application settings for DFS."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from PySide6.QtCore import QSettings


SETTINGS_SCHEMA_VERSION = 1


@dataclass(frozen=True, slots=True)
class AppearanceSettings:
    mode: str = "system"
    accent: str = "teal"


class SettingsService:
    """Single API for persistent DFS preferences.

    QSettings remains the storage backend for compatibility with existing
    installations, while all new code should access preferences through this
    service instead of constructing QSettings directly.
    """

    def __init__(self, backend: QSettings | None = None) -> None:
        self._backend = backend or QSettings()
        self._ensure_schema()

    def _ensure_schema(self) -> None:
        version = self.get_int("framework/schema_version", 0)
        if version < SETTINGS_SCHEMA_VERSION:
            self._backend.setValue("framework/schema_version", SETTINGS_SCHEMA_VERSION)
            self._backend.sync()

    def value(self, key: str, default: Any = None, value_type: type | None = None) -> Any:
        if value_type is None:
            return self._backend.value(key, default)
        return self._backend.value(key, default, type=value_type)

    def set_value(self, key: str, value: Any) -> None:
        self._backend.setValue(key, value)

    def remove(self, key: str) -> None:
        self._backend.remove(key)

    def sync(self) -> None:
        self._backend.sync()

    def get_bool(self, key: str, default: bool = False) -> bool:
        return bool(self.value(key, default, bool))

    def get_int(self, key: str, default: int = 0) -> int:
        return int(self.value(key, default, int))

    def get_str(self, key: str, default: str = "") -> str:
        value = self.value(key, default, str)
        return str(value) if value is not None else default

    @property
    def appearance(self) -> AppearanceSettings:
        return AppearanceSettings(
            mode=self.get_str("appearance/mode", "system"),
            accent=self.get_str("appearance/accent", "teal"),
        )

    @property
    def show_splash(self) -> bool:
        return self.get_bool("startup/show_splash", True)

    @property
    def splash_duration_ms(self) -> int:
        return max(0, self.get_int("startup/splash_duration_ms", 3000))

    @property
    def startup_page(self) -> str:
        return self.get_str("startup/page", "dashboard")

    @property
    def default_game_system(self) -> str:
        return self.get_str("application/game_system", "b5_acta_2e")

    @property
    def default_document_style(self) -> str:
        return self.get_str("documents/default_style", "dfs_standard")

    def reset_application_preferences(self) -> None:
        """Reset framework-managed preferences without touching user data."""
        for group in ("appearance", "startup", "documents", "explorer", "fleet", "framework"):
            self.remove(group)
        self._ensure_schema()
        self.sync()
