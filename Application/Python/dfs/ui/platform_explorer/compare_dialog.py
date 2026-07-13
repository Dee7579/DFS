"""Readable side-by-side comparison for two DFS platforms."""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QApplication,
    QAbstractItemView,
    QDialog,
    QDialogButtonBox,
    QHeaderView,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)

from dfs.domain.catalog import PlatformDetail, PlatformProfile


def _profile(platform: PlatformDetail) -> PlatformProfile | None:
    return platform.profiles[0] if platform.profiles else None


def _text(value: object) -> str:
    return str(value) if value not in (None, "") else "—"


def _weapon_text(weapon) -> str:
    traits = f" — {weapon.traits}" if weapon.traits else ""
    return f'{weapon.arc}  {weapon.name}  {weapon.range_value}"  AD {weapon.attack_dice}{traits}'


class PlatformCompareDialog(QDialog):
    """A single scrolling comparison table that emphasizes differences."""


    def __init__(self, left: PlatformDetail, right: PlatformDetail, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle(f"Compare — {left.name} and {right.name}")
        self._configure_colors()
        self.resize(1120, 800)

        layout = QVBoxLayout(self)
        heading = QLabel(f"{left.name}  vs  {right.name}")
        heading.setObjectName("platformTitle")
        heading.setWordWrap(True)
        layout.addWidget(heading)

        left_profile = _profile(left)
        right_profile = _profile(right)
        if left_profile is None or right_profile is None:
            layout.addWidget(QLabel("Both platforms must have at least one profile to compare."))
        else:
            layout.addWidget(
                self._comparison_table(left, left_profile, right, right_profile),
                1,
            )

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(self.reject)
        buttons.accepted.connect(self.accept)
        layout.addWidget(buttons)


    def _configure_colors(self) -> None:
        """Choose comparison colors that remain readable in light and dark modes."""
        palette = QApplication.palette()
        base = palette.color(palette.ColorRole.Base)
        text = palette.color(palette.ColorRole.Text)
        dark_mode = base.lightness() < 128

        if dark_mode:
            self.section_background = QColor("#334155")
            self.difference_background = QColor("#164e63")
            self.section_foreground = QColor("#f8fafc")
            self.cell_foreground = QColor("#f1f5f9")
        else:
            self.section_background = QColor("#d9e1ea")
            self.difference_background = QColor("#ecfeff")
            self.section_foreground = QColor("#111827")
            self.cell_foreground = text

    def _comparison_table(
        self,
        left: PlatformDetail,
        lp: PlatformProfile,
        right: PlatformDetail,
        rp: PlatformProfile,
    ) -> QTableWidget:
        attributes = (
            ("Faction", left.faction_name, right.faction_name),
            ("Fleet / Era", lp.fleet_name, rp.fleet_name),
            ("Priority", lp.priority_level, rp.priority_level),
            ("Initiative", lp.initiative, rp.initiative),
            ("Speed", lp.speed, rp.speed),
            ("Turn", lp.turn, rp.turn),
            ("Hull", lp.hull, rp.hull),
            ("Damage", lp.damage, rp.damage),
            ("Crew", lp.crew, rp.crew),
            ("Troops", lp.troops, rp.troops),
            ("Craft", lp.craft, rp.craft),
            ("In Service", lp.in_service, rp.in_service),
        )
        weapon_count = max(len(lp.weapons), len(rp.weapons), 1)
        total_rows = 1 + len(attributes) + 1 + 1 + 1 + weapon_count

        table = QTableWidget(total_rows, 3)
        table.setHorizontalHeaderLabels(("Attribute", left.name, right.name))
        table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        table.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        table.setAlternatingRowColors(True)
        table.setWordWrap(True)
        table.verticalHeader().setVisible(False)
        table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)

        row = 0
        self._set_section(table, row, "Platform Profile")
        row += 1
        for label, left_value, right_value in attributes:
            self._set_row(table, row, label, _text(left_value), _text(right_value))
            row += 1

        self._set_section(table, row, "Platform Traits")
        row += 1
        self._set_row(
            table,
            row,
            "Traits",
            "\n".join(lp.traits) or "—",
            "\n".join(rp.traits) or "—",
        )
        row += 1

        self._set_section(table, row, "Weapons")
        row += 1
        left_weapons = [_weapon_text(w) for w in lp.weapons]
        right_weapons = [_weapon_text(w) for w in rp.weapons]
        for index in range(weapon_count):
            self._set_row(
                table,
                row,
                str(index + 1),
                left_weapons[index] if index < len(left_weapons) else "—",
                right_weapons[index] if index < len(right_weapons) else "—",
            )
            row += 1

        table.resizeRowsToContents()
        table.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        return table

    def _set_section(self, table: QTableWidget, row: int, title: str) -> None:
        item = QTableWidgetItem(title)
        font = item.font()
        font.setBold(True)
        item.setFont(font)
        item.setBackground(self.section_background)
        item.setForeground(self.section_foreground)
        item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        table.setItem(row, 0, item)
        table.setSpan(row, 0, 1, 3)

    def _set_row(self, table: QTableWidget, row: int, label: str, left: str, right: str) -> None:
        different = left != right
        for column, value in enumerate((label, left, right)):
            item = QTableWidgetItem(value)
            item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            item.setForeground(self.cell_foreground)
            if column == 0:
                font = item.font()
                font.setBold(True)
                item.setFont(font)
            if different and column in (1, 2):
                item.setBackground(self.difference_background)
            table.setItem(row, column, item)
