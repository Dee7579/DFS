"""Top-level DFS desktop window and module navigation."""

from __future__ import annotations

from PySide6.QtCore import QSettings, Qt
from PySide6.QtGui import QCloseEvent
from PySide6.QtWidgets import (
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
from dfs.ui.dashboard import DashboardPage
from dfs.ui.ship_viewer.page import ShipViewerPage


class MainWindow(QMainWindow):
    def __init__(self, services: ApplicationServices, database_label: str) -> None:
        super().__init__()
        self._settings = QSettings()
        self.setWindowTitle("Dee's Fighting Ships")
        self.resize(1500, 900)
        self.setMinimumSize(1100, 700)

        self.navigation = QListWidget()
        self.navigation.setObjectName("navigation")
        self.navigation.setFixedWidth(190)
        for text in (
            "Dashboard",
            "Ship Viewer",
            "Fleet Builder",
            "Codex Browser",
            "Campaign Manager",
            "Platform Editor",
        ):
            item = QListWidgetItem(text)
            if text not in ("Dashboard", "Ship Viewer"):
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEnabled)
            self.navigation.addItem(item)

        self.pages = QStackedWidget()
        self.dashboard = DashboardPage()
        self.ship_viewer = ShipViewerPage(services)
        self.pages.addWidget(self.dashboard)
        self.pages.addWidget(self.ship_viewer)

        app_name = QLabel("DFS")
        app_name.setObjectName("appName")
        database = QLabel(database_label)
        database.setObjectName("databaseLabel")
        database.setWordWrap(True)

        sidebar = QWidget()
        sidebar.setObjectName("sidebar")
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.addWidget(app_name)
        sidebar_layout.addWidget(self.navigation, 1)
        sidebar_layout.addWidget(database)

        central = QWidget()
        layout = QHBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(sidebar)
        layout.addWidget(self.pages, 1)
        self.setCentralWidget(central)

        self.navigation.currentRowChanged.connect(self._navigate)
        self.dashboard.open_ship_viewer.connect(lambda: self.navigation.setCurrentRow(1))

        geometry = self._settings.value("main_window/geometry")
        state = self._settings.value("main_window/state")
        if geometry:
            self.restoreGeometry(geometry)
        if state:
            self.restoreState(state)
        self.navigation.setCurrentRow(
            self._settings.value("main_window/page", 0, type=int)
        )

    def _navigate(self, row: int) -> None:
        if row in (0, 1):
            self.pages.setCurrentIndex(row)
            self._settings.setValue("main_window/page", row)

    def closeEvent(self, event: QCloseEvent) -> None:  # noqa: N802
        self.ship_viewer.save_settings()
        self._settings.setValue("main_window/geometry", self.saveGeometry())
        self._settings.setValue("main_window/state", self.saveState())
        super().closeEvent(event)
