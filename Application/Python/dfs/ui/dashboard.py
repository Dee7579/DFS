"""DFS application dashboard."""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QGridLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from dfs.bootstrap import ApplicationServices
from dfs.domain.catalog import PlatformFilter


class DashboardPage(QWidget):
    open_platform_explorer = Signal()
    open_ship_viewer = open_platform_explorer  # Compatibility alias.

    def __init__(self, services: ApplicationServices) -> None:
        super().__init__()
        platform_count = services.catalog.count()
        platforms = services.catalog.search(PlatformFilter(limit=1000))
        profile_count = sum(item.profile_count for item in platforms)
        faction_count = len(services.catalog.list_factions())

        title = QLabel("Dee's Fighting Ships")
        title.setObjectName("dashboardTitle")
        subtitle = QLabel("Tactical Reference System — Babylon 5: A Call to Arms")
        subtitle.setObjectName("dashboardSubtitle")

        database_summary = QLabel(
            f"{platform_count:,} Platforms    •    {profile_count:,} Profiles    •    "
            f"{faction_count:,} Factions"
        )
        database_summary.setObjectName("dashboardStats")

        explorer = QPushButton("Platform Explorer\nBrowse ships, fighters, traits, weapons and sheets")
        explorer.setObjectName("moduleButton")
        explorer.clicked.connect(self.open_platform_explorer.emit)

        grid = QGridLayout()
        grid.addWidget(explorer, 0, 0)
        for column, text in enumerate(
            ("Fleet Builder\nPlanned for DFS 2.1", "Codex Browser\nPlanned", "Campaign Manager\nPlanned"),
            start=1,
        ):
            button = QPushButton(text)
            button.setEnabled(False)
            button.setObjectName("moduleButton")
            grid.addWidget(button, 0, column)

        layout = QVBoxLayout(self)
        layout.addStretch(1)
        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addWidget(database_summary)
        layout.addSpacing(28)
        layout.addLayout(grid)
        layout.addStretch(2)
