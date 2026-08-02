from __future__ import annotations

import os
from types import SimpleNamespace

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
pytest.importorskip("PySide6")

from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QApplication, QWidget

import dfs.ui.main_window as main_window_module


class _Settings:
    def __init__(self) -> None:
        self.values: dict[str, object] = {}

    @property
    def default_game_system(self) -> str:
        return "b5_acta_2e"

    @property
    def startup_page(self) -> str:
        return "dashboard"

    def value(self, key: str, default=None):
        return self.values.get(key, default)

    def get_int(self, key: str, default: int = 0) -> int:
        return int(self.values.get(key, default))

    def get_bool(self, key: str, default: bool = False) -> bool:
        return bool(self.values.get(key, default))

    def set_value(self, key: str, value: object) -> None:
        self.values[key] = value

    def sync(self) -> None:
        pass


class _Status(QObject):
    changed = Signal(str)

    def __init__(self) -> None:
        super().__init__()
        self.message = "Ready"

    def set(self, message: str) -> None:
        self.message = message
        self.changed.emit(message)


class _Notifications(QObject):
    published = Signal(object)


class _ContextWidget(QWidget):
    def __init__(self, _context) -> None:
        super().__init__()


class _Dashboard(_ContextWidget):
    open_platform_explorer = Signal()
    open_platform = Signal(int)


class _Explorer(_ContextWidget):
    def open_platform(self, _ship_id: int) -> None:
        pass

    def reset_layout(self) -> None:
        pass

    def save_settings(self) -> None:
        pass


class _FleetBuilder(_ContextWidget):
    open_platform_requested = Signal(int)


class _Tactical(_ContextWidget):
    def confirm_close(self) -> bool:
        return True


def _context(settings: _Settings):
    system = SimpleNamespace(
        id="b5_acta_2e",
        short_name="B5 ACTA",
        display_name="Babylon 5 ACTA",
        enabled=True,
    )
    return SimpleNamespace(
        settings=settings,
        game_systems=SimpleNamespace(
            list_systems=lambda: (system,),
            get=lambda _system_id: system,
        ),
        catalog=SimpleNamespace(count=lambda: 304, count_profiles=lambda: 304),
        status=_Status(),
        notifications=_Notifications(),
    )


def test_sidebar_collapses_to_icon_rail_and_persists(monkeypatch) -> None:
    app = QApplication.instance() or QApplication([])
    monkeypatch.setattr(main_window_module, "DashboardPage", _Dashboard)
    monkeypatch.setattr(main_window_module, "PlatformExplorerPage", _Explorer)
    monkeypatch.setattr(main_window_module, "FleetBuilderPage", _FleetBuilder)
    monkeypatch.setattr(main_window_module, "TacticalAssistantPage", _Tactical)
    monkeypatch.setattr(main_window_module, "SettingsPage", _ContextWidget)

    settings = _Settings()
    window = main_window_module.MainWindow(_context(settings), "Certified data")
    try:
        window._set_sidebar_collapsed(True, persist=True)
        assert window.sidebar.width() == 58
        assert window.navigation.item(0).text() == ""
        assert window.navigation.item(0).toolTip() == "Dashboard"
        assert window.app_tagline.isHidden() is True
        assert settings.values["main_window/sidebar_collapsed"] is True

        window._toggle_sidebar()
        assert window.navigation.item(0).text() == "Dashboard"
        assert window.sidebar_toggle_button.text() == "◀"
        assert settings.values["main_window/sidebar_collapsed"] is False
        app.processEvents()
    finally:
        window.close()


def test_small_window_auto_collapses_without_overwriting_preference(monkeypatch) -> None:
    app = QApplication.instance() or QApplication([])
    monkeypatch.setattr(main_window_module, "DashboardPage", _Dashboard)
    monkeypatch.setattr(main_window_module, "PlatformExplorerPage", _Explorer)
    monkeypatch.setattr(main_window_module, "FleetBuilderPage", _FleetBuilder)
    monkeypatch.setattr(main_window_module, "TacticalAssistantPage", _Tactical)
    monkeypatch.setattr(main_window_module, "SettingsPage", _ContextWidget)

    settings = _Settings()
    window = main_window_module.MainWindow(_context(settings), "Certified data")
    try:
        window.show()
        window.resize(1100, 700)
        app.processEvents()
        assert window._sidebar_collapsed is True
        assert "main_window/sidebar_collapsed" not in settings.values
    finally:
        window.close()
