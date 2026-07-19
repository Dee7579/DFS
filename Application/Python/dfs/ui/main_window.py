"""Top-level DFS desktop window and shared application framework shell."""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QCloseEvent, QKeySequence
from PySide6.QtWidgets import (
    QComboBox, QHBoxLayout, QLabel, QListWidget, QListWidgetItem, QMainWindow,
    QMessageBox, QStackedWidget, QVBoxLayout, QWidget,
)

from dfs.bootstrap import ApplicationContext
from dfs.framework.notification_service import Notification
from dfs.domain.catalog import PlatformFilter
from dfs.ui.about_dialog import AboutDialog
from dfs.ui.dashboard import DashboardPage
from dfs.ui.platform_explorer.page import PlatformExplorerPage
from dfs.ui.settings.page import SettingsPage
from dfs.ui.fleet_builder import FleetBuilderPage


class MainWindow(QMainWindow):
    PAGE_DASHBOARD = 0
    PAGE_EXPLORER = 1
    PAGE_FLEET_BUILDER = 2
    PAGE_SETTINGS = 3

    def __init__(self, context: ApplicationContext, database_label: str) -> None:
        super().__init__()
        self._context = context
        self._services = context  # Compatibility alias for current modules.
        self._database_label = database_label
        self._settings = context.settings
        self.setWindowTitle("Dee's Fighting Ships — Tactical Reference System")
        self.resize(1500, 900)
        self.setMinimumSize(1100, 700)

        self.system_combo = QComboBox()
        self.system_combo.setObjectName("gameSystemSelector")
        selected_id = self._settings.default_game_system
        selected_index = 0
        for index, system in enumerate(context.game_systems.list_systems()):
            label = system.short_name if system.enabled else f"{system.short_name} — Coming Soon"
            self.system_combo.addItem(label, system.id)
            item = self.system_combo.model().item(index)
            if item is not None and not system.enabled:
                item.setEnabled(False)
            if system.id == selected_id and system.enabled:
                selected_index = index
        self.system_combo.setCurrentIndex(selected_index)
        self.system_combo.currentIndexChanged.connect(self._system_changed)

        self.navigation = QListWidget()
        self.navigation.setObjectName("navigation")
        self.navigation.setFixedWidth(190)
        for text in (
            "Dashboard", "Platform Explorer", "Fleet Builder", "Tactical Assistant",
            "Codex Browser", "Campaign Manager", "Platform Editor", "Settings",
        ):
            item = QListWidgetItem(text)
            if text not in ("Dashboard", "Platform Explorer", "Fleet Builder", "Settings"):
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEnabled)
            self.navigation.addItem(item)

        self.pages = QStackedWidget()
        self.dashboard = DashboardPage(context)
        self.platform_explorer = PlatformExplorerPage(context)
        self.fleet_builder = FleetBuilderPage(context)
        self.settings_page = SettingsPage(context)
        self.ship_viewer = self.platform_explorer
        self.pages.addWidget(self.dashboard)
        self.pages.addWidget(self.platform_explorer)
        self.pages.addWidget(self.fleet_builder)
        self.pages.addWidget(self.settings_page)

        app_name = QLabel("DFS")
        app_name.setObjectName("appName")
        app_tagline = QLabel("Tactical Reference System")
        app_tagline.setObjectName("appTagline")
        system_caption = QLabel("Game System")
        system_caption.setObjectName("gameSystemCaption")
        database = QLabel(database_label)
        database.setObjectName("databaseLabel")
        database.setWordWrap(True)

        sidebar = QWidget()
        sidebar.setObjectName("sidebar")
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.addWidget(app_name)
        sidebar_layout.addWidget(app_tagline)
        sidebar_layout.addWidget(system_caption)
        sidebar_layout.addWidget(self.system_combo)
        sidebar_layout.addSpacing(8)
        sidebar_layout.addWidget(self.navigation, 1)
        sidebar_layout.addWidget(database)

        central = QWidget()
        layout = QHBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(sidebar)
        layout.addWidget(self.pages, 1)
        self.setCentralWidget(central)

        self.navigation.currentRowChanged.connect(self._navigate)
        self.dashboard.open_platform_explorer.connect(lambda: self.navigation.setCurrentRow(1))
        self.dashboard.open_platform.connect(self._open_platform_from_dashboard)
        self.fleet_builder.open_platform_requested.connect(self._open_platform_from_fleet_builder)
        self._build_menu()
        self._build_status_bar()
        context.notifications.published.connect(self._show_notification)

        geometry = self._settings.value("main_window/geometry")
        state = self._settings.value("main_window/state")
        if geometry:
            self.restoreGeometry(geometry)
        if state:
            self.restoreState(state)

        saved_page = self._settings.get_int("main_window/page", 0)
        startup_page = self._settings.startup_page
        if startup_page == "platform_explorer":
            saved_page = self.PAGE_EXPLORER
        elif startup_page == "dashboard":
            saved_page = self.PAGE_DASHBOARD
        self.navigation.setCurrentRow(saved_page if saved_page in (0, 1, 2, 7) else 0)

    def _build_menu(self) -> None:
        view_menu = self.menuBar().addMenu("&View")
        reset_layout_action = QAction("Reset Platform Explorer Layout", self)
        reset_layout_action.setShortcut(QKeySequence("Ctrl+Shift+0"))
        reset_layout_action.triggered.connect(self._reset_platform_explorer_layout)
        view_menu.addAction(reset_layout_action)
        settings_action = QAction("&Settings", self)
        settings_action.setShortcut(QKeySequence("Ctrl+,"))
        settings_action.triggered.connect(lambda: self.navigation.setCurrentRow(7))
        view_menu.addAction(settings_action)

        help_menu = self.menuBar().addMenu("&Help")
        about_action = QAction("&About Dee's Fighting Ships", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)

        explorer_action = QAction("Platform &Explorer", self)
        explorer_action.setShortcut(QKeySequence("Ctrl+1"))
        explorer_action.triggered.connect(lambda: self.navigation.setCurrentRow(1))
        self.addAction(explorer_action)

    def _build_status_bar(self) -> None:
        system = self._context.game_systems.get(self._settings.default_game_system)
        platform_count = self._context.catalog.count()
        profile_count = sum(
            item.profile_count for item in self._context.catalog.search(PlatformFilter(limit=1000))
        )
        self._system_status = QLabel(system.short_name)
        self._data_status = QLabel(f"{platform_count:,} Platforms  •  {profile_count:,} Profiles")
        self._message_status = QLabel(self._context.status.message)
        self.statusBar().addWidget(self._system_status)
        self.statusBar().addWidget(QLabel("  |  "))
        self.statusBar().addWidget(self._data_status)
        self.statusBar().addPermanentWidget(self._message_status)
        self._context.status.changed.connect(self._message_status.setText)

    def _system_changed(self, index: int) -> None:
        system_id = self.system_combo.itemData(index)
        if system_id:
            self._settings.set_value("application/game_system", system_id)
            self._settings.sync()
            system = self._context.game_systems.get(system_id)
            self._system_status.setText(system.short_name)
            self._context.status.set(f"Game system: {system.display_name}")

    def _open_platform_from_dashboard(self, ship_id: int) -> None:
        self.navigation.setCurrentRow(1)
        self.platform_explorer.open_platform(ship_id)

    def _open_platform_from_fleet_builder(self, ship_id: int) -> None:
        self.navigation.setCurrentRow(1)
        self.platform_explorer.open_platform(ship_id)

    def _reset_platform_explorer_layout(self) -> None:
        self.navigation.setCurrentRow(1)
        self.platform_explorer.reset_layout()
        self._context.status.set("Platform Explorer layout reset")

    def _show_about(self) -> None:
        AboutDialog(self._context, self._database_label, self).exec()

    def _show_notification(self, notification: Notification) -> None:
        if notification.level == "error":
            QMessageBox.critical(self, notification.title, notification.message)
        elif notification.level == "warning":
            QMessageBox.warning(self, notification.title, notification.message)
        else:
            self.statusBar().showMessage(f"{notification.title}: {notification.message}", 3500)

    def _navigate(self, row: int) -> None:
        mapping = {0: self.PAGE_DASHBOARD, 1: self.PAGE_EXPLORER, 2: self.PAGE_FLEET_BUILDER, 7: self.PAGE_SETTINGS}
        if row in mapping:
            self.pages.setCurrentIndex(mapping[row])
            self._settings.set_value("main_window/page", row)

    def closeEvent(self, event: QCloseEvent) -> None:  # noqa: N802
        self.platform_explorer.save_settings()
        self._settings.set_value("main_window/geometry", self.saveGeometry())
        self._settings.set_value("main_window/state", self.saveState())
        self._settings.sync()
        super().closeEvent(event)
