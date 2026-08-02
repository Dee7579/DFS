"""About dialog for Dee's Fighting Ships."""

from __future__ import annotations

import platform
import sqlite3

from PySide6 import __version__ as pyside_version
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialog, QDialogButtonBox, QGridLayout, QLabel, QVBoxLayout

from dfs.bootstrap import ApplicationServices


APP_VERSION = "2.4.0-alpha27"


class AboutDialog(QDialog):
    def __init__(self, services: ApplicationServices, database_label: str, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("About Dee's Fighting Ships")
        self.setModal(True)
        self.setMinimumWidth(520)

        platform_count = services.catalog.count()
        profile_count = services.catalog.count_profiles()
        faction_count = len(services.catalog.list_factions())
        style_count = len(services.documents.list_styles())

        title = QLabel("Dee's Fighting Ships")
        title.setObjectName("aboutTitle")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle = QLabel("Tactical Reference System")
        subtitle.setObjectName("aboutSubtitle")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        system = services.game_systems.get(services.game_systems.default_id)
        game = QLabel(system.display_name)
        game.setAlignment(Qt.AlignmentFlag.AlignCenter)

        stats = QGridLayout()
        rows = (
            ("Version", APP_VERSION),
            ("Platforms", f"{platform_count:,}"),
            ("Profiles", f"{profile_count:,}"),
            ("Factions", f"{faction_count:,}"),
            ("PDF styles installed", str(style_count)),
            ("Database", database_label),
            ("Python", platform.python_version()),
            ("PySide", pyside_version),
            ("SQLite", sqlite3.sqlite_version),
        )
        for row, (caption, value) in enumerate(rows):
            left = QLabel(caption)
            left.setObjectName("aboutCaption")
            right = QLabel(value)
            right.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            stats.addWidget(left, row, 0)
            stats.addWidget(right, row, 1)

        credit = QLabel(
            "Developed by Dewayne Harris\n"
            "Architecture and software engineering with OpenAI ChatGPT"
        )
        credit.setObjectName("aboutCredit")
        credit.setAlignment(Qt.AlignmentFlag.AlignCenter)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        buttons.accepted.connect(self.accept)

        layout = QVBoxLayout(self)
        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addWidget(game)
        layout.addSpacing(16)
        layout.addLayout(stats)
        layout.addSpacing(16)
        layout.addWidget(credit)
        layout.addWidget(buttons)
