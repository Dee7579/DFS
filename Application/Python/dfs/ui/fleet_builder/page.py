"""DFS Fleet Builder workspace.

The widget remains a thin presentation layer. Fleet mutation, cost calculation,
validation, and persistence are delegated to shared services.
"""
from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
from dataclasses import replace
from html import escape
from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QBrush, QPalette
from PySide6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QComboBox,
    QDialog,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMenu,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from dfs.bootstrap import ApplicationContext
from dfs.domain.catalog import PlatformFilter, PlatformProfile
from dfs.domain.fleet import Fleet, ValidationSeverity
from dfs.domain.fleet.replacements import replacement_map
from dfs.domain.fleet.ordnance import missile_loadout_map
from dfs.domain.fleet.included_craft import normalize_craft_name, parse_included_craft
from dfs.domain.fleet.huge_hangars import capacity_from_traits, embarked_profile_ids
from dfs.domain.fleet.grouped_purchases import grouped_purchase_label, grouped_purchase_size, purchased_choice_count
from dfs.domain.fleet.priority import (
    PRIORITIES,
    PRIORITY_INDEX,
    can_add_ancient,
    can_add_priority,
    format_unaffordable_choice,
)
from dfs.ui.platform_explorer.compare_dialog import PlatformCompareDialog
from dfs.ui.fleet_builder.print_dialog import FleetPrintDialog
from dfs.ui.fleet_builder.replacement_dialog import CraftReplacementDialog
from dfs.ui.fleet_builder.ordnance_dialog import MissileLoadoutDialog
from dfs.ui.fleet_builder.huge_hangars_dialog import HugeHangarsDialog
from dfs.services.fleet.b5_allied_contingents import definition_for, permitted_profile, is_allied_profile
from dfs.services.fleet.b5_composite_fleets import source_fleet_name


class FleetRosterTable(QTableWidget):
    """Roster table that requests domain-level parent-entry reordering.

    Included-craft rows never move independently; dragging any row in a parent
    group resolves to the purchased parent entry.
    """

    move_requested = Signal(str, object, bool)

    def __init__(self, rows: int, columns: int, parent: QWidget | None = None) -> None:
        super().__init__(rows, columns, parent)
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDropIndicatorShown(True)
        self.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        self.setDragDropOverwriteMode(False)
        self._drag_entry_id: str | None = None

    def startDrag(self, supported_actions) -> None:  # noqa: N802 - Qt override
        self._drag_entry_id = self._parent_entry_id(self.currentRow())
        if self._drag_entry_id:
            super().startDrag(supported_actions)

    def _parent_entry_id(self, row: int) -> str | None:
        while row >= 0:
            item = self.item(row, 0)
            if item is not None:
                entry_id = item.data(Qt.ItemDataRole.UserRole)
                if entry_id:
                    return str(entry_id)
            row -= 1
        return None

    def dropEvent(self, event) -> None:  # noqa: N802 - Qt override
        source_id = self._drag_entry_id or self._parent_entry_id(self.currentRow())
        self._drag_entry_id = None
        if not source_id:
            event.ignore()
            return
        position = event.position().toPoint()
        target_row = self.rowAt(position.y())
        if target_row < 0:
            self.move_requested.emit(source_id, None, True)
            event.acceptProposedAction()
            return
        target_id = self._parent_entry_id(target_row)
        if not target_id or target_id == source_id:
            event.ignore()
            return
        rect = self.visualItemRect(self.item(target_row, 0))
        before = position.y() < rect.center().y()
        self.move_requested.emit(source_id, target_id, before)
        event.acceptProposedAction()


