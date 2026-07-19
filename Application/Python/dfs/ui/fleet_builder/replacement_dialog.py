"""Inline fleet-craft replacement editor."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from PySide6.QtWidgets import (
    QDialog, QDialogButtonBox, QFormLayout, QGroupBox, QLabel, QSpinBox, QVBoxLayout, QWidget,
)

from dfs.domain.fleet.replacements import ReplacementOpportunity


class CraftReplacementDialog(QDialog):
    def __init__(
        self,
        parent_name: str,
        parent_quantity: int,
        opportunities: tuple[ReplacementOpportunity, ...],
        current: Mapping[str, Mapping[str, int]],
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle(f"Configure Air Group - {parent_name}")
        self.resize(560, 420)
        self._opportunities = opportunities
        self._spins: dict[tuple[str, int], QSpinBox] = {}

        root = QVBoxLayout(self)
        intro = QLabel(
            f"<b>Configure Air Group</b><br>{parent_name}<br><br>"
            "Allocate standard flights to legal replacements. Unassigned flights remain standard."
        )
        intro.setWordWrap(True)
        root.addWidget(intro)

        for opportunity in opportunities:
            total = opportunity.source_quantity * parent_quantity
            group = QGroupBox(f"Standard complement: {total} {opportunity.source_printed_name}")
            form = QFormLayout(group)
            source_current = current.get(opportunity.source_printed_name, {})
            for resolved in opportunity.targets:
                spin = QSpinBox()
                spin.setRange(0, total)
                spin.setValue(int(source_current.get(str(resolved.profile_id), 0)))
                label = resolved.platform_name
                notes = []
                if resolved.target.minimum_year is not None:
                    notes.append(f"{resolved.target.minimum_year}+")
                if resolved.target.patrol_group_size:
                    notes.append(f"up to {resolved.target.patrol_group_size} per Patrol choice")
                if resolved.target.carries_parent_troop:
                    notes.append("carries 1 parent Troop")
                if notes:
                    label += " (" + "; ".join(notes) + ")"
                form.addRow(label, spin)
                self._spins[(opportunity.source_printed_name, resolved.profile_id)] = spin
            source_note = QLabel(
                f"Source: {opportunity.source_book}, p. {opportunity.source_page}."
                + (" All Starfuries must change together when selecting another Starfury type." if opportunity.all_or_none else "")
            )
            source_note.setWordWrap(True)
            form.addRow(source_note)
            root.addWidget(group)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self._validate_and_accept)
        buttons.rejected.connect(self.reject)
        root.addWidget(buttons)

    def _validate_and_accept(self) -> None:
        for opportunity in self._opportunities:
            total = opportunity.source_quantity
            # The caller supplies multiplied quantities in source_quantity when needed.
            selected = sum(
                spin.value()
                for (source, _), spin in self._spins.items()
                if source == opportunity.source_printed_name
            )
            # Actual total validation is repeated by the rule engine; this prevents the common UI mistake.
            max_value = max((spin.maximum() for (source, _), spin in self._spins.items() if source == opportunity.source_printed_name), default=total)
            if selected > max_value:
                from PySide6.QtWidgets import QMessageBox
                QMessageBox.warning(self, "Configure Air Group", f"Only {max_value} {opportunity.source_printed_name} flights are included.")
                return
            if opportunity.all_or_none and selected not in (0, max_value):
                # Breaching Pods may replace any number; all-or-none only applies when changing to a Starfury.
                paid_or_fighter = [
                    spin.value() for (source, profile_id), spin in self._spins.items()
                    if source == opportunity.source_printed_name
                    and next((t for t in opportunity.targets if t.profile_id == profile_id), None)
                    and "breaching" not in next(t for t in opportunity.targets if t.profile_id == profile_id).platform_name.casefold()
                ]
                fighter_total = sum(paid_or_fighter)
                if fighter_total not in (0, max_value):
                    from PySide6.QtWidgets import QMessageBox
                    QMessageBox.warning(self, "Configure Air Group", "Early Years Starfuries must all be replaced by the same alternate Starfury type.")
                    return
        self.accept()

    def selections(self) -> dict[str, dict[int, int]]:
        result: dict[str, dict[int, int]] = {}
        for (source, profile_id), spin in self._spins.items():
            if spin.value() > 0:
                result.setdefault(source, {})[profile_id] = spin.value()
        return result

    def patrol_costs(self) -> dict[str, int]:
        result: dict[str, int] = {}
        for opportunity in self._opportunities:
            total = 0
            for target in opportunity.targets:
                quantity = self._spins[(opportunity.source_printed_name, target.profile_id)].value()
                total += target.target.patrol_choices(quantity)
            result[opportunity.source_printed_name] = total
        return result
