"""DFS application settings workspace."""
from __future__ import annotations

from PySide6.QtWidgets import (
    QApplication, QCheckBox, QComboBox, QFormLayout, QGroupBox, QHBoxLayout,
    QLabel, QPushButton, QSpinBox, QVBoxLayout, QWidget,
)

from dfs.bootstrap import ApplicationContext


class SettingsPage(QWidget):
    def __init__(self, context: ApplicationContext) -> None:
        super().__init__()
        self._context = context
        self.setObjectName("settingsPage")

        title = QLabel("Settings")
        title.setObjectName("pageTitle")
        subtitle = QLabel("Application-wide appearance, startup, and document preferences")
        subtitle.setObjectName("pageSubtitle")

        appearance = QGroupBox("Appearance")
        appearance_form = QFormLayout(appearance)
        self.mode_combo = QComboBox()
        self.mode_combo.addItem("Follow system", "system")
        self.mode_combo.addItem("Light", "light")
        self.mode_combo.addItem("Dark", "dark")
        appearance_form.addRow("Appearance", self.mode_combo)

        startup = QGroupBox("Startup")
        startup_form = QFormLayout(startup)
        self.show_splash = QCheckBox("Show the DFS splash screen")
        self.splash_seconds = QSpinBox()
        self.splash_seconds.setRange(0, 10)
        self.splash_seconds.setSuffix(" seconds")
        self.startup_page = QComboBox()
        self.startup_page.addItem("Dashboard", "dashboard")
        self.startup_page.addItem("Platform Explorer", "platform_explorer")
        self.startup_page.addItem("Last workspace", "last_workspace")
        startup_form.addRow("", self.show_splash)
        startup_form.addRow("Minimum splash duration", self.splash_seconds)
        startup_form.addRow("Startup workspace", self.startup_page)

        documents = QGroupBox("Documents")
        documents_form = QFormLayout(documents)
        self.document_style = QComboBox()
        for style in context.documents.list_styles():
            self.document_style.addItem(style.label, style.style_id)
        documents_form.addRow("Default PDF theme", self.document_style)

        explorer = QGroupBox("Platform Explorer")
        explorer_form = QFormLayout(explorer)
        self.remember_layout = QCheckBox("Remember pane sizes and layout")
        self.remember_filters = QCheckBox("Remember filters")
        explorer_form.addRow("", self.remember_layout)
        explorer_form.addRow("", self.remember_filters)

        save = QPushButton("Apply Settings")
        save.setObjectName("primaryAction")
        save.clicked.connect(self._apply)
        reset = QPushButton("Reset Application Preferences")
        reset.clicked.connect(self._reset)
        buttons = QHBoxLayout()
        buttons.addStretch(1)
        buttons.addWidget(reset)
        buttons.addWidget(save)

        columns = QHBoxLayout()
        left = QVBoxLayout()
        left.addWidget(appearance)
        left.addWidget(startup)
        left.addStretch(1)
        right = QVBoxLayout()
        right.addWidget(explorer)
        right.addWidget(documents)
        right.addStretch(1)
        columns.addLayout(left, 1)
        columns.addLayout(right, 1)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 28)
        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addSpacing(18)
        layout.addLayout(columns)
        layout.addLayout(buttons)

        self.mode_combo.currentIndexChanged.connect(self._preview_theme)
        self._load_controls_from_settings()

    @staticmethod
    def _set_combo_data(combo: QComboBox, value: str) -> None:
        index = combo.findData(value)
        if index >= 0:
            combo.setCurrentIndex(index)

    def _load_controls_from_settings(self) -> None:
        """Refresh every control from the centralized settings service."""
        settings = self._context.settings
        self.mode_combo.blockSignals(True)
        self._set_combo_data(self.mode_combo, settings.appearance.mode)
        self.mode_combo.blockSignals(False)
        self.show_splash.setChecked(settings.show_splash)
        self.splash_seconds.setValue(round(settings.splash_duration_ms / 1000))
        self._set_combo_data(self.startup_page, settings.startup_page)
        self._set_combo_data(self.document_style, settings.default_document_style)
        self.remember_layout.setChecked(settings.get_bool("explorer/remember_layout", True))
        self.remember_filters.setChecked(settings.get_bool("explorer/remember_filters", True))

    def _preview_theme(self) -> None:
        app = QApplication.instance()
        self._context.settings.set_value("appearance/mode", self.mode_combo.currentData())
        self._context.theme.apply(app)

    def _apply(self) -> None:
        settings = self._context.settings
        settings.set_value("appearance/mode", self.mode_combo.currentData())
        settings.set_value("startup/show_splash", self.show_splash.isChecked())
        settings.set_value("startup/splash_duration_ms", self.splash_seconds.value() * 1000)
        settings.set_value("startup/page", self.startup_page.currentData())
        settings.set_value("documents/default_style", self.document_style.currentData())
        settings.set_value("explorer/remember_layout", self.remember_layout.isChecked())
        settings.set_value("explorer/remember_filters", self.remember_filters.isChecked())
        settings.sync()
        self._context.theme.apply(QApplication.instance())
        self._context.status.set("Settings saved")
        self._context.notifications.success("Settings", "Application preferences were saved.")

    def _reset(self) -> None:
        """Reset framework preferences and immediately reflect defaults in the UI."""
        self._context.settings.reset_application_preferences()
        self._load_controls_from_settings()
        self._context.theme.apply(QApplication.instance())
        self._context.status.set("Application preferences reset")
        self._context.notifications.success(
            "Settings",
            "Application preferences were restored to their defaults.",
        )
