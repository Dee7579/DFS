"""Polished Ship Viewer workspace: Phase 3B."""

from __future__ import annotations

from PySide6.QtCore import QItemSelection, QSettings, QTimer, Qt
from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QSplitter,
    QTableView,
    QVBoxLayout,
    QWidget,
)

from dfs.bootstrap import ApplicationServices
from dfs.domain.catalog import FilterOption, PlatformFilter
from dfs.ui.shared.error_dialog import show_error
from dfs.ui.ship_viewer.detail_panel import PlatformDetailPanel
from dfs.ui.ship_viewer.platform_table_model import PlatformTableModel


class ShipViewerPage(QWidget):
    SETTINGS_GROUP = "ship_viewer"

    def __init__(self, services: ApplicationServices) -> None:
        super().__init__()
        self._services = services
        self._model = PlatformTableModel()
        self._settings = QSettings()

        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Search platform name or class…")
        self.search_box.setClearButtonEnabled(True)

        self.year_spin = QSpinBox()
        self.year_spin.setRange(0, 9999)
        self.year_spin.setSpecialValueText("Any year")
        self.year_spin.setToolTip(
            "Show profiles available during this Earth year. "
            "Use 0/Any year to disable the date filter."
        )

        self.faction_combo = QComboBox()
        self.fleet_combo = QComboBox()
        self.priority_combo = QComboBox()
        self.trait_combo = QComboBox()
        self.weapon_combo = QComboBox()
        self.clear_button = QPushButton("Clear filters")

        filters = QFrame()
        filters.setObjectName("filterPanel")
        filter_layout = QVBoxLayout(filters)
        filter_layout.addWidget(QLabel("Search"))
        filter_layout.addWidget(self.search_box)
        filter_layout.addWidget(QLabel("Available in Year"))
        filter_layout.addWidget(self.year_spin)

        for caption, combo in (
            ("Faction", self.faction_combo),
            ("Fleet / Era", self.fleet_combo),
            ("Priority", self.priority_combo),
        ):
            filter_layout.addWidget(QLabel(caption))
            filter_layout.addWidget(combo)

        self.advanced_group = QGroupBox("Advanced Filters")
        self.advanced_group.setCheckable(True)
        self.advanced_group.setChecked(True)
        advanced_layout = QVBoxLayout(self.advanced_group)
        for caption, combo in (("Trait", self.trait_combo), ("Weapon", self.weapon_combo)):
            advanced_layout.addWidget(QLabel(caption))
            advanced_layout.addWidget(combo)
        filter_layout.addWidget(self.advanced_group)
        filter_layout.addWidget(self.clear_button)
        filter_layout.addStretch(1)

        self.result_count = QLabel("0 platforms")
        self.result_count.setObjectName("resultCount")
        self.table = QTableView()
        self.table.setModel(self._model)
        self.table.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableView.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QTableView.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.setSortingEnabled(False)
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(30)
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)

        results = QWidget()
        results_layout = QVBoxLayout(results)
        results_layout.setContentsMargins(0, 0, 0, 0)
        results_layout.addWidget(self.result_count)
        results_layout.addWidget(self.table, 1)

        self.detail_panel = PlatformDetailPanel(self._services.documents)

        self.center_splitter = QSplitter(Qt.Orientation.Horizontal)
        self.center_splitter.setObjectName("shipViewerCenterSplitter")
        self.center_splitter.addWidget(results)
        self.center_splitter.addWidget(self.detail_panel)
        self.center_splitter.setSizes((520, 700))
        self.center_splitter.setChildrenCollapsible(False)
        self.center_splitter.setStretchFactor(0, 2)
        self.center_splitter.setStretchFactor(1, 3)

        self.main_splitter = QSplitter(Qt.Orientation.Horizontal)
        self.main_splitter.setObjectName("shipViewerMainSplitter")
        self.main_splitter.addWidget(filters)
        self.main_splitter.addWidget(self.center_splitter)
        self.main_splitter.setSizes((250, 1250))
        self.main_splitter.setChildrenCollapsible(False)
        self.main_splitter.setStretchFactor(0, 0)
        self.main_splitter.setStretchFactor(1, 1)

        title_row = QHBoxLayout()
        title = QLabel("Ship Viewer")
        title.setObjectName("pageTitle")
        self.active_filter_summary = QLabel("")
        self.active_filter_summary.setObjectName("activeFilterSummary")
        self.active_filter_summary.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        title_row.addWidget(title)
        title_row.addStretch(1)
        title_row.addWidget(self.active_filter_summary)

        subtitle = QLabel("Browse the complete DFS Babylon 5 platform catalog.")
        subtitle.setObjectName("pageSubtitle")

        layout = QVBoxLayout(self)
        layout.addLayout(title_row)
        layout.addWidget(subtitle)
        layout.addWidget(self.main_splitter, 1)

        self._search_timer = QTimer(self)
        self._search_timer.setSingleShot(True)
        self._search_timer.setInterval(250)
        self._search_timer.timeout.connect(self.refresh_results)

        self.search_box.textChanged.connect(self._schedule_search)
        self.year_spin.valueChanged.connect(self._schedule_search)
        self.faction_combo.currentIndexChanged.connect(self._faction_changed)
        for combo in (self.fleet_combo, self.priority_combo, self.trait_combo, self.weapon_combo):
            combo.currentIndexChanged.connect(self._schedule_search)
        self.clear_button.clicked.connect(self.clear_filters)
        self.table.selectionModel().selectionChanged.connect(self._selection_changed)
        self.table.doubleClicked.connect(self._open_selected_result)
        self.main_splitter.splitterMoved.connect(lambda *_: self.save_settings())
        self.center_splitter.splitterMoved.connect(lambda *_: self.save_settings())
        self.advanced_group.toggled.connect(lambda *_: self.save_settings())

        self._load_filter_options()
        self.restore_settings()
        self.refresh_results()

    @staticmethod
    def _populate_combo(combo: QComboBox, options: list[FilterOption], all_label: str) -> None:
        current_data = combo.currentData()
        combo.blockSignals(True)
        combo.clear()
        combo.addItem(all_label, None)
        selected_index = 0
        for index, option in enumerate(options, start=1):
            suffix = f" ({option.count})" if option.count else ""
            combo.addItem(f"{option.label}{suffix}", option.id)
            if option.id == current_data:
                selected_index = index
        combo.setCurrentIndex(selected_index)
        combo.blockSignals(False)

    def _load_filter_options(self) -> None:
        try:
            self._populate_combo(self.faction_combo, self._services.catalog.list_factions(), "All factions")
            self._populate_combo(self.fleet_combo, self._services.catalog.list_fleets(), "All fleets / eras")
            self._populate_combo(self.priority_combo, self._services.catalog.list_priorities(), "All priorities")
            self._populate_combo(self.trait_combo, self._services.catalog.list_traits(), "All traits")
            self._populate_combo(self.weapon_combo, self._services.catalog.list_weapons(), "All weapons")
        except Exception as exc:
            show_error(self, "Unable to load filters", str(exc))

    def _faction_changed(self) -> None:
        faction_id = self.faction_combo.currentData()
        try:
            self._populate_combo(
                self.fleet_combo,
                self._services.catalog.list_fleets(faction_id),
                "All fleets / eras",
            )
        except Exception as exc:
            show_error(self, "Unable to load fleets", str(exc))
        self._schedule_search()

    def _schedule_search(self) -> None:
        self._search_timer.start()

    def _filters(self) -> PlatformFilter:
        faction_id = self.faction_combo.currentData()
        fleet_id = self.fleet_combo.currentData()
        priority = self.priority_combo.currentData()
        trait = self.trait_combo.currentData()
        weapon = self.weapon_combo.currentData()
        year = self.year_spin.value()
        return PlatformFilter(
            search_text=self.search_box.text(),
            faction_ids=(int(faction_id),) if faction_id is not None else (),
            fleet_list_ids=(int(fleet_id),) if fleet_id is not None else (),
            priority_levels=(str(priority),) if priority is not None else (),
            traits=(str(trait),) if trait is not None else (),
            weapons=(str(weapon),) if weapon is not None else (),
            available_year=year if year > 0 else None,
            limit=1000,
        )

    def refresh_results(self) -> None:
        selected_ship_id = self._selected_ship_id()
        try:
            filters = self._filters()
            platforms = self._services.catalog.search(filters)
            total = self._services.catalog.count(filters)
            self._model.set_platforms(platforms)
            shown = len(platforms)
            self.result_count.setText(
                f"{total} platform{'s' if total != 1 else ''}"
                + (f" — showing first {shown}" if shown < total else "")
            )
            self._update_filter_summary(filters)
            self.detail_panel.clear()
            if platforms:
                row_to_select = 0
                if selected_ship_id is not None:
                    for row, platform in enumerate(platforms):
                        if platform.ship_id == selected_ship_id:
                            row_to_select = row
                            break
                self.table.selectRow(row_to_select)
            self.save_settings()
        except Exception as exc:
            show_error(self, "Ship Viewer search failed", str(exc))

    def _update_filter_summary(self, filters: PlatformFilter) -> None:
        parts: list[str] = []
        if filters.available_year is not None:
            parts.append(f"Available in {filters.available_year}")
        if filters.search_text.strip():
            parts.append(f'“{filters.search_text.strip()}”')
        active_count = sum(bool(value) for value in (
            filters.faction_ids, filters.fleet_list_ids, filters.priority_levels,
            filters.traits, filters.weapons,
        ))
        if active_count:
            parts.append(f"{active_count} categorical filter{'s' if active_count != 1 else ''}")
        self.active_filter_summary.setText(" • ".join(parts))

    def clear_filters(self) -> None:
        self.search_box.clear()
        self.year_spin.setValue(0)
        for combo in (
            self.faction_combo,
            self.fleet_combo,
            self.priority_combo,
            self.trait_combo,
            self.weapon_combo,
        ):
            combo.setCurrentIndex(0)
        self.refresh_results()

    def _selected_ship_id(self) -> int | None:
        index = self.table.currentIndex()
        platform = self._model.platform_at(index.row()) if index.isValid() else None
        return platform.ship_id if platform else None

    def _selection_changed(self, selected: QItemSelection, _deselected: QItemSelection) -> None:
        indexes = selected.indexes()
        if not indexes:
            return
        platform = self._model.platform_at(indexes[0].row())
        if platform is None:
            return
        try:
            detail = self._services.platform_details.get(platform.ship_id)
            self.detail_panel.set_platform(detail)
        except Exception as exc:
            show_error(self, "Unable to load platform", str(exc))

    def _open_selected_result(self, *_args) -> None:
        self.detail_panel.setFocus(Qt.FocusReason.OtherFocusReason)
        self.detail_panel.tabs.setCurrentIndex(0)

    def restore_settings(self) -> None:
        self._settings.beginGroup(self.SETTINGS_GROUP)
        main_state = self._settings.value("main_splitter")
        center_state = self._settings.value("center_splitter")
        if main_state:
            self.main_splitter.restoreState(main_state)
        if center_state:
            self.center_splitter.restoreState(center_state)
        self.advanced_group.setChecked(
            self._settings.value("advanced_open", True, type=bool)
        )
        self.year_spin.setValue(self._settings.value("year", 0, type=int))
        self._settings.endGroup()

    def save_settings(self) -> None:
        self._settings.beginGroup(self.SETTINGS_GROUP)
        self._settings.setValue("main_splitter", self.main_splitter.saveState())
        self._settings.setValue("center_splitter", self.center_splitter.saveState())
        self._settings.setValue("advanced_open", self.advanced_group.isChecked())
        self._settings.setValue("year", self.year_spin.value())
        self._settings.endGroup()
