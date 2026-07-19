"""Useful DFS application dashboard and launch surface."""

from __future__ import annotations

from PySide6.QtCore import QSettings, Signal, Qt
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from dfs.bootstrap import ApplicationServices


class _DashboardCard(QFrame):
    def __init__(self, title: str, body: QWidget | str) -> None:
        super().__init__()
        self.setObjectName("dashboardCard")
        layout = QVBoxLayout(self)
        heading = QLabel(title)
        heading.setObjectName("dashboardCardTitle")
        layout.addWidget(heading)
        if isinstance(body, str):
            label = QLabel(body)
            label.setObjectName("dashboardCardBody")
            label.setWordWrap(True)
            layout.addWidget(label)
        else:
            layout.addWidget(body)
        layout.addStretch(1)


class DashboardPage(QWidget):
    open_platform_explorer = Signal()
    open_platform = Signal(int)
    open_ship_viewer = open_platform_explorer  # Compatibility alias.

    def __init__(self, services: ApplicationServices) -> None:
        super().__init__()
        self._services = services
        self._settings = QSettings()

        platform_count = services.catalog.count()
        profile_count = services.catalog.count_profiles()
        faction_count = len(services.catalog.list_factions())
        system = services.game_systems.get(services.game_systems.default_id)

        title = QLabel("Dee's Fighting Ships")
        title.setObjectName("dashboardTitle")
        subtitle = QLabel(f"Tactical Reference System — {system.display_name}")
        subtitle.setObjectName("dashboardSubtitle")

        continue_box = QWidget()
        continue_layout = QVBoxLayout(continue_box)
        continue_layout.setContentsMargins(0, 0, 0, 0)
        last_id = self._settings.value("recent_platforms/last_id", 0, type=int)
        if last_id:
            try:
                detail = services.platform_details.get(last_id)
                name = detail.name
                faction = detail.faction_name
                button = QPushButton(f"{name}\n{faction}")
                button.setObjectName("continueButton")
                button.clicked.connect(lambda _checked=False, sid=last_id: self.open_platform.emit(sid))
                continue_layout.addWidget(button)
            except Exception:
                continue_layout.addWidget(QLabel("Open Platform Explorer to begin browsing."))
        else:
            continue_layout.addWidget(QLabel("Open Platform Explorer to begin browsing."))

        recent_box = QWidget()
        recent_layout = QVBoxLayout(recent_box)
        recent_layout.setContentsMargins(0, 0, 0, 0)
        ids = self._settings.value("recent_platforms/ids", [], type=list) or []
        added = 0
        for raw_id in ids[:5]:
            try:
                ship_id = int(raw_id)
                detail = services.platform_details.get(ship_id)
            except Exception:
                continue
            button = QPushButton(detail.name)
            button.setObjectName("recentPlatformButton")
            button.clicked.connect(lambda _checked=False, sid=ship_id: self.open_platform.emit(sid))
            recent_layout.addWidget(button)
            added += 1
        if not added:
            recent_layout.addWidget(QLabel("Recently opened platforms will appear here."))


        favorite_box = QWidget()
        favorite_layout = QVBoxLayout(favorite_box)
        favorite_layout.setContentsMargins(0, 0, 0, 0)
        favorite_ids = self._settings.value("favorite_platforms/ids", [], type=list) or []
        favorite_added = 0
        for raw_id in favorite_ids[:5]:
            try:
                ship_id = int(raw_id)
                detail = services.platform_details.get(ship_id)
            except Exception:
                continue
            button = QPushButton(f"★ {detail.name}")
            button.setObjectName("recentPlatformButton")
            button.clicked.connect(lambda _checked=False, sid=ship_id: self.open_platform.emit(sid))
            favorite_layout.addWidget(button)
            favorite_added += 1
        if not favorite_added:
            favorite_layout.addWidget(QLabel("Mark platforms as favorites in Platform Explorer."))

        database_body = (
            f"{platform_count:,} platforms\n"
            f"{profile_count:,} profiles\n"
            f"{faction_count:,} factions\n\n"
            "Current database loaded successfully."
        )
        themes = services.documents.list_styles()
        theme_names = "\n".join(f"• {style.label}" for style in themes)
        theme_body = theme_names or "No presentation themes installed."

        explorer = QPushButton("Open Platform Explorer")
        explorer.setObjectName("primaryDashboardAction")
        explorer.clicked.connect(self.open_platform_explorer.emit)

        cards = QGridLayout()
        cards.setHorizontalSpacing(18)
        cards.setVerticalSpacing(18)
        cards.addWidget(_DashboardCard("Continue Working", continue_box), 0, 0)
        cards.addWidget(_DashboardCard("Recent Platforms", recent_box), 0, 1)
        cards.addWidget(_DashboardCard("Favorite Platforms", favorite_box), 1, 0)
        cards.addWidget(_DashboardCard("Database Status", database_body), 1, 1)
        cards.addWidget(_DashboardCard("Installed Presentation Themes", theme_body), 2, 0, 1, 2)
        cards.setColumnStretch(0, 1)
        cards.setColumnStretch(1, 1)

        top = QHBoxLayout()
        heading = QVBoxLayout()
        heading.addWidget(title)
        heading.addWidget(subtitle)
        top.addLayout(heading)
        top.addStretch(1)
        top.addWidget(explorer, alignment=Qt.AlignmentFlag.AlignVCenter)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 28)
        layout.addLayout(top)
        layout.addSpacing(20)
        layout.addLayout(cards)
        layout.addStretch(1)

    def refresh_recent(self) -> None:
        """Dashboard content is reconstructed on the next application launch.

        Kept as an explicit hook so a future live dashboard model can refresh in place.
        """
