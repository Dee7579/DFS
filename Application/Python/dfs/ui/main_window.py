"""Top-level DFS desktop window, game-system selector and module navigation."""

from __future__ import annotations

from PySide6.QtCore import QSettings, Qt
from PySide6.QtGui import QAction, QCloseEvent, QKeySequence, QStandardItemModel
from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from dfs.bootstrap import ApplicationServices
from dfs.ui.about_dialog import AboutDialog
from dfs.ui.dashboard import DashboardPage
from dfs.ui.platform_explorer.page import PlatformExplorerPage


class MainWindow(QMainWindow):
    def __init__(self, services: ApplicationServices, database_label: str) -> None:
        super().__init__()
        self._services = services
        self._database_label = database_label
        self._settings = QSettings()
        self.setWindowTitle("Dee's Fighting Ships — Tactical Reference System")
        self.resize(1500, 900)
        self.setMinimumSize(1100, 700)

        self.system_combo = QComboBox()
        self.system_combo.setObjectName("gameSystemSelector")
        selected_id = self._settings.value(
            "application/game_system", services.game_systems.default_id, type=str
        )
        selected_index = 0
        for index, system in enumerate(services.game_systems.list_systems()):
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
            "Dashboard",
            "Platform Explorer",
            "Fleet Builder",
            "Codex Browser",
            "Campaign Manager",
            "Platform Editor",
        ):
            item = QListWidgetItem(text)
            if text not in ("Dashboard", "Platform Explorer"):
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEnabled)
            self.navigation.addItem(item)

        self.pages = QStackedWidget()
        self.dashboard = DashboardPage(services)
        self.platform_explorer = PlatformExplorerPage(services)
        self.ship_viewer = self.platform_explorer
        self.pages.addWidget(self.dashboard)
        self.pages.addWidget(self.platform_explorer)

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
        self._build_menu()

        geometry = self._settings.value("main_window/geometry")
        state = self._settings.value("main_window/state")
        if geometry:
            self.restoreGeometry(geometry)
        if state:
            self.restoreState(state)
        self.navigation.setCurrentRow(self._settings.value("main_window/page", 0, type=int))

    def _build_menu(self) -> None:
        view_menu = self.menuBar().addMenu("&View")
        reset_layout_action = QAction("Reset Platform Explorer Layout", self)
        reset_layout_action.setShortcut(QKeySequence("Ctrl+Shift+0"))
        reset_layout_action.triggered.connect(self._reset_platform_explorer_layout)
        view_menu.addAction(reset_layout_action)

        help_menu = self.menuBar().addMenu("&Help")
        about_action = QAction("&About Dee's Fighting Ships", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)

        explorer_action = QAction("Platform &Explorer", self)
        explorer_action.setShortcut(QKeySequence("Ctrl+1"))
        explorer_action.triggered.connect(lambda: self.navigation.setCurrentRow(1))
        self.addAction(explorer_action)

    def _system_changed(self, index: int) -> None:
        system_id = self.system_combo.itemData(index)
        if system_id:
            self._settings.setValue("application/game_system", system_id)

    def _open_platform_from_dashboard(self, ship_id: int) -> None:
        self.navigation.setCurrentRow(1)
        self.platform_explorer.open_platform(ship_id)

    def _reset_platform_explorer_layout(self) -> None:
        self.navigation.setCurrentRow(1)
        self.platform_explorer.reset_layout()

    def _show_about(self) -> None:
        AboutDialog(self._services, self._database_label, self).exec()

    def _navigate(self, row: int) -> None:
        if row in (0, 1):
            self.pages.setCurrentIndex(row)
            self._settings.setValue("main_window/page", row)

    def closeEvent(self, event: QCloseEvent) -> None:  # noqa: N802
        self.platform_explorer.save_settings()
        self._settings.setValue("main_window/geometry", self.saveGeometry())
        self._settings.setValue("main_window/state", self.saveState())
        super().closeEvent(event)
