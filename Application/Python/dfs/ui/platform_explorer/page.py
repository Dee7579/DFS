"""DFS Platform Explorer workspace."""

from __future__ import annotations

from PySide6.QtCore import QItemSelection, QSettings, QTimer, Qt, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QMessageBox,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QSplitter,
    QListView,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from dfs.bootstrap import ApplicationServices
from dfs.domain.catalog import FilterOption, PlatformFilter
from dfs.ui.shared.error_dialog import show_error
from dfs.ui.platform_explorer.detail_panel import PlatformDetailPanel
from dfs.ui.platform_explorer.platform_list_model import PlatformListDelegate, PlatformListModel
from dfs.ui.platform_explorer.compare_dialog import PlatformCompareDialog


class PlatformExplorerPage(QWidget):
    platform_opened = Signal(int)
    SETTINGS_GROUP = "platform_explorer"
    LAYOUT_VERSION = 2

    def __init__(self, services: ApplicationServices) -> None:
        super().__init__()
        self._services = services
        self._model = PlatformListModel()
        self._settings = QSettings()
        self._history: list[int] = []
        self._history_index = -1
        self._navigating_history = False
        self._compare_baseline_id: int | None = None

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
        self.filters_panel = filters
        filters.setObjectName("filterPanel")
        filters.setMinimumWidth(175)
        filters.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Expanding)
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
        self.platform_list = QListView()
        self.platform_list.setModel(self._model)
        self.platform_list.setItemDelegate(PlatformListDelegate(self.platform_list))
        self.platform_list.setSelectionMode(QListView.SelectionMode.SingleSelection)
        self.platform_list.setEditTriggers(QListView.EditTrigger.NoEditTriggers)
        self.platform_list.setAlternatingRowColors(False)
        self.platform_list.setMouseTracking(True)
        self.platform_list.setUniformItemSizes(True)
        self.platform_list.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.platform_list.setMinimumWidth(190)
        self.platform_list.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Expanding)

        results = QWidget()
        self.results_panel = results
        results.setMinimumWidth(190)
        results.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Expanding)
        results_layout = QVBoxLayout(results)
        results_layout.setContentsMargins(0, 0, 0, 0)
        results_layout.addWidget(self.result_count)
        results_layout.addWidget(self.platform_list, 1)

        self.detail_panel = PlatformDetailPanel(self._services.documents, self._services.codex)

        self.center_splitter = QSplitter(Qt.Orientation.Horizontal)
        self.center_splitter.setObjectName("platformExplorerCenterSplitter")
        self.center_splitter.addWidget(results)
        self.center_splitter.addWidget(self.detail_panel)
        self.center_splitter.setHandleWidth(9)
        self.center_splitter.setOpaqueResize(True)
        self.center_splitter.setChildrenCollapsible(False)
        self.center_splitter.setStretchFactor(0, 0)
        self.center_splitter.setStretchFactor(1, 1)

        self.main_splitter = QSplitter(Qt.Orientation.Horizontal)
        self.main_splitter.setObjectName("platformExplorerMainSplitter")
        self.main_splitter.addWidget(filters)
        self.main_splitter.addWidget(self.center_splitter)
        self.main_splitter.setHandleWidth(9)
        self.main_splitter.setOpaqueResize(True)
        self.main_splitter.setChildrenCollapsible(False)
        self.main_splitter.setStretchFactor(0, 0)
        self.main_splitter.setStretchFactor(1, 1)

        title_row = QHBoxLayout()
        self.back_button = QPushButton("←")
        self.back_button.setToolTip("Back")
        self.back_button.setEnabled(False)
        self.forward_button = QPushButton("→")
        self.forward_button.setToolTip("Forward")
        self.forward_button.setEnabled(False)
        title = QLabel("Platform Explorer")
        title.setObjectName("pageTitle")
        self.active_filter_summary = QLabel("")
        self.active_filter_summary.setObjectName("activeFilterSummary")
        self.active_filter_summary.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        title_row.addWidget(self.back_button)
        title_row.addWidget(self.forward_button)
        title_row.addWidget(title)
        title_row.addStretch(1)
        title_row.addWidget(self.active_filter_summary)

        subtitle = QLabel("Explore ships, fighters, stations, Ancients, drones and other DFS platforms.")
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
        self.platform_list.selectionModel().selectionChanged.connect(self._selection_changed)
        self.platform_list.doubleClicked.connect(self._open_selected_result)
        self.back_button.clicked.connect(self.go_back)
        self.forward_button.clicked.connect(self.go_forward)
        self.detail_panel.related_platform_requested.connect(self._open_related_craft)
        self.detail_panel.favorite_toggled.connect(self._set_favorite)
        self.detail_panel.compare_requested.connect(self._compare_requested)
        self.main_splitter.splitterMoved.connect(lambda *_: self.save_settings())
        self.center_splitter.splitterMoved.connect(lambda *_: self.save_settings())
        self.advanced_group.toggled.connect(lambda *_: self.save_settings())

        self._load_filter_options()
        restored_layout = self.restore_settings()
        if not restored_layout:
            QTimer.singleShot(0, self.reset_layout)
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
                self.platform_list.setCurrentIndex(self._model.index(row_to_select, 0))
            self.save_settings()
        except Exception as exc:
            show_error(self, "Platform Explorer search failed", str(exc))

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
        index = self.platform_list.currentIndex()
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
            self.detail_panel.set_favorite(self._is_favorite(platform.ship_id))
            if not self._navigating_history:
                self._push_history(platform.ship_id)
            self._record_recent_platform(platform.ship_id)
            self.platform_opened.emit(platform.ship_id)
        except Exception as exc:
            show_error(self, "Unable to load platform", str(exc))

    def _favorite_ids(self) -> list[int]:
        values = self._settings.value("favorite_platforms/ids", [], type=list) or []
        return [int(value) for value in values if str(value).isdigit()]

    def _is_favorite(self, ship_id: int) -> bool:
        return ship_id in self._favorite_ids()

    def _set_favorite(self, ship_id: int, favorite: bool) -> None:
        ids = self._favorite_ids()
        ids = [value for value in ids if value != ship_id]
        if favorite:
            ids.insert(0, ship_id)
        self._settings.setValue("favorite_platforms/ids", ids[:50])

    def _push_history(self, ship_id: int) -> None:
        if self._history_index >= 0 and self._history[self._history_index] == ship_id:
            return
        self._history = self._history[: self._history_index + 1]
        self._history.append(ship_id)
        self._history_index = len(self._history) - 1
        self._update_history_buttons()

    def _update_history_buttons(self) -> None:
        self.back_button.setEnabled(self._history_index > 0)
        self.forward_button.setEnabled(0 <= self._history_index < len(self._history) - 1)

    def go_back(self) -> None:
        if self._history_index <= 0:
            return
        self._history_index -= 1
        self._open_history_id(self._history[self._history_index])

    def go_forward(self) -> None:
        if self._history_index >= len(self._history) - 1:
            return
        self._history_index += 1
        self._open_history_id(self._history[self._history_index])

    def _open_history_id(self, ship_id: int) -> None:
        self._navigating_history = True
        try:
            self.open_platform(ship_id)
        finally:
            self._navigating_history = False
            self._update_history_buttons()

    def _open_related_craft(self, craft_text: str) -> None:
        import re
        cleaned = re.sub(r"^\s*\d+\s+", "", craft_text.strip())
        cleaned = re.sub(r"\bflights?\b", "Flight", cleaned, flags=re.IGNORECASE)
        queries = [cleaned]
        if " Flight" in cleaned:
            queries.append(cleaned.replace(" Flight", ""))
        matches = []
        for query in queries:
            matches = self._services.catalog.search(PlatformFilter(search_text=query, limit=50))
            if matches:
                break
        if not matches:
            QMessageBox.information(self, "Related Craft", f"No platform matching “{craft_text}” was found.")
            return
        exact = next((p for p in matches if p.name.casefold() == cleaned.casefold()), matches[0])
        self.open_platform(exact.ship_id)

    def _compare_requested(self, ship_id: int) -> None:
        if self._compare_baseline_id is None:
            self._compare_baseline_id = ship_id
            baseline = self._services.platform_details.get(ship_id)
            self.detail_panel.set_compare_mode(baseline.name)
            QMessageBox.information(
                self, "Compare Platforms",
                "Comparison baseline selected. Open another platform and press Compare again."
            )
            return
        if self._compare_baseline_id == ship_id:
            self._compare_baseline_id = None
            self.detail_panel.set_compare_mode(None)
            return
        left = self._services.platform_details.get(self._compare_baseline_id)
        right = self._services.platform_details.get(ship_id)
        PlatformCompareDialog(left, right, self).exec()
        self._compare_baseline_id = None
        self.detail_panel.set_compare_mode(None)

    def _open_selected_result(self, *_args) -> None:
        self.detail_panel.setFocus(Qt.FocusReason.OtherFocusReason)
        self.detail_panel.tabs.setCurrentIndex(0)

    def open_platform(self, ship_id: int) -> None:
        """Open a platform from another workspace, preserving current filters when possible."""
        for row in range(self._model.rowCount()):
            platform = self._model.platform_at(row)
            if platform is not None and platform.ship_id == ship_id:
                self.platform_list.setCurrentIndex(self._model.index(row, 0))
                return
        # The platform may be hidden by active filters. Clear them and retry.
        self.clear_filters()
        for row in range(self._model.rowCount()):
            platform = self._model.platform_at(row)
            if platform is not None and platform.ship_id == ship_id:
                self.platform_list.setCurrentIndex(self._model.index(row, 0))
                return

    def _record_recent_platform(self, ship_id: int) -> None:
        ids = self._settings.value("recent_platforms/ids", [], type=list) or []
        normalized = [int(value) for value in ids if str(value).isdigit()]
        normalized = [value for value in normalized if value != ship_id]
        normalized.insert(0, ship_id)
        self._settings.setValue("recent_platforms/ids", normalized[:10])
        self._settings.setValue("recent_platforms/last_id", ship_id)

    def restore_settings(self) -> bool:
        self._settings.beginGroup(self.SETTINGS_GROUP)
        layout_version = self._settings.value("layout_version", 0, type=int)
        main_state = self._settings.value("main_splitter")
        center_state = self._settings.value("center_splitter")
        restored = False
        if layout_version == self.LAYOUT_VERSION and main_state and center_state:
            main_ok = self.main_splitter.restoreState(main_state)
            center_ok = self.center_splitter.restoreState(center_state)
            restored = bool(main_ok and center_ok)
        self.advanced_group.setChecked(
            self._settings.value("advanced_open", True, type=bool)
        )
        self.year_spin.setValue(self._settings.value("year", 0, type=int))
        self._settings.endGroup()
        return restored

    def reset_layout(self) -> None:
        """Restore the recommended 18 / 22 / 60 workspace proportions."""

        total_width = max(self.main_splitter.width(), 1100)
        filter_width = max(190, int(total_width * 0.18))
        content_width = max(700, total_width - filter_width)
        navigator_width = max(220, int(total_width * 0.22))
        workspace_width = max(420, content_width - navigator_width)
        self.main_splitter.setSizes((filter_width, content_width))
        self.center_splitter.setSizes((navigator_width, workspace_width))
        self.save_settings()

    def save_settings(self) -> None:
        self._settings.beginGroup(self.SETTINGS_GROUP)
        self._settings.setValue("layout_version", self.LAYOUT_VERSION)
        self._settings.setValue("main_splitter", self.main_splitter.saveState())
        self._settings.setValue("center_splitter", self.center_splitter.saveState())
        self._settings.setValue("advanced_open", self.advanced_group.isChecked())
        self._settings.setValue("year", self.year_spin.value())
        self._settings.endGroup()
