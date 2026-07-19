"""Configuration dialog for Drakh Huge Hangars."""
from __future__ import annotations

from collections import Counter

from PySide6.QtWidgets import (
    QDialog, QDialogButtonBox, QGridLayout, QLabel, QSpinBox, QVBoxLayout,
)


class HugeHangarsDialog(QDialog):
    def __init__(self, parent_name: str, capacity: int, candidates, selected_profile_ids, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Configure Huge Hangars - {parent_name}")
        self.resize(620, 420)
        self._capacity = int(capacity)
        self._candidates = tuple(candidates)
        selected = Counter(int(value) for value in selected_profile_ids)
        self._spins: dict[int, tuple[QSpinBox, int]] = {}

        layout = QVBoxLayout(self)
        intro = QLabel(
            "Select the ships embarked in this vessel's Huge Hangars. Embarked ships cost no Fleet Allocation Points, "
            "cannot start deployed, and each receives its own ship sheet."
        )
        intro.setWordWrap(True)
        layout.addWidget(intro)

        grid = QGridLayout()
        grid.addWidget(QLabel("Embarked platform"), 0, 0)
        grid.addWidget(QLabel("Slots each"), 0, 1)
        grid.addWidget(QLabel("Quantity"), 0, 2)
        for row, candidate in enumerate(self._candidates, start=1):
            profile_id, name, slot_cost = candidate
            grid.addWidget(QLabel(name), row, 0)
            grid.addWidget(QLabel(str(slot_cost)), row, 1)
            spin = QSpinBox()
            spin.setRange(0, max(1, self._capacity // max(1, slot_cost)))
            spin.setValue(selected.get(profile_id, 0))
            spin.valueChanged.connect(self._refresh)
            grid.addWidget(spin, row, 2)
            self._spins[int(profile_id)] = (spin, int(slot_cost))
        layout.addLayout(grid)

        self.status = QLabel()
        self.status.setWordWrap(True)
        layout.addWidget(self.status)
        layout.addStretch(1)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        self._ok = buttons.button(QDialogButtonBox.StandardButton.Ok)
        self._refresh()

    def slots_used(self) -> int:
        return sum(spin.value() * cost for spin, cost in self._spins.values())

    def _refresh(self) -> None:
        used = self.slots_used()
        remaining = self._capacity - used
        self.status.setText(f"Slots used: {used} / {self._capacity}    |    Remaining: {remaining}")
        self._ok.setEnabled(used <= self._capacity)

    def selected_profile_ids(self) -> tuple[int, ...]:
        result: list[int] = []
        for profile_id, (spin, _cost) in self._spins.items():
            result.extend([profile_id] * spin.value())
        return tuple(result)
