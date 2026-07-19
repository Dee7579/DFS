"""Earth Alliance missile-loadout editor."""
from __future__ import annotations

from typing import Mapping

from PySide6.QtWidgets import QComboBox, QDialog, QDialogButtonBox, QFormLayout, QLabel, QVBoxLayout, QWidget

from dfs.domain.fleet.ordnance import MissileRackOpportunity


class MissileLoadoutDialog(QDialog):
    def __init__(
        self,
        platform_name: str,
        opportunities: tuple[MissileRackOpportunity, ...],
        current: Mapping[str, str],
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle(f"Configure Ordnance - {platform_name}")
        self.resize(620, 330)
        self._combos: dict[str, QComboBox] = {}

        root = QVBoxLayout(self)
        heading = QLabel(f"<b>Configure Ordnance</b><br>{platform_name}")
        root.addWidget(heading)
        intro = QLabel(
            "Choose one missile type for each missile rack. Each rack retains its printed arc, Attack Dice, "
            "and Slow-Loading trait where applicable. Variants are limited by the selected fleet year."
        )
        intro.setWordWrap(True)
        root.addWidget(intro)

        form = QFormLayout()
        for opportunity in opportunities:
            combo = QComboBox()
            combo.addItem(
                f"Printed standard ({opportunity.standard_range}\"; {opportunity.standard_traits})",
                "standard",
            )
            for variant in opportunity.variants:
                if variant.variant_id == "standard":
                    continue
                details = f'{variant.range_value}\"'
                if variant.traits:
                    details += f"; {variant.traits}"
                details += f"; {variant.minimum_year}+"
                combo.addItem(f"{variant.display_name} ({details})", variant.variant_id)
            selected = current.get(opportunity.rack_key, "standard")
            index = combo.findData(selected)
            combo.setCurrentIndex(max(0, index))
            self._combos[opportunity.rack_key] = combo
            form.addRow(opportunity.label, combo)
        root.addLayout(form)

        source = QLabel("Source: B5 ACTA Fleet Lists, Missile Variants, pp. 15-16.")
        source.setWordWrap(True)
        root.addWidget(source)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        root.addWidget(buttons)

    def selections(self) -> dict[str, str]:
        return {rack_key: str(combo.currentData()) for rack_key, combo in self._combos.items()}
