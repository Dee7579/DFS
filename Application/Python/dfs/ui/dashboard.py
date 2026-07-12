"""Initial DFS application dashboard."""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QGridLayout, QLabel, QPushButton, QVBoxLayout, QWidget


class DashboardPage(QWidget):
    open_ship_viewer = Signal()

    def __init__(self) -> None:
        super().__init__()
        title = QLabel("Dee's Fighting Ships")
        title.setObjectName("dashboardTitle")
        subtitle = QLabel("Babylon 5: A Call to Arms — Desktop Application")
        subtitle.setObjectName("dashboardSubtitle")

        ship_viewer = QPushButton("Ship Viewer\nBrowse platforms, profiles, traits and weapons")
        ship_viewer.setObjectName("moduleButton")
        ship_viewer.clicked.connect(self.open_ship_viewer.emit)

        grid = QGridLayout()
        grid.addWidget(ship_viewer, 0, 0)
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
        layout.addSpacing(28)
        layout.addLayout(grid)
        layout.addStretch(2)
