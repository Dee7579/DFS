"""Top-level DFS desktop window and shared application framework shell."""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QCloseEvent, QKeySequence, QResizeEvent
from PySide6.QtWidgets import (
    QComboBox, QHBoxLayout, QLabel, QListWidget, QListWidgetItem, QMainWindow,
    QMessageBox, QPushButton, QStackedWidget, QStyle, QVBoxLayout, QWidget,
)

from dfs.bootstrap import ApplicationContext
from dfs.framework.notification_service import Notification
from dfs.ui.about_dialog import AboutDialog
from dfs.ui.dashboard import DashboardPage
from dfs.ui.platform_explorer.page import PlatformExplorerPage
from dfs.ui.settings.page import SettingsPage
from dfs.ui.fleet_builder import FleetBuilderPage
from dfs.ui.tactical_assistant import TacticalAssistantPage


class MainWindow(QMainWindow):
    PAGE_DASHBOARD = 0
    PAGE_EXPLORER = 1
    PAGE_FLEET_BUILDER = 2
    PAGE_TACTICAL_ASSISTANT = 3
    PAGE_SETTINGS = 4

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
        self._navigation_labels = (
            "Dashboard", "Platform Explorer", "Fleet Builder", "Tactical Assistant",
            "Codex Browser", "Campaign Manager", "Platform Editor", "Settings",
        )
        standard_icons = (
            QStyle.StandardPixmap.SP_DesktopIcon,
            QStyle.StandardPixmap.SP_FileDialogContentsView,
            QStyle.StandardPixmap.SP_DirIcon,
            QStyle.StandardPixmap.SP_ComputerIcon,
            QStyle.StandardPixmap.SP_MessageBoxInformation,
            QStyle.StandardPixmap.SP_DriveNetIcon,
            QStyle.StandardPixmap.SP_FileDialogDetailedView,
            QStyle.StandardPixmap.SP_FileDialogListView,
        )
        for text, icon_type in zip(self._navigation_labels, standard_icons):
            item = QListWidgetItem(text)
            item.setIcon(self.style().standardIcon(icon_type))
            item.setToolTip(text)
            if text not in (
                "Dashboard", "Platform Explorer", "Fleet Builder", "Tactical Assistant", "Settings"
            ):
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEnabled)
            self.navigation.addItem(item)

        self.pages = QStackedWidget()
        self.dashboard = DashboardPage(context)
        self.platform_explorer = PlatformExplorerPage(context)
        self.fleet_builder = FleetBuilderPage(context)
        self.tactical_assistant = TacticalAssistantPage(context)
        self.settings_page = SettingsPage(context)
        self.ship_viewer = self.platform_explorer
        self.pages.addWidget(self.dashboard)
        self.pages.addWidget(self.platform_explorer)
        self.pages.addWidget(self.fleet_builder)
        self.pages.addWidget(self.tactical_assistant)
        self.pages.addWidget(self.settings_page)

        self.app_name = QLabel("DFS")
        self.app_name.setObjectName("appName")
        self.app_tagline = QLabel("Tactical Reference System")
        self.app_tagline.setObjectName("appTagline")
        self.system_caption = QLabel("Game System")
        self.system_caption.setObjectName("gameSystemCaption")
        self.database_label = QLabel(database_label)
        self.database_label.setObjectName("databaseLabel")
        self.database_label.setWordWrap(True)
        self.sidebar_toggle_button = QPushButton("◀")
        self.sidebar_toggle_button.setFixedWidth(34)
        self.sidebar_toggle_button.setToolTip("Collapse navigation")
        self.sidebar_toggle_button.clicked.connect(self._toggle_sidebar)

        sidebar_header = QHBoxLayout()
        sidebar_header.addWidget(self.app_name, 1)
        sidebar_header.addWidget(self.sidebar_toggle_button)

        self.sidebar = QWidget()
        self.sidebar.setObjectName("sidebar")
        sidebar_layout = QVBoxLayout(self.sidebar)
        sidebar_layout.addLayout(sidebar_header)
        sidebar_layout.addWidget(self.app_tagline)
        sidebar_layout.addWidget(self.system_caption)
        sidebar_layout.addWidget(self.system_combo)
        sidebar_layout.addSpacing(8)
        sidebar_layout.addWidget(self.navigation, 1)
        sidebar_layout.addWidget(self.database_label)

        central = QWidget()
        layout = QHBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.sidebar)
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

        self._sidebar_collapsed = False
        self._sidebar_manual_override = False
        saved_sidebar = self._settings.value("main_window/sidebar_collapsed", None)
        collapsed = (
            self._settings.get_bool("main_window/sidebar_collapsed", False)
            if saved_sidebar is not None
            else self.width() < 1250
        )
        self._set_sidebar_collapsed(collapsed, persist=False)

        saved_page = self._settings.get_int("main_window/page", 0)
        startup_page = self._settings.startup_page
        if startup_page == "platform_explorer":
            saved_page = self.PAGE_EXPLORER
        elif startup_page == "dashboard":
            saved_page = self.PAGE_DASHBOARD
        self.navigation.setCurrentRow(saved_page if saved_page in (0, 1, 2, 3, 7) else 0)

    def _toggle_sidebar(self) -> None:
        self._sidebar_manual_override = True
        self._set_sidebar_collapsed(not self._sidebar_collapsed, persist=True)

    def _set_sidebar_collapsed(self, collapsed: bool, *, persist: bool) -> None:
        self._sidebar_collapsed = bool(collapsed)
        if self._sidebar_collapsed:
            self.sidebar.setFixedWidth(58)
            self.navigation.setFixedWidth(42)
            self.app_name.hide()
            self.app_tagline.hide()
            self.system_caption.hide()
            self.system_combo.hide()
            self.database_label.hide()
            self.sidebar_toggle_button.setText("▶")
            self.sidebar_toggle_button.setToolTip("Expand navigation")
        else:
            self.sidebar.setFixedWidth(214)
            self.navigation.setFixedWidth(190)
            self.app_name.show()
            self.app_tagline.show()
            self.system_caption.show()
            self.system_combo.show()
            self.database_label.show()
            self.sidebar_toggle_button.setText("◀")
            self.sidebar_toggle_button.setToolTip("Collapse navigation")

        for index, label in enumerate(self._navigation_labels):
            item = self.navigation.item(index)
            if item is not None:
                item.setText("" if self._sidebar_collapsed else label)
                item.setToolTip(label)
        if persist:
            self._settings.set_value(
                "main_window/sidebar_collapsed",
                self._sidebar_collapsed,
            )
            self._settings.sync()

    def resizeEvent(self, event: QResizeEvent) -> None:  # noqa: N802
        super().resizeEvent(event)
        if (
            hasattr(self, "sidebar")
            and hasattr(self, "_sidebar_collapsed")
            and event.size().width() < 1250
            and not self._sidebar_collapsed
            and not self._sidebar_manual_override
        ):
            self._set_sidebar_collapsed(True, persist=False)

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

        fleet_action = QAction("&Fleet Builder", self)
        fleet_action.setShortcut(QKeySequence("Ctrl+2"))
        fleet_action.triggered.connect(lambda: self.navigation.setCurrentRow(2))
        self.addAction(fleet_action)

        tactical_action = QAction("&Tactical Assistant", self)
        tactical_action.setShortcut(QKeySequence("Ctrl+3"))
        tactical_action.triggered.connect(lambda: self.navigation.setCurrentRow(3))
        self.addAction(tactical_action)

    def _build_status_bar(self) -> None:
        system = self._context.game_systems.get(self._settings.default_game_system)
        platform_count = self._context.catalog.count()
        profile_count = self._context.catalog.count_profiles()
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
        mapping = {
            0: self.PAGE_DASHBOARD,
            1: self.PAGE_EXPLORER,
            2: self.PAGE_FLEET_BUILDER,
            3: self.PAGE_TACTICAL_ASSISTANT,
            7: self.PAGE_SETTINGS,
        }
        if row in mapping:
            self.pages.setCurrentIndex(mapping[row])
            self._settings.set_value("main_window/page", row)

    def closeEvent(self, event: QCloseEvent) -> None:  # noqa: N802
        if not self.tactical_assistant.confirm_close():
            event.ignore()
            return
        self.platform_explorer.save_settings()
        self._settings.set_value("main_window/geometry", self.saveGeometry())
        self._settings.set_value("main_window/state", self.saveState())
        self._settings.sync()
        super().closeEvent(event)