class FleetBuilderPage(QWidget):
    """Create, validate, save, and load fleets using shared services."""

    open_platform_requested = Signal(int)

    def __init__(self, context: ApplicationContext, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._context = context
        self._fleet: Fleet | None = None
        self._available_profiles: list[tuple[int, str, PlatformProfile]] = []
        self._entry_profiles: dict[str, PlatformProfile] = {}
        self._current_path: Path | None = None
        self._building_controls = False
        self._compare_anchor: tuple[int, int, str] | None = None
        self._craft_resolution_cache: dict[tuple[str, int | None], tuple[int, str, PlatformProfile] | None] = {}
        self._roster_sort_column: int | None = None
        self._roster_sort_descending = False

        self._build_ui()
        self._populate_construction_profiles()
        self._populate_factions()
        self.new_fleet()

    def _build_ui(self) -> None:
        title = QLabel("Fleet Builder")
        title.setObjectName("pageTitle")
        subtitle = QLabel("Build, validate, save, and load fleets using the selected construction rules.")
        subtitle.setObjectName("pageSubtitle")

        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Fleet name")
        self.profile_combo = QComboBox()
        self.faction_combo = QComboBox()
        self.fleet_combo = QComboBox()
        self.year_spin = QSpinBox()
        self.year_spin.setRange(0, 9999)
        self.year_spin.setSpecialValueText("Any year")
        self.priority_combo = QComboBox()
        self.priority_combo.addItems(PRIORITIES)
        self.priority_combo.setCurrentText("Raid")
        self.fap_spin = QSpinBox()
        self.fap_spin.setRange(1, 99)
        self.fap_spin.setValue(5)

        form = QFormLayout()
        form.setContentsMargins(8, 8, 8, 8)
        form.addRow("Fleet name", self.name_edit)
        form.addRow("Construction profile", self.profile_combo)
        form.addRow("Faction", self.faction_combo)
        form.addRow("Fleet / Era", self.fleet_combo)
        form.addRow("Year", self.year_spin)
        form.addRow("Scenario priority", self.priority_combo)
        form.addRow("Fleet Allocation Points", self.fap_spin)

        setup_group = QGroupBox("Fleet Setup")
        setup_group.setLayout(form)

        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Search legal platforms…")
        self.allied_fleet_combo = QComboBox()
        self.allied_fleet_combo.addItem("None", None)
        self.allied_fleet_combo.currentIndexChanged.connect(self._allied_fleet_changed)
        self.construction_guidance_label = QLabel("")
        self.construction_guidance_label.setObjectName("pageSubtitle")
        self.construction_guidance_label.setWordWrap(True)
        self.available_list = QListWidget()
        self.available_list.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.available_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.available_list.customContextMenuRequested.connect(self._show_available_context_menu)
        self.available_list.itemDoubleClicked.connect(lambda _: self._add_selected_profile())
        self.available_list.currentItemChanged.connect(self._available_selection_changed)
        self.add_button = QPushButton("Add to Fleet →")
        self.add_button.clicked.connect(self._add_selected_profile)
        self.compare_button = QPushButton("Compare…")
        self.compare_button.clicked.connect(self._compare_selected)

        available_buttons = QHBoxLayout()
        available_buttons.addWidget(self.compare_button)
        available_buttons.addWidget(self.add_button, 1)

        available_layout = QVBoxLayout()
        available_layout.setContentsMargins(8, 8, 8, 8)
        available_layout.addWidget(self.search_edit)
        allied_row = QHBoxLayout()
        allied_row.addWidget(QLabel("Allied Fleet"))
        allied_row.addWidget(self.allied_fleet_combo, 1)
        available_layout.addLayout(allied_row)
        available_layout.addWidget(self.construction_guidance_label)
        available_layout.addWidget(self.available_list, 1)
        available_layout.addLayout(available_buttons)
        available_group = QGroupBox("Available Platforms")
        available_group.setLayout(available_layout)

        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(10)
        left_layout.addWidget(setup_group)
        left_layout.addWidget(available_group, 1)

        self.roster_table = FleetRosterTable(0, 5)
        self.roster_table.setHorizontalHeaderLabels(("Platform", "Ship Name", "Priority", "Qty", ""))
        self.roster_table.verticalHeader().setVisible(False)
        self.roster_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.roster_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.roster_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.roster_table.customContextMenuRequested.connect(self._show_roster_context_menu)
        self.roster_table.cellDoubleClicked.connect(self._roster_double_clicked)
        self.roster_table.move_requested.connect(self._move_roster_entry)
        header = self.roster_table.horizontalHeader()
        header.setSectionsClickable(True)
        header.setSortIndicatorShown(False)
        header.sectionClicked.connect(self._roster_header_clicked)
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)

        self.summary_label = QLabel("No fleet")
        self.summary_label.setWordWrap(True)
        self.validation_box = QTextEdit()
        self.validation_box.setReadOnly(True)
        self.validation_box.setMinimumHeight(130)

        roster_layout = QVBoxLayout()
        roster_layout.setContentsMargins(8, 8, 8, 8)
        roster_layout.addWidget(self.roster_table, 1)
        roster_layout.addWidget(self.summary_label)
        roster_layout.addWidget(QLabel("Construction Messages"))
        roster_layout.addWidget(self.validation_box)
        roster_group = QGroupBox("Fleet Roster")
        roster_group.setLayout(roster_layout)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(left_panel)
        splitter.addWidget(roster_group)
        splitter.setStretchFactor(0, 2)
        splitter.setStretchFactor(1, 5)
        splitter.setChildrenCollapsible(False)
        splitter.setSizes([470, 1050])

        new_button = QPushButton("New")
        open_button = QPushButton("Open…")
        save_button = QPushButton("Save")
        save_as_button = QPushButton("Save As…")
        print_button = QPushButton("Print Fleet…")
        new_button.clicked.connect(self.new_fleet)
        open_button.clicked.connect(self.open_fleet)
        save_button.clicked.connect(self.save_fleet)
        save_as_button.clicked.connect(lambda: self.save_fleet(save_as=True))
        print_button.clicked.connect(self.print_fleet)
        file_buttons = QHBoxLayout()
        file_buttons.addStretch(1)
        file_buttons.addWidget(print_button)
        file_buttons.addSpacing(18)
        file_buttons.addWidget(new_button)
        file_buttons.addWidget(open_button)
        file_buttons.addWidget(save_button)
        file_buttons.addWidget(save_as_button)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 18, 24, 18)
        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addWidget(splitter, 1)
        layout.addLayout(file_buttons)

        self.search_edit.textChanged.connect(self._refresh_available)
        self.name_edit.editingFinished.connect(self._sync_fleet_from_controls)
        self.profile_combo.currentIndexChanged.connect(self._sync_fleet_from_controls)
        self.faction_combo.currentIndexChanged.connect(self._faction_changed)
        self.fleet_combo.currentIndexChanged.connect(self._sync_fleet_from_controls)
        self.year_spin.valueChanged.connect(self._sync_fleet_from_controls)
        self.priority_combo.currentTextChanged.connect(self._sync_fleet_from_controls)
        self.fap_spin.valueChanged.connect(self._sync_fleet_from_controls)

    def _populate_construction_profiles(self) -> None:
        self.profile_combo.clear()
        for profile in self._context.fleets.profiles():
            self.profile_combo.addItem(profile.display_name, profile.profile_id)

    def _populate_factions(self) -> None:
        self.faction_combo.clear()
        self.faction_combo.addItem("Select faction…", None)
        for option in self._context.catalog.list_factions():
            fleet_options = self._context.catalog.list_fleets(int(option.id))
            has_selectable_profiles = any(
                self._context.catalog.search(
                    PlatformFilter(fleet_list_ids=(int(fleet.id),), limit=1)
                )
                for fleet in fleet_options
            )
            if has_selectable_profiles:
                self.faction_combo.addItem(option.label, int(option.id))

    def _populate_fleets(self, faction_id: int | None) -> None:
        self.fleet_combo.clear()
        if faction_id is None:
            self.fleet_combo.addItem("Select faction first…", None)
            self.fleet_combo.setEnabled(False)
            return

        options = self._context.catalog.list_fleets(faction_id)
        if len(options) == 1:
            option = options[0]
            self.fleet_combo.addItem(option.label, int(option.id))
            self.fleet_combo.setCurrentIndex(0)
            self.fleet_combo.setEnabled(False)
            self.fleet_combo.setToolTip("This faction has one fleet list, so it is selected automatically.")
            return

        self.fleet_combo.addItem("Select fleet / era…", None)
        for option in options:
            self.fleet_combo.addItem(option.label, int(option.id))
        self.fleet_combo.setEnabled(True)
        self.fleet_combo.setToolTip("Select the fleet or era used for this force.")

    def print_fleet(self) -> None:
        if self._fleet is None or not self._fleet.entries:
            QMessageBox.information(self, "Print Fleet", "Add at least one platform before printing.")
            return
        dialog = FleetPrintDialog(self._context, self._fleet, self._current_path, self)
        if dialog.exec() == QDialog.DialogCode.Accepted and dialog.printed_item_keys:
            timestamp = datetime.now(timezone.utc).isoformat()
            self._fleet = self._context.fleet_prints.mark_printed(
                self._fleet, dialog.printed_item_keys, timestamp
            )
            self._context.status.set("Selected fleet sheets sent to printer")

    def new_fleet(self) -> None:
        self._current_path = None
        self._compare_anchor = None
        self._fleet = self._context.fleets.create_fleet(
            name="Untitled Fleet",
            construction_profile_id=self.profile_combo.currentData() or "b5_acta_priority_standard",
            faction_id=self.faction_combo.currentData(),
            fleet_list_id=self.fleet_combo.currentData(),
            selected_year=None,
            scenario_priority=self.priority_combo.currentText() or "Raid",
            fleet_allocation_points=self.fap_spin.value(),
        )
        self.name_edit.setText(self._fleet.name)
        self._entry_profiles.clear()
        self._refresh_available()
        self._refresh_roster()
        self._context.status.set("New fleet created")

    def _faction_changed(self) -> None:
        if self._building_controls:
            return
        self._populate_fleets(self.faction_combo.currentData())
        self._sync_fleet_from_controls()

    def _sync_fleet_from_controls(self) -> None:
        if self._building_controls or self._fleet is None:
            return
        metadata = dict(self._fleet.metadata)
        metadata["scenario_priority"] = self.priority_combo.currentText()
        metadata["fleet_allocation_points"] = self.fap_spin.value()
        selected_ally = self._selected_allied_fleet_id()
        if selected_ally is None:
            metadata.pop("allied_fleet_list_id", None)
        else:
            metadata["allied_fleet_list_id"] = selected_ally
        self._fleet = replace(
            self._fleet,
            name=self.name_edit.text().strip() or "Untitled Fleet",
            construction_profile_id=self.profile_combo.currentData() or "b5_acta_priority_standard",
            faction_id=self.faction_combo.currentData(),
            fleet_list_id=self.fleet_combo.currentData(),
            selected_year=self.year_spin.value() or None,
            metadata=metadata,
        )
        self._refresh_available()
        self._refresh_roster()

    def _selected_priority_counts(self) -> Counter[str]:
        counts: Counter[str] = Counter()
        if self._fleet is None:
            return counts
        for entry in self._fleet.entries:
            profile = self._context.platform_details.get_profile(entry.profile_id)
            if profile is not None and profile.priority_level in PRIORITIES:
                counts[profile.priority_level] += purchased_choice_count(entry.profile_id, entry.quantity, entry.options)
        return counts

    def _construction_mode(self) -> str:
        profile_id = self._fleet.construction_profile_id if self._fleet else (self.profile_combo.currentData() or "")
        if profile_id == "b5_acta_sandbox" or profile_id == "no_validation":
            return "sandbox"
        if profile_id == "b5_acta_priority_advisory":
            return "advisory"
        return "official"

    def _fleet_list_labels(self) -> dict[int, str]:
        labels: dict[int, str] = {}
        for faction in self._context.catalog.list_factions():
            for option in self._context.catalog.list_fleets(int(faction.id)):
                labels[int(option.id)] = option.label
        return labels

    def _selected_allied_fleet_id(self) -> int | None:
        value = self.allied_fleet_combo.currentData()
        return int(value) if value is not None else None

    def _inferred_allied_fleet_id(self) -> int | None:
        sources = self._allied_source_fleet_ids()
        if len(sources) == 1:
            return next(iter(sources))
        if self._fleet is not None:
            value = self._fleet.metadata.get("allied_fleet_list_id")
            if value is not None:
                try:
                    return int(value)
                except (TypeError, ValueError):
                    pass
        return None

    def _populate_allied_fleets(self) -> None:
        current = self._inferred_allied_fleet_id()
        definition = definition_for(self._fleet) if self._fleet else None
        mode = self._construction_mode()
        labels = self._fleet_list_labels()
        self.allied_fleet_combo.blockSignals(True)
        try:
            self.allied_fleet_combo.clear()
            self.allied_fleet_combo.addItem("None", None)
            if definition is not None and mode != "sandbox":
                for fleet_list_id in definition.allowed_fleet_list_ids:
                    self.allied_fleet_combo.addItem(labels.get(fleet_list_id, f"Fleet list {fleet_list_id}"), fleet_list_id)
            index = self.allied_fleet_combo.findData(current)
            self.allied_fleet_combo.setCurrentIndex(index if index >= 0 else 0)
        finally:
            self.allied_fleet_combo.blockSignals(False)
        enabled = bool(self._fleet and self._fleet.fleet_list_id and definition and mode != "sandbox")
        self.allied_fleet_combo.setEnabled(enabled)
        if mode == "sandbox":
            self.allied_fleet_combo.setToolTip("All platforms are already available in Open / Sandbox mode.")
        elif definition is None:
            self.allied_fleet_combo.setToolTip("This fleet has no official allied-contingent option.")
        else:
            self.allied_fleet_combo.setToolTip("Choose the single official allied fleet list to display.")

    def _allied_fleet_changed(self) -> None:
        if self._building_controls or self._fleet is None:
            return
        selected = self._selected_allied_fleet_id()
        existing = self._allied_source_fleet_ids()
        if existing and (selected is None or selected not in existing):
            labels = self._fleet_list_labels()
            current_names = ", ".join(labels.get(value, f"Fleet list {value}") for value in sorted(existing))
            answer = QMessageBox.question(
                self,
                "Change Allied Fleet",
                f"The roster contains allied ships from {current_names}.\n\n"
                "Remove those allied ships and change the Allied Fleet selection?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel,
                QMessageBox.StandardButton.Cancel,
            )
            if answer != QMessageBox.StandardButton.Yes:
                self._populate_allied_fleets()
                return
            for entry in tuple(self._fleet.entries):
                profile = self._context.platform_details.get_profile(entry.profile_id)
                if profile is not None and profile.fleet_list_id != self._fleet.fleet_list_id:
                    self._fleet = self._context.fleets.remove_entry(self._fleet, entry.entry_id)

        metadata = dict(self._fleet.metadata)
        if selected is None:
            metadata.pop("allied_fleet_list_id", None)
        else:
            metadata["allied_fleet_list_id"] = selected
        self._fleet = replace(self._fleet, metadata=metadata)
        self._refresh_roster()
        self._refresh_available()

    def _allied_source_fleet_ids(self) -> set[int]:
        if self._fleet is None or self._fleet.fleet_list_id is None:
            return set()
        return {
            profile.fleet_list_id
            for entry in self._fleet.entries
            if (profile := self._context.platform_details.get_profile(entry.profile_id)) is not None
            and profile.fleet_list_id != self._fleet.fleet_list_id
        }

    def _allied_guidance(self) -> str:
        if self._fleet is None or self._fleet.fleet_list_id is None:
            return "Select a fleet / era to begin."
        mode = self._construction_mode()
        if mode == "sandbox":
            return "Open / Sandbox mode — construction rules and platform filtering are disabled."
        definition = definition_for(self._fleet)
        if definition is None:
            return "This fleet has no standard allied-contingent option."
        source_id = self._selected_allied_fleet_id()
        if source_id is None:
            return "Allied contingent: none selected. Choose an Allied Fleet to display its platforms."
        source_name = self._fleet_list_labels().get(source_id, f"Fleet list {source_id}")
        return f"Allied contingent: {source_name}. Maximum allowance: one scenario-level FAP."

    def _eligible_profiles(self) -> list[tuple[int, str, PlatformProfile]]:
        if self._fleet is None or self._fleet.faction_id is None or self._fleet.fleet_list_id is None:
            return []
        mode = self._construction_mode()
        selected_ally = self._selected_allied_fleet_id() if mode != "sandbox" else None
        fleet_list_ids: tuple[int, ...] = () if mode == "sandbox" else (
            (self._fleet.fleet_list_id,) + ((selected_ally,) if selected_ally is not None else ())
        )
        filters = PlatformFilter(
            search_text=self.search_edit.text(),
            fleet_list_ids=fleet_list_ids,
            limit=5000 if mode == "sandbox" else 1000,
        )
        scenario = str(self._fleet.metadata.get("scenario_priority", "Raid"))
        scenario_index = PRIORITY_INDEX.get(scenario, PRIORITY_INDEX["Raid"])
        results: list[tuple[int, str, PlatformProfile]] = []
        for summary in self._context.catalog.search(filters):
            detail = self._context.platform_details.get(summary.ship_id)
            if detail is None:
                continue
            for profile in detail.profiles:
                if fleet_list_ids and profile.fleet_list_id not in fleet_list_ids:
                    continue
                if mode == "official" and profile.priority_level in PRIORITY_INDEX and PRIORITY_INDEX[profile.priority_level] > scenario_index:
                    continue
                if mode == "official" and self._fleet.selected_year is not None:
                    from dfs.domain.in_service import parse_in_service
                    if not parse_in_service(profile.in_service).includes(self._fleet.selected_year):
                        continue
                results.append((summary.ship_id, summary.name, profile))
        return results

    @staticmethod
    def _profile_tooltip(name: str, profile: PlatformProfile, availability_note: str = "") -> str:
        traits = ", ".join(profile.traits) if profile.traits else "None"
        weapons = []
        for weapon in profile.weapons:
            traits_text = f" — {escape(weapon.traits)}" if weapon.traits else ""
            weapons.append(
                f"{escape(weapon.arc)} &nbsp; {escape(weapon.name)} &nbsp; "
                f"{escape(weapon.range_value)}&quot; &nbsp; AD {escape(weapon.attack_dice)}{traits_text}"
            )
        weapon_text = "<br>".join(weapons) if weapons else "None"
        notes = list(profile.notes)
        purchase_size = grouped_purchase_size(profile.profile_id)
        if purchase_size > 1:
            notes.insert(0, f"Purchased in pairs. One {profile.priority_level} choice purchases {purchase_size} ships.")
        if any(str(trait).casefold() == "unique" for trait in profile.traits):
            notes.insert(0, "Unique. Maximum one per fleet.")
        notes_text = "<br>".join(f"• {escape(note)}" for note in notes) if notes else ""
        prefix = (f"{escape(availability_note).replace(chr(10), '<br>')}<br><br>" if availability_note else "")
        return (
            prefix
            + f"<b>{escape(name)}</b><br>"
            f"{escape(profile.fleet_name)} — {escape(profile.priority_level)}<br><br>"
            f"<b>Speed</b> {escape(profile.speed)} &nbsp;&nbsp; "
            f"<b>Turn</b> {escape(profile.turn)} &nbsp;&nbsp; "
            f"<b>Hull</b> {escape(profile.hull)}<br>"
            f"<b>Damage</b> {escape(profile.damage)} &nbsp;&nbsp; "
            f"<b>Crew</b> {escape(profile.crew)} &nbsp;&nbsp; "
            f"<b>Troops</b> {escape(profile.troops)}<br>"
            f"<b>In Service</b> {escape(profile.in_service)}<br>"
            f"<b>Craft</b> {escape(profile.craft or 'None')}<br><br>"
            f"<b>Traits</b><br>{escape(traits)}<br><br>"
            f"<b>Weapons</b><br>{weapon_text}"
            + (f"<br><br><b>Notes</b><br>{notes_text}" if notes_text else "")
        )

    def _refresh_available(self) -> None:
        self.available_list.clear()
        self._populate_allied_fleets()
        self._available_profiles = self._eligible_profiles()
        fleet_ready = bool(self._fleet and self._fleet.fleet_list_id)
        disabled_brush = QBrush(self.palette().color(QPalette.ColorRole.PlaceholderText))
        mode = self._construction_mode()

        for ship_id, name, profile in self._available_profiles:
            allowed, reason = self._can_add_profile(profile)
            allied_label = "  •  Allied" if self._fleet and is_allied_profile(self._fleet, profile) else ""
            advisory_label = "  •  Advisory" if mode == "advisory" and reason else ""
            displayed_fleet = source_fleet_name(profile.source_book, profile.fleet_name)
            item = QListWidgetItem(
                f"{name}\n{profile.priority_level}  •  {displayed_fleet}{allied_label}{advisory_label}  •  {profile.in_service}"
            )
            item.setData(Qt.ItemDataRole.UserRole, profile.profile_id)
            item.setData(Qt.ItemDataRole.UserRole + 1, ship_id)
            item.setData(Qt.ItemDataRole.UserRole + 2, allowed)
            note = reason
            if reason and not allowed:
                note = f"Unavailable — {reason}"
            elif reason and mode == "advisory":
                note = f"Rules advisory — {reason} This choice is allowed in Advisory mode."
            item.setToolTip(self._profile_tooltip(name, profile, note))
            if not allowed:
                item.setForeground(disabled_brush)
            self.available_list.addItem(item)

        self.available_list.setEnabled(fleet_ready)
        self.search_edit.setEnabled(fleet_ready)
        self.construction_guidance_label.setText(self._allied_guidance())
        self.add_button.setEnabled(False)
        self.compare_button.setEnabled(bool(self._available_profiles))
        if not fleet_ready:
            self.available_list.addItem("Select a fleet / era to view available platforms.")

    def _available_selection_changed(self, current: QListWidgetItem | None, _previous=None) -> None:
        affordable = bool(current and current.data(Qt.ItemDataRole.UserRole + 2))
        self.add_button.setEnabled(affordable)
        self.compare_button.setEnabled(bool(current and current.data(Qt.ItemDataRole.UserRole)))

    def _profile_name(self, profile_id: int) -> tuple[str, PlatformProfile | None]:
        profile = self._context.platform_details.get_profile(profile_id)
        if profile is None:
            return f"Profile {profile_id}", None
        for summary in self._context.catalog.search(PlatformFilter(fleet_list_ids=(profile.fleet_list_id,), limit=1000)):
            detail = self._context.platform_details.get(summary.ship_id)
            if detail and any(p.profile_id == profile_id for p in detail.profiles):
                return summary.name, profile
        return f"Profile {profile_id}", profile

    def _current_available(self) -> tuple[int, int, str] | None:
        item = self.available_list.currentItem()
        if item is None or item.data(Qt.ItemDataRole.UserRole) is None:
            return None
        return (
            int(item.data(Qt.ItemDataRole.UserRole + 1)),
            int(item.data(Qt.ItemDataRole.UserRole)),
            item.text().splitlines()[0],
        )

    def _add_selected_profile(self) -> None:
        if self._fleet is None or self._fleet.fleet_list_id is None:
            return
        item = self.available_list.currentItem()
        if item is None or not bool(item.data(Qt.ItemDataRole.UserRole + 2)):
            return
        profile_id = int(item.data(Qt.ItemDataRole.UserRole))
        self._fleet = self._context.fleets.add_grouped_profile(
            self._fleet, profile_id, grouped_purchase_size(profile_id)
        )
        self._refresh_roster()
        self._refresh_available()
        self._context.status.set("Platform added to fleet")

    def _show_available_context_menu(self, point) -> None:
        item = self.available_list.itemAt(point)
        if item is None or item.data(Qt.ItemDataRole.UserRole) is None:
            return
        self.available_list.setCurrentItem(item)
        menu = QMenu(self)
        add_action = menu.addAction("Add to Fleet")
        add_action.setEnabled(bool(item.data(Qt.ItemDataRole.UserRole + 2)))
        add_action.triggered.connect(self._add_selected_profile)
        menu.addSeparator()
        open_action = menu.addAction("Open in Platform Explorer")
        open_action.triggered.connect(self._open_selected_in_explorer)
        mark_action = menu.addAction("Mark for Comparison")
        mark_action.triggered.connect(self._mark_selected_for_comparison)
        compare_action = menu.addAction("Compare with Marked")
        compare_action.setEnabled(self._compare_anchor is not None)
        compare_action.triggered.connect(self._compare_selected)
        menu.exec(self.available_list.mapToGlobal(point))

    def _open_selected_in_explorer(self) -> None:
        selected = self._current_available()
        if selected:
            self.open_platform_requested.emit(selected[0])

    def _mark_selected_for_comparison(self) -> None:
        selected = self._current_available()
        if selected:
            self._compare_anchor = selected
            self._context.status.set(f"Comparison platform: {selected[2]}")

    def _detail_for_profile(self, ship_id: int, profile_id: int):
        detail = self._context.platform_details.get(ship_id)
        if detail is None:
            return None
        selected = next((p for p in detail.profiles if p.profile_id == profile_id), None)
        if selected is None:
            return detail
        return replace(detail, profiles=(selected, *tuple(p for p in detail.profiles if p.profile_id != profile_id)))

    def _compare_selected(self) -> None:
        selected = self._current_available()
        if selected is None:
            return
        if self._compare_anchor is None or self._compare_anchor[:2] == selected[:2]:
            self._compare_anchor = selected
            self._context.status.set(f"Select another platform, then choose Compare: {selected[2]}")
            return
        left = self._detail_for_profile(self._compare_anchor[0], self._compare_anchor[1])
        right = self._detail_for_profile(selected[0], selected[1])
        if left is None or right is None:
            return
        self._show_fleet_compare(left, right)
        self._compare_anchor = None

    def _can_add_profile(self, profile: PlatformProfile) -> tuple[bool, str]:
        if self._fleet is None or self._fleet.fleet_list_id is None:
            return False, "Select a fleet / era before adding platforms."
        mode = self._construction_mode()
        if mode == "sandbox":
            return True, ""

        reasons: list[str] = []
        if not permitted_profile(self._fleet, profile):
            reasons.append("this fleet list does not permit that platform")
        if is_allied_profile(self._fleet, profile):
            selected_ally = self._selected_allied_fleet_id()
            if selected_ally is None or profile.fleet_list_id != selected_ally:
                reasons.append("select this platform's fleet in the Allied Fleet box first")
            allied_counts = Counter()
            for entry in self._fleet.entries:
                current = self._context.platform_details.get_profile(entry.profile_id)
                if current is not None and current.fleet_list_id != self._fleet.fleet_list_id and current.priority_level in PRIORITIES:
                    allied_counts[current.priority_level] += purchased_choice_count(entry.profile_id, entry.quantity, entry.options)
            scenario = str(self._fleet.metadata.get("scenario_priority", "Raid"))
            allied_definition = definition_for(self._fleet)
            allied_allowance = allied_definition.max_scenario_fap if allied_definition is not None else 1
            if profile.priority_level in PRIORITIES and not can_add_priority(
                scenario, allied_allowance, allied_counts, profile.priority_level
            ):
                reasons.append(format_unaffordable_choice(
                    scenario, allied_allowance, allied_counts, profile.priority_level,
                    allowance_label="allied allowance",
                ))
        if profile.priority_level == "Ancient" and self._fleet.fleet_list_id == 19:
            selected_ancients = 0
            for entry in self._fleet.entries:
                current = self._context.platform_details.get_profile(entry.profile_id)
                if current is not None and current.priority_level == "Ancient":
                    selected_ancients += entry.quantity
            scenario = str(self._fleet.metadata.get("scenario_priority", "Raid"))
            fap = int(self._fleet.metadata.get("fleet_allocation_points", 1))
            if not can_add_ancient(scenario, fap, selected_ancients):
                reasons.append("no Ancient choice remains in the fleet budget")
        elif profile.priority_level in PRIORITIES:
            counts = self._selected_priority_counts()
            scenario = str(self._fleet.metadata.get("scenario_priority", "Raid"))
            fap = int(self._fleet.metadata.get("fleet_allocation_points", 1))
            if not can_add_priority(scenario, fap, counts, profile.priority_level):
                reasons.append(format_unaffordable_choice(
                    scenario, fap, counts, profile.priority_level
                ))
        if self._fleet.selected_year is not None:
            from dfs.domain.in_service import parse_in_service
            if not parse_in_service(profile.in_service).includes(self._fleet.selected_year):
                reasons.append(f"the platform is not in service in {self._fleet.selected_year}")

        for message in self._context.fleets.preview_add_profile_rules(self._fleet, profile.profile_id):
            # Grouped purchases are applied atomically by the Add action. The
            # preview engine evaluates a hypothetical single ship, so its
            # incomplete-group warning does not apply to this UI operation.
            if message.rule_id == "B5-GROUPED-PURCHASE-001" and grouped_purchase_size(profile.profile_id) > 1:
                continue
            lines = [message.title, "", message.message]
            remedy_items = tuple(getattr(message, "remedy_items", ()))
            if remedy_items:
                lines.extend(("", "How to make this legal"))
                lines.extend(f"• {item}" for item in remedy_items)
            lines.extend(("", f"Rule ID: {message.rule_id}", f"Source: {message.source.citation}"))
            reasons.append("\n".join(lines))

        if not reasons:
            return True, ""
        combined = "\n\n".join(reasons)
        reason = combined[:1].upper() + combined[1:]
        if not reason.endswith("."):
            reason += "."
        return (True, reason) if mode == "advisory" else (False, reason)

    def _add_profile_from_compare(self, profile_id: int) -> None:
        if self._fleet is None:
            return
        profile = self._context.platform_details.get_profile(profile_id)
        if profile is None:
            return
        allowed, reason = self._can_add_profile(profile)
        if not allowed:
            self._context.notifications.warning("Cannot Add Platform", reason)
            return
        self._fleet = self._context.fleets.add_grouped_profile(
            self._fleet, profile_id, grouped_purchase_size(profile_id)
        )
        self._refresh_roster()
        self._refresh_available()
        self._context.status.set("Platform added to fleet")

    def _show_fleet_compare(self, left, right) -> None:
        left_profile = left.profiles[0] if left.profiles else None
        right_profile = right.profiles[0] if right.profiles else None
        left_allowed, left_reason = self._can_add_profile(left_profile) if left_profile else (False, "No profile available.")
        right_allowed, right_reason = self._can_add_profile(right_profile) if right_profile else (False, "No profile available.")
        PlatformCompareDialog(
            left,
            right,
            self,
            add_left=(lambda profile_id=left_profile.profile_id: self._add_profile_from_compare(profile_id)) if left_profile else None,
            add_right=(lambda profile_id=right_profile.profile_id: self._add_profile_from_compare(profile_id)) if right_profile else None,
            left_add_enabled=left_allowed,
            right_add_enabled=right_allowed,
            left_disabled_reason=left_reason,
            right_disabled_reason=right_reason,
        ).exec()

    def _resolve_included_craft(
        self, printed_name: str, fleet_list_id: int | None
    ) -> tuple[int, str, PlatformProfile] | None:
        cache_key = (normalize_craft_name(printed_name), fleet_list_id)
        if cache_key in self._craft_resolution_cache:
            return self._craft_resolution_cache[cache_key]

        target = cache_key[0]
        if not target:
            self._craft_resolution_cache[cache_key] = None
            return None

        best: tuple[int, str, PlatformProfile] | None = None
        best_score = -1
        filters = PlatformFilter(
            faction_ids=(self._fleet.faction_id,) if self._fleet and self._fleet.faction_id else (),
            limit=1000,
        )
        for summary in self._context.catalog.search(filters):
            normalized = normalize_craft_name(summary.name)
            score = 0
            if normalized == target:
                score = 100
            elif target in normalized or normalized in target:
                score = 60
            else:
                target_words = set(target.split())
                candidate_words = set(normalized.split())
                score = len(target_words & candidate_words) * 10
            if score <= best_score:
                continue
            detail = self._context.platform_details.get(summary.ship_id)
            if detail is None or not detail.profiles:
                continue
            profile = next(
                (item for item in detail.profiles if item.fleet_list_id == fleet_list_id),
                detail.profiles[0],
            )
            best = (summary.ship_id, summary.name, profile)
            best_score = score

        if best_score < 20:
            best = None
        self._craft_resolution_cache[cache_key] = best
        return best

    def _replacement_opportunities(self, entry, profile: PlatformProfile):
        if self._fleet is None:
            return ()
        opportunities = self._context.fighter_replacements.opportunities(
            profile, self._fleet.selected_year
        )
        return tuple(
            replace(opportunity, source_quantity=opportunity.source_quantity * entry.quantity)
            for opportunity in opportunities
        )

    def _manage_craft_replacements(self, entry_id: str) -> None:
        if self._fleet is None:
            return
        entry = next((candidate for candidate in self._fleet.entries if candidate.entry_id == entry_id), None)
        profile = self._entry_profiles.get(entry_id) if entry is not None else None
        if entry is None or profile is None:
            return
        opportunities = self._replacement_opportunities(entry, profile)
        if not opportunities:
            self._context.notifications.info("Configure Air Group", "This platform has no fighter replacement options in the selected fleet and year.")
            return
        name, _ = self._profile_name(entry.profile_id)
        dialog = CraftReplacementDialog(
            name, 1, opportunities, replacement_map(entry.options), self
        )
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        selections = dialog.selections()
        costs = dialog.patrol_costs()
        fleet = self._fleet
        for opportunity in opportunities:
            fleet = self._context.fleets.set_craft_replacements(
                fleet, entry.entry_id, opportunity.source_printed_name,
                selections.get(opportunity.source_printed_name, {}),
                costs.get(opportunity.source_printed_name, 0),
            )
        self._fleet = fleet
        self._refresh_roster()
        self._refresh_available()
        self._context.status.set("Air group updated")

    def _insert_included_craft_rows(
        self, row: int, parent_entry, parent_profile: PlatformProfile
    ) -> int:
        selected_replacements = replacement_map(parent_entry.options)
        for craft in parse_included_craft(parent_profile.craft):
            total_quantity = craft.quantity * parent_entry.quantity
            source_map = selected_replacements.get(craft.printed_name, {})
            replaced_total = sum(max(0, int(value)) for value in source_map.values())
            remaining = max(0, total_quantity - replaced_total)

            child_rows: list[tuple[str, int, int | None, int | None, str]] = []
            if remaining:
                resolved = self._resolve_included_craft(craft.printed_name, parent_profile.fleet_list_id)
                child_rows.append((
                    resolved[1] if resolved else craft.printed_name,
                    remaining,
                    resolved[2].profile_id if resolved else None,
                    resolved[0] if resolved else None,
                    "Standard",
                ))
            for raw_profile_id, quantity in source_map.items():
                try:
                    profile_id = int(raw_profile_id)
                except (TypeError, ValueError):
                    continue
                resolved_replacement = self._context.fighter_replacements.resolve_profile(profile_id)
                if resolved_replacement is None:
                    child_rows.append((f"Unresolved replacement profile {profile_id}", int(quantity), profile_id, None, "Replacement"))
                else:
                    detail, replacement_profile = resolved_replacement
                    child_rows.append((detail.name, int(quantity), profile_id, detail.ship_id, "Replacement"))

            for display_name, quantity, profile_id, ship_id, kind_label in child_rows:
                self.roster_table.insertRow(row)
                item = QTableWidgetItem(f"    ↳ {display_name} ({quantity})")
                item.setData(Qt.ItemDataRole.UserRole + 10, "craft")
                item.setData(Qt.ItemDataRole.UserRole + 11, parent_entry.entry_id)
                if profile_id is not None:
                    item.setData(Qt.ItemDataRole.UserRole + 1, profile_id)
                if ship_id is not None:
                    item.setData(Qt.ItemDataRole.UserRole + 2, ship_id)
                item.setToolTip(
                    f"{kind_label} craft from {parent_profile.fleet_name}; does not spend a platform choice"
                    + (" (replacement purchase cost is included in the fleet budget)." if kind_label == "Replacement" else ".")
                )
                font = item.font()
                font.setItalic(True)
                item.setFont(font)
                self.roster_table.setItem(row, 0, item)
                label_item = QTableWidgetItem(kind_label)
                label_item.setFlags(label_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.roster_table.setItem(row, 1, label_item)
                self.roster_table.setItem(row, 2, QTableWidgetItem("Included"))
                self.roster_table.setItem(row, 3, QTableWidgetItem(str(quantity)))
                self.roster_table.setItem(row, 4, QTableWidgetItem(""))
                row += 1
        row = self._insert_huge_hangars_rows(row, parent_entry, parent_profile)
        return self._insert_missile_rows(row, parent_entry, parent_profile)

    def _huge_hangars_candidates(self, parent_entry, parent_profile: PlatformProfile):
        capacity = capacity_from_traits(parent_profile.traits) * parent_entry.quantity
        if capacity <= 0 or self._fleet is None:
            return ()
        parent_name, _ = self._profile_name(parent_entry.profile_id)
        basic = {
            normalize_craft_name("Sa’ria’stor Light Raider"): 1,
            normalize_craft_name("Ria’stor Heavy Raider"): 1,
            normalize_craft_name("Kama’re Scout"): 1,
        }
        amu_only = {
            normalize_craft_name("Dra’Vash Cruiser"): 8,
            normalize_craft_name("Ria’vash Strike Cruiser"): 8,
            normalize_craft_name("Ria’stor Gris Fast Destroyer"): 2,
            normalize_craft_name("Sa’dravash Light Cruiser"): 2,
            normalize_craft_name("Kama’re Sas Patrol Cruiser"): 2,
        } if normalize_craft_name(parent_name).startswith("amu mothership") else {}
        allowed = {**basic, **amu_only}
        candidates = []
        for summary in self._context.catalog.search(PlatformFilter(limit=1000)):
            normalized = normalize_craft_name(summary.name)
            matched_cost = None
            for target, cost in allowed.items():
                if normalized == target or (target in normalized and len(target) > 8):
                    matched_cost = cost
                    break
            if matched_cost is None:
                continue
            detail = self._context.platform_details.get(summary.ship_id)
            if detail is None or not detail.profiles:
                continue
            profile = next((p for p in detail.profiles if p.fleet_list_id == parent_profile.fleet_list_id), detail.profiles[0])
            candidates.append((profile.profile_id, detail.name, matched_cost, detail.ship_id))
        unique = {}
        for item in candidates:
            unique.setdefault(item[0], item)
        return tuple(sorted(unique.values(), key=lambda item: (item[2], item[1].casefold())))

    def _configure_huge_hangars(self, entry_id: str) -> None:
        if self._fleet is None:
            return
        entry = next((item for item in self._fleet.entries if item.entry_id == entry_id), None)
        profile = self._entry_profiles.get(entry_id) if entry is not None else None
        if entry is None or profile is None:
            return
        capacity = capacity_from_traits(profile.traits) * entry.quantity
        candidates = self._huge_hangars_candidates(entry, profile)
        if capacity <= 0 or not candidates:
            self._context.notifications.info("Configure Huge Hangars", "This platform has no configurable Huge Hangars.")
            return
        name, _ = self._profile_name(entry.profile_id)
        dialog = HugeHangarsDialog(
            name, capacity, [(pid, label, cost) for pid, label, cost, _sid in candidates],
            embarked_profile_ids(entry.options), self
        )
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        self._fleet = self._context.fleets.set_huge_hangars(
            self._fleet, entry.entry_id, dialog.selected_profile_ids()
        )
        self._refresh_roster()
        self._context.status.set("Huge Hangars updated")

    def _insert_huge_hangars_rows(self, row: int, parent_entry, parent_profile: PlatformProfile) -> int:
        capacity = capacity_from_traits(parent_profile.traits) * parent_entry.quantity
        if capacity <= 0:
            return row
        candidates = {pid: (name, cost, ship_id) for pid, name, cost, ship_id in self._huge_hangars_candidates(parent_entry, parent_profile)}
        selected = embarked_profile_ids(parent_entry.options)
        used = sum(candidates.get(pid, ("", 0, None))[1] for pid in selected)
        self.roster_table.insertRow(row)
        header = QTableWidgetItem(f"    ↳ Huge Hangars: {used} / {capacity} slots used")
        header.setData(Qt.ItemDataRole.UserRole + 10, "hangar")
        header.setData(Qt.ItemDataRole.UserRole + 11, parent_entry.entry_id)
        header.setToolTip("Double-click to configure individually embarked Drakh ships. These ships cost no FAP and cannot start deployed.")
        font = header.font(); font.setItalic(True); header.setFont(font)
        self.roster_table.setItem(row, 0, header)
        self.roster_table.setItem(row, 1, QTableWidgetItem("Configure"))
        self.roster_table.setItem(row, 2, QTableWidgetItem("Embarked"))
        self.roster_table.setItem(row, 3, QTableWidgetItem(str(len(selected))))
        self.roster_table.setItem(row, 4, QTableWidgetItem(""))
        row += 1
        counters = {}
        for profile_id in selected:
            name, cost, ship_id = candidates.get(profile_id, (f"Unknown profile {profile_id}", 0, None))
            counters[name] = counters.get(name, 0) + 1
            self.roster_table.insertRow(row)
            item = QTableWidgetItem(f"        ↳ {name} #{counters[name]}")
            item.setData(Qt.ItemDataRole.UserRole + 10, "hangar")
            item.setData(Qt.ItemDataRole.UserRole + 11, parent_entry.entry_id)
            item.setData(Qt.ItemDataRole.UserRole + 1, profile_id)
            if ship_id is not None:
                item.setData(Qt.ItemDataRole.UserRole + 2, ship_id)
            item.setToolTip(f"Embarked ship; uses {cost} Huge Hangars slot(s), costs no FAP, and receives its own ship sheet.")
            font = item.font(); font.setItalic(True); item.setFont(font)
            self.roster_table.setItem(row, 0, item)
            self.roster_table.setItem(row, 1, QTableWidgetItem("Embarked"))
            self.roster_table.setItem(row, 2, QTableWidgetItem("No FAP"))
            self.roster_table.setItem(row, 3, QTableWidgetItem("1"))
            self.roster_table.setItem(row, 4, QTableWidgetItem(""))
            row += 1
        return row

    def _missile_opportunities(self, entry, profile: PlatformProfile):
        if self._fleet is None:
            return ()
        name, _ = self._profile_name(entry.profile_id)
        return self._context.missile_loadouts.opportunities(
            name, profile, self._fleet.selected_year
        )

    def _insert_missile_rows(self, row: int, parent_entry, parent_profile: PlatformProfile) -> int:
        opportunities = self._missile_opportunities(parent_entry, parent_profile)
        if not opportunities:
            return row
        selections = missile_loadout_map(parent_entry.options)
        for opportunity in opportunities:
            variant_id = selections.get(opportunity.rack_key, "standard")
            variant = self._context.missile_loadouts.variant(variant_id)
            if variant_id == "standard" or variant is None:
                display = "Printed standard missile"
                status = "Standard"
            else:
                display = variant.display_name
                status = "Replacement"
            self.roster_table.insertRow(row)
            item = QTableWidgetItem(f"    ↳ {opportunity.label}: {display}")
            item.setData(Qt.ItemDataRole.UserRole + 10, "missile")
            item.setData(Qt.ItemDataRole.UserRole + 11, parent_entry.entry_id)
            item.setToolTip(
                f"{status} ordnance. Double-click to configure this ship's missile racks. "
                f"Source: {opportunity.source_book}, pp. 15-16."
            )
            font = item.font()
            font.setItalic(True)
            item.setFont(font)
            self.roster_table.setItem(row, 0, item)
            self.roster_table.setItem(row, 1, QTableWidgetItem(status))
            self.roster_table.setItem(row, 2, QTableWidgetItem("Ordnance"))
            self.roster_table.setItem(row, 3, QTableWidgetItem("1"))
            self.roster_table.setItem(row, 4, QTableWidgetItem(""))
            row += 1
        return row

    def _configure_ordnance(self, entry_id: str) -> None:
        if self._fleet is None:
            return
        entry = next((candidate for candidate in self._fleet.entries if candidate.entry_id == entry_id), None)
        profile = self._entry_profiles.get(entry_id) if entry is not None else None
        if entry is None or profile is None:
            return
        opportunities = self._missile_opportunities(entry, profile)
        if not opportunities:
            self._context.notifications.info("Configure Ordnance", "This platform has no configurable missile racks in the selected fleet and year.")
            return
        name, _ = self._profile_name(entry.profile_id)
        dialog = MissileLoadoutDialog(name, opportunities, missile_loadout_map(entry.options), self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        self._fleet = self._context.fleets.set_missile_loadouts(
            self._fleet, entry.entry_id, dialog.selections()
        )
        self._refresh_roster()
        self._context.status.set("Ordnance loadout updated")

    def _row_child_context(self, row: int):
        item = self.roster_table.item(row, 0)
        if item is None:
            return None
        kind = item.data(Qt.ItemDataRole.UserRole + 10)
        parent_entry_id = item.data(Qt.ItemDataRole.UserRole + 11)
        if kind not in ("craft", "missile", "hangar") or not parent_entry_id:
            return None
        return str(kind), str(parent_entry_id), item

    def _roster_double_clicked(self, row: int, _column: int) -> None:
        child = self._row_child_context(row)
        if child is None:
            return
        kind, entry_id, _item = child
        if kind == "craft":
            self._manage_craft_replacements(entry_id)
        elif kind == "missile":
            self._configure_ordnance(entry_id)
        elif kind == "hangar":
            self._configure_huge_hangars(entry_id)

    def _show_child_context_menu(self, point, child) -> bool:
        kind, entry_id, item = child
        menu = QMenu(self)
        if kind == "craft":
            configure = menu.addAction("Configure Air Group…")
            configure.triggered.connect(lambda: self._manage_craft_replacements(entry_id))
            profile_id = item.data(Qt.ItemDataRole.UserRole + 1)
            ship_id = item.data(Qt.ItemDataRole.UserRole + 2)
            if ship_id:
                menu.addSeparator()
                open_action = menu.addAction("Open Fighter in Platform Explorer")
                open_action.triggered.connect(lambda _=False, value=int(ship_id): self.open_platform_requested.emit(value))
            if profile_id and ship_id:
                compare_action = menu.addAction("Mark Fighter for Comparison")
                compare_action.triggered.connect(
                    lambda _=False, sid=int(ship_id), pid=int(profile_id), name=item.text().strip():
                    self._mark_roster_for_comparison(sid, pid, name)
                )
        elif kind == "missile":
            configure = menu.addAction("Configure Ordnance…")
            configure.triggered.connect(lambda: self._configure_ordnance(entry_id))
        else:
            configure = menu.addAction("Configure Huge Hangars…")
            configure.triggered.connect(lambda: self._configure_huge_hangars(entry_id))
            ship_id = item.data(Qt.ItemDataRole.UserRole + 2)
            if ship_id:
                menu.addSeparator()
                open_action = menu.addAction("Open Embarked Ship in Platform Explorer")
                open_action.triggered.connect(lambda _=False, value=int(ship_id): self.open_platform_requested.emit(value))
        menu.exec(self.roster_table.mapToGlobal(point))
        return True

    def _set_custom_order(self) -> None:
        self._roster_sort_column = None
        self._roster_sort_descending = False
        header = self.roster_table.horizontalHeader()
        header.setSortIndicatorShown(False)

    def _move_roster_entry(
        self, entry_id: str, target_entry_id: str | None, before: bool
    ) -> None:
        if self._fleet is None:
            return
        self._fleet = self._context.fleets.move_entry(
            self._fleet, entry_id, target_entry_id, before=before
        )
        self._set_custom_order()
        self._refresh_roster()
        self._context.status.set("Fleet roster set to Custom Order")

    def _move_entry_by_offset(self, entry_id: str, offset: int) -> None:
        if self._fleet is None:
            return
        ids = [entry.entry_id for entry in self._fleet.entries]
        try:
            source_index = ids.index(entry_id)
        except ValueError:
            return
        target_index = max(0, min(len(ids) - 1, source_index + offset))
        if target_index == source_index:
            return
        ids.pop(source_index)
        ids.insert(target_index, entry_id)
        self._fleet = self._context.fleets.reorder_entries(self._fleet, ids)
        self._set_custom_order()
        self._refresh_roster()
        self._context.status.set("Fleet roster set to Custom Order")

    def _move_entry_to_edge(self, entry_id: str, *, top: bool) -> None:
        if self._fleet is None:
            return
        ids = [entry.entry_id for entry in self._fleet.entries]
        if entry_id not in ids:
            return
        ids.remove(entry_id)
        if top:
            ids.insert(0, entry_id)
        else:
            ids.append(entry_id)
        self._fleet = self._context.fleets.reorder_entries(self._fleet, ids)
        self._set_custom_order()
        self._refresh_roster()
        self._context.status.set("Fleet roster set to Custom Order")

    def _roster_header_clicked(self, column: int) -> None:
        if self._fleet is None or column not in (0, 2):
            return
        descending = self._roster_sort_column == column and not self._roster_sort_descending
        self._roster_sort_column = column
        self._roster_sort_descending = descending

        names: dict[str, str] = {}
        priorities: dict[str, int] = {}
        for entry in self._fleet.entries:
            name, profile = self._profile_name(entry.profile_id)
            names[entry.entry_id] = name.casefold()
            priorities[entry.entry_id] = PRIORITY_INDEX.get(
                profile.priority_level if profile else "", -1
            )
        if column == 0:
            key = lambda entry: (names[entry.entry_id], entry.entry_id)
        else:
            key = lambda entry: (priorities[entry.entry_id], names[entry.entry_id])
        ordered = sorted(self._fleet.entries, key=key, reverse=descending)
        self._fleet = self._context.fleets.reorder_entries(
            self._fleet, [entry.entry_id for entry in ordered]
        )
        header = self.roster_table.horizontalHeader()
        header.setSortIndicatorShown(True)
        header.setSortIndicator(
            column,
            Qt.SortOrder.DescendingOrder if descending else Qt.SortOrder.AscendingOrder,
        )
        self._refresh_roster()
        label = "Platform" if column == 0 else "Priority"
        direction = "descending" if descending else "ascending"
        self._context.status.set(f"Fleet roster sorted by {label} ({direction})")

    def _refresh_roster(self) -> None:
        self.roster_table.setRowCount(0)
        self._entry_profiles.clear()
        if self._fleet is None:
            self.summary_label.setText("No fleet")
            self.validation_box.clear()
            return

        row = 0
        for entry in self._fleet.entries:
            name, profile = self._profile_name(entry.profile_id)
            if profile is not None:
                self._entry_profiles[entry.entry_id] = profile
            self.roster_table.insertRow(row)
            platform_item = QTableWidgetItem(name)
            platform_item.setData(Qt.ItemDataRole.UserRole, entry.entry_id)
            platform_item.setData(Qt.ItemDataRole.UserRole + 1, entry.profile_id)
            if profile is not None:
                vessel_note = f"Vessel name: {entry.vessel_name}" if entry.vessel_name else "Unnamed vessel"
                platform_item.setToolTip(self._profile_tooltip(name, profile, vessel_note))
            self.roster_table.setItem(row, 0, platform_item)

            vessel_name = QLineEdit(entry.vessel_name)
            vessel_name.setPlaceholderText(
                "Optional ship name" if entry.quantity == 1 else "Name one vessel (splits group)"
            )
            if profile is not None:
                vessel_name.setToolTip(platform_item.toolTip())
            vessel_name.editingFinished.connect(
                lambda entry_id=entry.entry_id, editor=vessel_name: self._set_vessel_name(
                    entry_id, editor.text()
                )
            )
            self.roster_table.setCellWidget(row, 1, vessel_name)
            priority_item = QTableWidgetItem(profile.priority_level if profile else "?")
            if profile is not None:
                priority_item.setToolTip(platform_item.toolTip())
            self.roster_table.setItem(row, 2, priority_item)
            qty = QSpinBox()
            group_size = grouped_purchase_size(entry.profile_id)
            if group_size > 1 and entry.options.get("grouped_purchase_group_id"):
                qty.setRange(1, 1)
                qty.setValue(1)
                qty.setButtonSymbols(QSpinBox.ButtonSymbols.NoButtons)
            else:
                qty.setRange(1, 99)
                qty.setSingleStep(1)
                qty.setValue(entry.quantity)
                qty.valueChanged.connect(lambda value, entry_id=entry.entry_id: self._set_quantity(entry_id, value))
            if profile is not None:
                purchase_note = grouped_purchase_label(entry.profile_id)
                qty.setToolTip(platform_item.toolTip() + ("\n\n" + purchase_note if purchase_note else ""))
            self.roster_table.setCellWidget(row, 3, qty)
            remove = QPushButton("Remove")
            remove.clicked.connect(lambda _=False, entry_id=entry.entry_id: self._remove_entry(entry_id))
            self.roster_table.setCellWidget(row, 4, remove)
            row += 1

            if profile is not None:
                row = self._insert_included_craft_rows(row, entry, profile)

        summary = self._context.fleets.summarize(self._fleet)
        counts = ", ".join(f"{value} {priority}" for priority, value in summary.priority_counts.items()) or "No selections"
        self.summary_label.setText(
            f"Budget: {summary.budget_label}    |    Selected: {counts}    |    {summary.remaining_label}"
        )
        if not summary.validation.messages:
            self.validation_box.setPlainText("No construction errors or warnings.")
        else:
            lines = []
            for message in summary.validation.messages:
                prefix = {
                    ValidationSeverity.ERROR: "INVALID",
                    ValidationSeverity.WARNING: "WARNING",
                    ValidationSeverity.INFO: "INFO",
                }[message.severity]
                lines.append(f"{prefix}: {message.message}")
            self.validation_box.setPlainText("\n".join(lines))

    def _set_vessel_name(self, entry_id: str, vessel_name: str) -> None:
        if self._fleet is None:
            return
        current = next((entry for entry in self._fleet.entries if entry.entry_id == entry_id), None)
        if current is None or current.vessel_name == vessel_name.strip():
            return
        self._fleet = self._context.fleets.set_vessel_name(self._fleet, entry_id, vessel_name)
        self._refresh_roster()
        self._refresh_available()
        self._context.status.set("Ship name updated")

    def _roster_entry_at(self, point=None):
        if self._fleet is None:
            return None
        row = self.roster_table.rowAt(point.y()) if point is not None else self.roster_table.currentRow()
        if row < 0:
            return None
        item = self.roster_table.item(row, 0)
        if item is None:
            return None
        entry_id = item.data(Qt.ItemDataRole.UserRole)
        return next((entry for entry in self._fleet.entries if entry.entry_id == entry_id), None)

    def _ship_for_profile(self, profile_id: int) -> tuple[int, str] | None:
        profile = self._context.platform_details.get_profile(profile_id)
        if profile is None:
            return None
        for summary in self._context.catalog.search(
            PlatformFilter(fleet_list_ids=(profile.fleet_list_id,), limit=1000)
        ):
            detail = self._context.platform_details.get(summary.ship_id)
            if detail and any(p.profile_id == profile_id for p in detail.profiles):
                return summary.ship_id, summary.name
        return None

    def _show_roster_context_menu(self, point) -> None:
        row = self.roster_table.rowAt(point.y())
        child = self._row_child_context(row) if row >= 0 else None
        if child is not None:
            self._show_child_context_menu(point, child)
            return
        entry = self._roster_entry_at(point)
        if entry is None:
            return
        menu = QMenu(self)
        rename_action = menu.addAction("Rename Ship")
        rename_action.triggered.connect(lambda: self.roster_table.cellWidget(
            self.roster_table.rowAt(point.y()), 1
        ).setFocus())
        platform = self._ship_for_profile(entry.profile_id)
        if platform is not None:
            open_action = menu.addAction("Open in Platform Explorer")
            open_action.triggered.connect(lambda _=False, ship_id=platform[0]: self.open_platform_requested.emit(ship_id))
            pdf_action = menu.addAction("View PDF in Platform Explorer")
            pdf_action.triggered.connect(lambda _=False, ship_id=platform[0]: self.open_platform_requested.emit(ship_id))
            compare_action = menu.addAction("Mark for Comparison")
            compare_action.triggered.connect(
                lambda _=False, ship_id=platform[0], profile_id=entry.profile_id, name=platform[1]: self._mark_roster_for_comparison(
                    ship_id, profile_id, name
                )
            )
            compare_marked = menu.addAction("Compare with Marked")
            compare_marked.setEnabled(
                self._compare_anchor is not None
                and self._compare_anchor[:2] != (platform[0], entry.profile_id)
            )
            compare_marked.triggered.connect(
                lambda _=False, ship_id=platform[0], profile_id=entry.profile_id, name=platform[1]: self._compare_roster_platform(
                    ship_id, profile_id, name
                )
            )
        menu.addSeparator()
        move_up = menu.addAction("Move Up")
        move_up.triggered.connect(lambda: self._move_entry_by_offset(entry.entry_id, -1))
        move_down = menu.addAction("Move Down")
        move_down.triggered.connect(lambda: self._move_entry_by_offset(entry.entry_id, 1))
        move_top = menu.addAction("Move to Top")
        move_top.triggered.connect(lambda: self._move_entry_to_edge(entry.entry_id, top=True))
        move_bottom = menu.addAction("Move to Bottom")
        move_bottom.triggered.connect(lambda: self._move_entry_to_edge(entry.entry_id, top=False))
        menu.addSeparator()
        duplicate_action = menu.addAction("Duplicate")
        duplicate_action.triggered.connect(lambda: self._duplicate_entry(entry.entry_id))
        remove_action = menu.addAction("Remove")
        remove_action.triggered.connect(lambda: self._remove_entry(entry.entry_id))
        menu.exec(self.roster_table.mapToGlobal(point))

    def _mark_roster_for_comparison(self, ship_id: int, profile_id: int, name: str) -> None:
        self._compare_anchor = (ship_id, profile_id, name)
        self._context.status.set(f"Comparison platform: {name}")

    def _compare_roster_platform(self, ship_id: int, profile_id: int, name: str) -> None:
        selected = (ship_id, profile_id, name)
        if self._compare_anchor is None or self._compare_anchor[:2] == selected[:2]:
            self._compare_anchor = selected
            self._context.status.set(f"Select another platform to compare with {name}")
            return
        left = self._detail_for_profile(self._compare_anchor[0], self._compare_anchor[1])
        right = self._detail_for_profile(ship_id, profile_id)
        if left is None or right is None:
            return
        self._show_fleet_compare(left, right)
        self._compare_anchor = None

    def _duplicate_entry(self, entry_id: str) -> None:
        if self._fleet is None:
            return
        source = next((entry for entry in self._fleet.entries if entry.entry_id == entry_id), None)
        if source is None:
            return
        self._fleet = self._context.fleets.add_profile(
            self._fleet, source.profile_id, source.quantity
        )
        self._refresh_roster()
        self._refresh_available()
        self._context.status.set("Fleet entry duplicated")

    def _set_quantity(self, entry_id: str, quantity: int) -> None:
        if self._fleet is None:
            return
        self._fleet = self._context.fleets.set_quantity(self._fleet, entry_id, quantity)
        self._refresh_roster()
        self._refresh_available()

    def _remove_entry(self, entry_id: str) -> None:
        if self._fleet is None:
            return
        entry = next((item for item in self._fleet.entries if item.entry_id == entry_id), None)
        group_id = entry.options.get("grouped_purchase_group_id") if entry is not None else None
        if group_id:
            remaining = tuple(
                item for item in self._fleet.entries
                if item.options.get("grouped_purchase_group_id") != group_id
            )
            self._fleet = self._fleet.replace_entries(remaining)
        else:
            self._fleet = self._context.fleets.remove_entry(self._fleet, entry_id)
        self._refresh_roster()
        self._refresh_available()
        self._context.status.set("Platform removed from fleet")

    def _default_fleet_folder(self) -> Path:
        configured = self._context.settings.get_str("fleet/default_folder", "").strip()
        folder = self._context.resources.writable_folder(
            configured,
            self._context.resources.fleet_files_root,
        )
        if not configured or Path(configured).expanduser().resolve() != folder:
            self._context.settings.set_value("fleet/default_folder", str(folder))
            self._context.settings.sync()
        return folder

    def _remember_fleet_folder(self, path: Path) -> None:
        self._context.settings.set_value("fleet/default_folder", str(path.parent.resolve()))
        self._context.settings.sync()

    def save_fleet(self, save_as: bool = False) -> None:
        if self._fleet is None:
            return
        path = self._current_path
        if save_as or path is None:
            selected, _ = QFileDialog.getSaveFileName(
                self,
                "Save DFS Fleet",
                str(self._default_fleet_folder() / f"{self._fleet.name}.dfs-fleet.json"),
                "DFS Fleet (*.dfs-fleet.json);;JSON Files (*.json)",
            )
            if not selected:
                return
            path = Path(selected)
            if not str(path).endswith(self._context.fleet_files.FILE_EXTENSION):
                path = Path(str(path) + self._context.fleet_files.FILE_EXTENSION)
        self._current_path = self._context.fleet_files.save(self._fleet, path)
        self._remember_fleet_folder(self._current_path)
        self._context.status.set(f"Fleet saved: {self._current_path.name}")
        self._context.notifications.info("Fleet Saved", str(self._current_path))

    def open_fleet(self) -> None:
        selected, _ = QFileDialog.getOpenFileName(
            self,
            "Open DFS Fleet",
            str(self._default_fleet_folder()),
            "DFS Fleet (*.dfs-fleet.json);;JSON Files (*.json)",
        )
        if not selected:
            return
        try:
            fleet = self._context.fleet_files.load(selected)
        except Exception as exc:
            QMessageBox.critical(self, "Open Fleet", str(exc))
            return
        self._fleet = fleet
        self._current_path = Path(selected)
        self._remember_fleet_folder(self._current_path)
        self._load_controls_from_fleet()
        self._refresh_available()
        self._refresh_roster()
        self._context.status.set(f"Fleet loaded: {self._current_path.name}")

    def _load_controls_from_fleet(self) -> None:
        if self._fleet is None:
            return
        self._building_controls = True
        try:
            self.name_edit.setText(self._fleet.name)
            index = self.profile_combo.findData(self._fleet.construction_profile_id)
            if index >= 0:
                self.profile_combo.setCurrentIndex(index)
            index = self.faction_combo.findData(self._fleet.faction_id)
            self.faction_combo.setCurrentIndex(max(0, index))
            self._populate_fleets(self._fleet.faction_id)
            index = self.fleet_combo.findData(self._fleet.fleet_list_id)
            self.fleet_combo.setCurrentIndex(max(0, index))
            self.year_spin.setValue(self._fleet.selected_year or 0)
            self.priority_combo.setCurrentText(str(self._fleet.metadata.get("scenario_priority", "Raid")))
            self.fap_spin.setValue(int(self._fleet.metadata.get("fleet_allocation_points", 1)))
            self._populate_allied_fleets()
        finally:
            self._building_controls = False
