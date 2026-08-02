"""Tactical Assistant combat-status workspace.

The page edits only independent :class:`TacticalGameState` objects and
``*.dfs-game.json`` files. Canonical platform modules and ``dfs.db`` remain
read-only inputs supplied through the application context.
"""
from __future__ import annotations

from html import escape
from pathlib import Path
import random
import re

from PySide6.QtCore import QEvent, QObject, QRect, Qt, Signal
from PySide6.QtGui import QBrush, QColor, QPixmap
from PySide6.QtWidgets import (
    QAbstractItemView,
    QBoxLayout,
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QInputDialog,
    QLabel,
    QLayout,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMenu,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QSplitter,
    QTabWidget,
    QTextEdit,
    QToolButton,
    QToolTip,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from dfs.bootstrap import ApplicationContext
from dfs.domain.tactical.reference_stats import fighter_reference_stats
from dfs.domain.tactical import (
    ATTACK_TABLE_HELP,
    COMMON_CODEX_RULE_NAMES,
    CRITICAL_TABLES_HELP,
    CRITICAL_RULES,
    CRITICAL_RULE_BY_KEY,
    DAMAGE_CONTROL_HELP,
    DISPOSITION_DAMAGE_TABLE_HELP,
    DISPOSITION_DESCRIPTIONS,
    GamePhase,
    PRIORITY_LEVELS,
    SCENARIOS,
    SCENARIO_BY_KEY,
    SCENARIO_CATEGORIES,
    SCENARIO_MAP_FILES,
    REFERENCE_ENTRIES,
    ReferenceEntry,
    TURN_SEQUENCE_HELP,
    TacticalGameState,
    TacticalUnitState,
    TrackState,
    UnitDisposition,
    UnitKind,
    apply_critical_rule,
    critical_targets,
    opponent_victory_points_from_local_fleet,
    random_scenario,
    random_priority_level,
    random_player_role,
    roll_loss_expression,
    special_action_availability,
)


_USER_ROLE = int(Qt.ItemDataRole.UserRole)
_CRAFT_GROUP_IDS_ROLE = _USER_ROLE + 20
_MUTED = QColor(128, 128, 128)
_MODIFIED_RED = "#c62828"
_TRAIT_DIVIDER = QColor("#4b5563")


class _ArithmeticSpinBox(QLineEdit):
    """Spin-box-compatible editor that reliably accepts ``+`` and ``-``.

    QSpinBox consumes leading signs before its validator receives keyboard
    input on some Qt/Windows combinations. A small compatibility editor keeps
    the existing Tactical Assistant API while allowing expressions such as
    ``-8`` and ``+4`` to be typed normally.
    """

    valueChanged = Signal(int)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._minimum = 0
        self._maximum = 0
        self._value = 0
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.editingFinished.connect(self.interpretText)

    def lineEdit(self) -> "_ArithmeticSpinBox":
        return self

    def setRange(self, minimum: int, maximum: int) -> None:
        self._minimum = int(minimum)
        self._maximum = max(self._minimum, int(maximum))
        self.setValue(self._value)

    def minimum(self) -> int:
        return self._minimum

    def maximum(self) -> int:
        return self._maximum

    def value(self) -> int:
        return self._value

    def setValue(self, value: int) -> None:
        resolved = max(self._minimum, min(self._maximum, int(value)))
        changed = resolved != self._value
        self._value = resolved
        self.setText(str(resolved))
        if changed and not self.signalsBlocked():
            self.valueChanged.emit(resolved)

    def interpretText(self) -> None:
        text = self.text().strip().replace(" ", "")
        if not text:
            self.setText(str(self._value))
            return
        if not re.fullmatch(r"[+-]?\d+", text):
            self.setText(str(self._value))
            self.selectAll()
            return
        value = int(text)
        if text.startswith(("+", "-")):
            value = self._value + value
        self.setValue(value)


class _PersistentToolTipFilter(QObject):
    """Keep rules tooltips visible until the pointer leaves their item."""

    _SHOW_TIME_MS = 3_600_000

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._resolvers: dict[QObject, object] = {}
        self._active_widget: QObject | None = None
        self._active_rect = QRect()

    def install_widget(self, widget: QWidget) -> None:
        self._install(widget, lambda _pos: (widget.toolTip(), widget.rect()))

    def install_tree(self, tree: QTreeWidget) -> None:
        viewport = tree.viewport()

        def resolve(pos):
            item = tree.itemAt(pos)
            if item is None:
                return "", QRect()
            column = max(0, tree.columnAt(pos.x()))
            return item.toolTip(column), tree.visualItemRect(item)

        self._install(viewport, resolve)

    def install_combo(self, combo: QComboBox) -> None:
        view = combo.view()
        viewport = view.viewport()

        def resolve(pos):
            index = view.indexAt(pos)
            if not index.isValid():
                return "", QRect()
            text = str(index.data(Qt.ItemDataRole.ToolTipRole) or "")
            return text, view.visualRect(index)

        self._install(viewport, resolve)

    def _install(self, widget: QWidget, resolver) -> None:
        self._resolvers[widget] = resolver
        widget.setMouseTracking(True)
        widget.installEventFilter(self)

    @staticmethod
    def _event_position(event):
        position = getattr(event, "position", None)
        if callable(position):
            return position().toPoint()
        return event.pos()

    @staticmethod
    def _event_global_position(event):
        position = getattr(event, "globalPosition", None)
        if callable(position):
            return position().toPoint()
        return event.globalPos()

    def eventFilter(self, watched: QObject, event) -> bool:  # type: ignore[override]
        event_type = event.type()
        if event_type == QEvent.Type.ToolTip and watched in self._resolvers:
            text, rect = self._resolvers[watched](self._event_position(event))
            if text:
                QToolTip.showText(
                    self._event_global_position(event),
                    str(text),
                    watched,
                    rect,
                    self._SHOW_TIME_MS,
                )
                self._active_widget = watched
                self._active_rect = QRect(rect)
                event.accept()
                return True
        elif event_type == QEvent.Type.Leave and watched is self._active_widget:
            QToolTip.hideText()
            self._active_widget = None
            self._active_rect = QRect()
        elif event_type == QEvent.Type.MouseMove and watched is self._active_widget:
            if not self._active_rect.contains(self._event_position(event)):
                QToolTip.hideText()
                self._active_widget = None
                self._active_rect = QRect()
        return super().eventFilter(watched, event)


class _CraftCountEditor(QWidget):
    """High-DPI-safe horizontal ``minus / value / plus`` counter."""

    valueChanged = Signal(int)

    def __init__(
        self,
        label: str,
        tooltip: str,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._minimum = 0
        self._maximum = 0
        self._value = 0

        self.decrement_button = QToolButton()
        self.decrement_button.setText("−")
        self.decrement_button.setAccessibleName(f"Decrease {label}")
        self.increment_button = QToolButton()
        self.increment_button.setText("+")
        self.increment_button.setAccessibleName(f"Increase {label}")
        for button in (self.decrement_button, self.increment_button):
            button.setFixedSize(22, 26)
            button.setToolTip(tooltip)

        self.value_label = QLabel("0")
        self.value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.value_label.setMinimumWidth(20)
        self.value_label.setAccessibleName(f"{label} flights")
        self.value_label.setToolTip(tooltip)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(1, 0, 1, 0)
        layout.setSpacing(1)
        layout.addWidget(self.decrement_button)
        layout.addWidget(self.value_label, 1)
        layout.addWidget(self.increment_button)
        self.setFixedWidth(68)
        self.setToolTip(tooltip)

        self.decrement_button.clicked.connect(lambda: self.setValue(self._value - 1))
        self.increment_button.clicked.connect(lambda: self.setValue(self._value + 1))
        self._update_buttons()

    def setRange(self, minimum: int, maximum: int) -> None:
        self._minimum = int(minimum)
        self._maximum = max(self._minimum, int(maximum))
        self.setValue(self._value)

    def value(self) -> int:
        return self._value

    def setValue(self, value: int) -> None:
        resolved = max(self._minimum, min(self._maximum, int(value)))
        changed = resolved != self._value
        self._value = resolved
        self.value_label.setText(str(resolved))
        self._update_buttons()
        if changed and not self.signalsBlocked():
            self.valueChanged.emit(resolved)

    def _update_buttons(self) -> None:
        self.decrement_button.setEnabled(self._value > self._minimum)
        self.increment_button.setEnabled(self._value < self._maximum)


class _CraftGroupEditor(QWidget):
    """Coordinate three linked counters while each occupies its own column."""

    counts_changed = Signal(int, int, int)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._total = 0
        self._loading = False
        self.ready_spin = _CraftCountEditor(
            "Ready",
            "Flights aboard the carrier and ready to launch.",
        )
        self.launched_spin = _CraftCountEditor(
            "Launched",
            "Flights currently launched on the table.",
        )
        self.lost_spin = _CraftCountEditor(
            "Lost",
            "Flights destroyed or otherwise lost.",
        )

        # This object coordinates the three controls, but the controls are
        # installed into separate Battle Roster columns. The coordinator itself
        # remains hidden and owned by the tree for the lifetime of the row.
        self.hide()

        self.ready_spin.valueChanged.connect(lambda value: self._changed("ready", value))
        self.launched_spin.valueChanged.connect(lambda value: self._changed("launched", value))
        self.lost_spin.valueChanged.connect(lambda value: self._changed("lost", value))

    @property
    def controls(self) -> tuple[_CraftCountEditor, _CraftCountEditor, _CraftCountEditor]:
        return self.ready_spin, self.launched_spin, self.lost_spin

    def set_counts(self, ready: int, launched: int, lost: int) -> None:
        self._total = max(0, int(ready) + int(launched) + int(lost))
        self._set_values(int(ready), int(launched), int(lost))

    def _set_values(self, ready: int, launched: int, lost: int) -> None:
        values = (max(0, ready), max(0, launched), max(0, lost))
        self._loading = True
        try:
            for spin, value in zip(
                (self.ready_spin, self.launched_spin, self.lost_spin),
                values,
            ):
                spin.setRange(0, self._total)
                spin.setValue(value)
        finally:
            self._loading = False

    def _changed(self, changed: str, value: int) -> None:
        if self._loading:
            return
        counts = {
            "ready": self.ready_spin.value(),
            "launched": self.launched_spin.value(),
            "lost": self.lost_spin.value(),
        }
        # The emitting spin already contains ``value``. Reconstruct its prior
        # value from the invariant total, then transfer the difference.
        previous = self._total - sum(
            count for name, count in counts.items() if name != changed
        )
        delta = int(value) - previous
        counts[changed] = int(value)

        priorities = {
            "ready": ("launched", "lost"),
            "launched": ("ready", "lost"),
            "lost": ("ready", "launched"),
        }[changed]
        if delta > 0:
            remaining = delta
            for name in priorities:
                transfer = min(remaining, counts[name])
                counts[name] -= transfer
                remaining -= transfer
        elif delta < 0:
            destination = "ready" if changed != "ready" else "launched"
            counts[destination] += -delta

        correction = self._total - sum(counts.values())
        if correction:
            destination = "ready" if changed != "ready" else "launched"
            counts[destination] = max(0, counts[destination] + correction)
        self._set_values(counts["ready"], counts["launched"], counts["lost"])
        self.counts_changed.emit(counts["ready"], counts["launched"], counts["lost"])


class _TrackEditor(QGroupBox):
    """Compact current/maximum editor supporting ``-8``, ``+4``, or ``24``."""

    current_changed = Signal(int)

    def __init__(
        self,
        title: str,
        parent: QWidget | None = None,
        *,
        allow_negative: bool = False,
    ) -> None:
        super().__init__(title, parent)
        self._allow_negative = bool(allow_negative)
        self.current_spin = _ArithmeticSpinBox()
        self.current_spin.setRange(0, 0)
        self.current_spin.setEnabled(False)
        self.current_spin.setToolTip(
            "Enter an absolute value (24), subtract damage (-8), or restore points (+4)."
        )
        self.maximum_label = QLabel("-")
        self.detail_label = QLabel("")
        self.detail_label.setObjectName("pageSubtitle")
        self.detail_label.setWordWrap(True)

        minus_button = QPushButton("-")
        plus_button = QPushButton("+")
        minus_button.setFixedWidth(34)
        plus_button.setFixedWidth(34)
        minus_button.clicked.connect(
            lambda: self.current_spin.setValue(
                max(self.current_spin.minimum(), self.current_spin.value() - 1)
            )
        )
        plus_button.clicked.connect(
            lambda: self.current_spin.setValue(
                min(self.current_spin.maximum(), self.current_spin.value() + 1)
            )
        )
        self._minus_button = minus_button
        self._plus_button = plus_button

        row = QHBoxLayout()
        row.addWidget(minus_button)
        row.addWidget(self.current_spin, 1)
        row.addWidget(QLabel("/"))
        row.addWidget(self.maximum_label)
        row.addWidget(plus_button)

        layout = QVBoxLayout(self)
        layout.addLayout(row)
        layout.addWidget(self.detail_label)

        self.current_spin.valueChanged.connect(self.current_changed.emit)

    def set_track(
        self,
        track: TrackState,
        *,
        operational: bool = True,
        operational_note: str = "",
    ) -> None:
        self.current_spin.blockSignals(True)
        try:
            available = track.available and track.current is not None and track.maximum is not None
            enabled = available and operational
            self.current_spin.setEnabled(enabled)
            self._minus_button.setEnabled(enabled)
            self._plus_button.setEnabled(enabled)
            if available:
                minimum = -9999 if self._allow_negative else 0
                self.current_spin.setRange(minimum, int(track.maximum))
                self.current_spin.setValue(int(track.current))
                self.maximum_label.setText(str(track.maximum))
                details: list[str] = []
                if track.threshold is not None:
                    details.append(f"Threshold {track.threshold}")
                if track.recovery:
                    details.append(f"Recovery {track.recovery}")
                if operational_note:
                    details.append(operational_note)
                self.detail_label.setText("  |  ".join(details))
                self.current_spin.setStyleSheet(
                    "color: #c62828; font-weight: 700;" if not operational else ""
                )
            else:
                self.current_spin.setRange(0, 0)
                self.current_spin.setValue(0)
                self.maximum_label.setText("-")
                self.detail_label.setText("Not applicable")
                self.current_spin.setStyleSheet("")
        finally:
            self.current_spin.blockSignals(False)


class _RulesDialog(QDialog):
    """Plain rules dialog without the operating-system alert sound."""

    def __init__(
        self,
        title: str,
        text: str,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.help_title = str(title or "Rules")
        self.help_text = str(text or "No rules are available for the current selection.")
        self.setWindowTitle(self.help_title)
        self.resize(760, 560)

        text_box = QTextEdit()
        text_box.setReadOnly(True)
        text_box.setPlainText(self.help_text)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addWidget(text_box, 1)
        layout.addWidget(buttons)


class _QuickReferenceDialog(QDialog):
    """Modeless, searchable table reference with live Codex results."""

    def __init__(self, codex=None, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("DFS Quick Reference")
        self.setModal(False)
        self.resize(920, 680)
        self._codex = codex
        self._base_entries = list(REFERENCE_ENTRIES)
        self._base_entries.extend(self._common_codex_entries())
        self._visible_entries: list[ReferenceEntry] = []

        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText(
            "Search procedures, conditions, actions, ship traits, or weapon traits..."
        )
        self.category_combo = QComboBox()
        self.category_combo.addItem("All categories", "")
        for category in sorted({entry.category for entry in self._base_entries}):
            self.category_combo.addItem(category, category)

        search_row = QHBoxLayout()
        search_row.addWidget(QLabel("Search"))
        search_row.addWidget(self.search_edit, 1)
        search_row.addWidget(self.category_combo)

        self.entry_list = QListWidget()
        self.entry_list.setMinimumWidth(280)
        self.detail_box = QTextEdit()
        self.detail_box.setReadOnly(True)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(self.entry_list)
        splitter.addWidget(self.detail_box)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 3)
        splitter.setSizes([300, 600])

        close_button = QPushButton("Close")
        close_button.clicked.connect(self.close)
        button_row = QHBoxLayout()
        button_row.addStretch(1)
        button_row.addWidget(close_button)

        layout = QVBoxLayout(self)
        layout.addLayout(search_row)
        layout.addWidget(splitter, 1)
        layout.addLayout(button_row)

        self.search_edit.textChanged.connect(self._refresh_entries)
        self.category_combo.currentIndexChanged.connect(self._refresh_entries)
        self.entry_list.currentRowChanged.connect(self._show_entry)
        self._refresh_entries()

    def _common_codex_entries(self) -> list[ReferenceEntry]:
        getter = getattr(self._codex, "get", None)
        if not callable(getter):
            return []
        entries: list[ReferenceEntry] = []
        for name in COMMON_CODEX_RULE_NAMES:
            try:
                entry = getter(name)
            except Exception:
                entry = None
            if entry is None:
                continue
            entries.append(
                ReferenceEntry(
                    str(entry.title),
                    str(entry.category or "Codex"),
                    str(entry.text),
                    str(entry.source),
                )
            )
        return entries

    @staticmethod
    def _matches(entry: ReferenceEntry, query: str, category: str) -> bool:
        if category and entry.category != category:
            return False
        if not query:
            return True
        searchable = " ".join((entry.title, entry.category, entry.text, entry.source)).casefold()
        return all(term in searchable for term in query.casefold().split())

    def _codex_search_entries(self, query: str) -> list[ReferenceEntry]:
        search = getattr(self._codex, "search", None)
        if not query or not callable(search):
            return []
        try:
            matches = search(query)
        except Exception:
            return []
        return [
            ReferenceEntry(
                str(entry.title),
                str(entry.category or "Codex"),
                str(entry.text),
                str(entry.source),
            )
            for entry in matches
        ]

    def _refresh_entries(self, *_args) -> None:
        query = self.search_edit.text().strip()
        category = str(self.category_combo.currentData() or "")
        candidates = [*self._base_entries, *self._codex_search_entries(query)]
        visible: list[ReferenceEntry] = []
        seen: set[tuple[str, str]] = set()
        for entry in candidates:
            key = (entry.title.casefold(), entry.category.casefold())
            if key in seen or not self._matches(entry, query, category):
                continue
            seen.add(key)
            visible.append(entry)
        visible.sort(key=lambda entry: (entry.category.casefold(), entry.title.casefold()))
        self._visible_entries = visible

        self.entry_list.blockSignals(True)
        try:
            self.entry_list.clear()
            for entry in visible:
                item = QListWidgetItem(entry.title)
                item.setToolTip(entry.category)
                self.entry_list.addItem(item)
        finally:
            self.entry_list.blockSignals(False)
        if visible:
            self.entry_list.setCurrentRow(0)
            self._show_entry(0)
        else:
            self.detail_box.setPlainText("No matching quick-reference or Codex entries.")

    def _show_entry(self, row: int) -> None:
        if row < 0 or row >= len(self._visible_entries):
            return
        entry = self._visible_entries[row]
        source = f"\n\nSource: {entry.source}" if entry.source else ""
        self.detail_box.setPlainText(
            f"{entry.title}\n{entry.category}\n\n{entry.text}{source}"
        )


class _ScenarioMapDialog(QDialog):
    """Silent scrollable viewer for a printed scenario deployment map."""

    def __init__(
        self,
        title: str,
        image_path: Path,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle(title)
        self.resize(920, 760)

        pixmap = QPixmap(str(image_path))
        image_label = QLabel()
        image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        if pixmap.isNull():
            image_label.setText(f"Unable to load deployment map:\n{image_path}")
        else:
            image_label.setPixmap(pixmap)
            image_label.setMinimumSize(pixmap.size())

        scroll = QScrollArea()
        scroll.setWidgetResizable(False)
        scroll.setAlignment(Qt.AlignmentFlag.AlignCenter)
        scroll.setWidget(image_label)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addWidget(scroll, 1)
        layout.addWidget(buttons)


class _HelpGroupBox(QGroupBox):
    """Group box with a visibly interactive, silent rules title.

    Hovering exposes the current rule text and clicking the highlighted title
    opens the same material in a readable dialog. Scenario, Critical Results,
    and Disposition use the same treatment so players can recognize active
    headers consistently.
    """

    def __init__(self, title: str, help_title: str, help_text: str) -> None:
        display_title = title if "ⓘ" in title else f"{title}  ⓘ"
        super().__init__(display_title)
        self._help_title = help_title
        self._help_text = help_text
        self.setObjectName("interactiveHelpGroup")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet(
            "QGroupBox#interactiveHelpGroup::title {"
            " color: palette(highlight);"
            " font-weight: 700;"
            " border: 1px solid palette(highlight);"
            " border-radius: 4px;"
            " padding: 1px 7px;"
            "}"
        )
        self.set_help_content(help_title, help_text)

    def set_help_content(self, help_title: str, help_text: str) -> None:
        self._help_title = str(help_title or "Rules")
        self._help_text = str(help_text or "No rules are available for the current selection.")
        self.setToolTip(self._help_text)

    def show_help(self) -> None:
        _RulesDialog(self._help_title, self._help_text, self).exec()

    def mousePressEvent(self, event) -> None:  # type: ignore[override]
        if event.position().y() <= 34:
            self.show_help()
            event.accept()
            return
        super().mousePressEvent(event)


class _BattleReportDialog(QDialog):
    """End-game summary with automatic points yielded by the local fleet."""

    def __init__(self, game: TacticalGameState, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._game = game
        self._automatic = opponent_victory_points_from_local_fleet(game)
        self.setWindowTitle("Battle Report")
        self.resize(720, 650)

        self.victory_points_spin = QSpinBox()
        self.victory_points_spin.setRange(0, 9999)
        self.victory_points_spin.setValue(game.victory_points)
        self.opponent_objective_spin = QSpinBox()
        self.opponent_objective_spin.setRange(0, 9999)
        self.opponent_objective_spin.setValue(
            max(0, game.opponent_victory_points - self._automatic.automatic_points)
        )
        self.opponent_points_spin = QSpinBox()
        self.opponent_points_spin.setRange(0, 9999)
        self.opponent_points_spin.setReadOnly(True)
        self.notes_edit = QTextEdit()
        self.notes_edit.setPlaceholderText(
            "Scenario bonuses, objective results, holding ground, or other report notes..."
        )
        self.notes_edit.setPlainText(game.battle_report_notes)
        self.summary = QTextEdit()
        self.summary.setReadOnly(True)
        self.scoring_breakdown = QTextEdit()
        self.scoring_breakdown.setReadOnly(True)
        self.scoring_breakdown.setMaximumHeight(180)

        scenario = SCENARIO_BY_KEY.get(game.scenario_key)
        scenario_name = scenario.name if scenario is not None else "None selected"
        self.scenario_label = QLabel(
            f"Scenario: {scenario_name}  |  Priority: {game.scenario_priority or 'Not selected'}"
        )
        self.scenario_label.setWordWrap(True)
        self.scenario_label.setToolTip(scenario.display_text if scenario is not None else "")

        points = QFormLayout()
        points.addRow("Your Victory Points", self.victory_points_spin)
        points.addRow("Opponent automatic unit VP", QLabel(str(self._automatic.automatic_points)))
        points.addRow("Opponent scenario/objective bonus", self.opponent_objective_spin)
        points.addRow("Opponent total VP", self.opponent_points_spin)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        ok = buttons.button(QDialogButtonBox.StandardButton.Ok)
        if ok is not None:
            ok.setText("End Game")
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addWidget(self.scenario_label)
        layout.addLayout(points)
        layout.addWidget(QLabel("Automatic Opponent Scoring"))
        layout.addWidget(self.scoring_breakdown)
        layout.addWidget(QLabel("Battle Summary"))
        layout.addWidget(self.summary, 1)
        layout.addWidget(QLabel("Report Notes"))
        layout.addWidget(self.notes_edit)
        layout.addWidget(buttons)

        self.victory_points_spin.valueChanged.connect(self._refresh_summary)
        self.opponent_objective_spin.valueChanged.connect(self._refresh_summary)
        self._refresh_summary()

    def _refresh_summary(self, *_args) -> None:
        own = self.victory_points_spin.value()
        opponent = self._automatic.automatic_points + self.opponent_objective_spin.value()
        self.opponent_points_spin.setValue(opponent)
        result = "Victory" if own > opponent else ("Defeat" if own < opponent else "Draw")
        platforms = [unit for unit in self._game.units if unit.kind is UnitKind.PLATFORM]
        craft = [unit for unit in self._game.units if unit.kind is UnitKind.CRAFT]
        lines = [
            f"Game: {self._game.name}",
            f"Fleet: {self._game.source_fleet_name}",
            f"Ended after Turn {self._game.turn_number} ({self._game.phase.value.title()})",
            f"Result: {result} - {own} to {opponent} VP",
            "",
            f"Platforms: {len(platforms)} total; "
            f"{sum(unit.is_destroyed for unit in platforms)} destroyed; "
            f"{sum(unit.is_adrift and not unit.is_destroyed for unit in platforms)} adrift; "
            f"{sum(unit.is_surrendered for unit in platforms)} surrendered; "
            f"{sum(unit.is_withdrawn for unit in platforms)} withdrawn; "
            f"{sum(unit.is_crippled and not unit.is_destroyed for unit in platforms)} crippled; "
            f"{sum(unit.is_skeleton_crew and not unit.is_destroyed for unit in platforms)} skeleton crew",
            f"Craft: {len(craft)} total; "
            f"{sum(unit.effective_craft_status == 'ready' for unit in craft)} ready; "
            f"{sum(unit.effective_craft_status == 'launched' for unit in craft)} launched; "
            f"{sum(unit.effective_craft_status == 'lost' for unit in craft)} lost",
            f"Active critical effects: {sum(len(unit.active_critical_hits) for unit in self._game.units)}",
        ]
        self.summary.setPlainText("\n".join(lines))

        breakdown = [
            f"{entry.label}: {entry.points} VP - {entry.reason}"
            for entry in self._automatic.entries
        ]
        if not breakdown:
            breakdown.append("No automatic unit Victory Points currently apply.")
        if self._automatic.note:
            breakdown.extend(("", self._automatic.note))
        scenario = SCENARIO_BY_KEY.get(self._game.scenario_key)
        if scenario is not None:
            breakdown.extend(("", f"Printed victory rule: {scenario.victory}"))
        self.scoring_breakdown.setPlainText("\n".join(breakdown))


class TacticalAssistantPage(QWidget):
    """Load a Fleet Builder roster and maintain its live battle state."""

    GAME_EXTENSION = ".dfs-game.json"

    def __init__(self, context: ApplicationContext, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._context = context
        self._service = context.tactical_games
        self._game: TacticalGameState | None = None
        self._current_path: Path | None = None
        self._dirty = False
        self._loading_controls = False
        self._unit_items: dict[str, QTreeWidgetItem] = {}
        self._craft_group_items: dict[tuple[str, str], QTreeWidgetItem] = {}
        self._craft_group_editors: list[_CraftGroupEditor] = []
        self._active_craft_unit_ids: tuple[str, ...] = ()
        self._quick_reference_dialog: _QuickReferenceDialog | None = None
        self._tooltip_filter = _PersistentToolTipFilter(self)
        self._detail_groups_stacked = False
        self._fighter_detail_mode = False
        self._traits_two_column = True
        self._header_wrapped: bool | None = None

        self._build_ui()
        self._install_persistent_tooltips()
        self._show_empty_state()

    @property
    def current_game(self) -> TacticalGameState | None:
        return self._game

    @property
    def current_path(self) -> Path | None:
        return self._current_path

    @property
    def is_dirty(self) -> bool:
        return self._dirty

    def _build_ui(self) -> None:
        self.page_title = QLabel("Tactical Assistant")
        self.page_title.setObjectName("pageTitle")

        self.dirty_label = QLabel("")
        self.dirty_label.setObjectName("pageSubtitle")

        self.new_from_fleet_button = QPushButton("New from Fleet...")
        self.open_game_button = QPushButton("Open Game...")
        self.save_button = QPushButton("Save")
        self.save_as_button = QPushButton("Save As...")
        self.quick_reference_button = QPushButton("Quick Reference")
        self.new_from_fleet_button.clicked.connect(self.new_from_fleet)
        self.open_game_button.clicked.connect(self.open_game)
        self.save_button.clicked.connect(self.save_game)
        self.save_as_button.clicked.connect(lambda: self.save_game(save_as=True))
        self.quick_reference_button.clicked.connect(self._show_quick_reference)

        self.header_widget = QWidget()
        self.header_layout = QGridLayout(self.header_widget)
        self.header_layout.setContentsMargins(0, 0, 0, 0)
        self.header_layout.setHorizontalSpacing(8)
        self.header_layout.setVerticalSpacing(4)
        self._set_header_wrapped(False)

        game_group = self._build_game_state_group()
        roster_group = self._build_roster_group()
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.addWidget(game_group)
        left_layout.addWidget(roster_group, 1)

        detail_panel = self._build_detail_panel()

        self.main_splitter = QSplitter(Qt.Orientation.Horizontal)
        self.main_splitter.addWidget(left_panel)
        self.main_splitter.addWidget(detail_panel)
        self.main_splitter.setChildrenCollapsible(False)
        self.main_splitter.setStretchFactor(0, 2)
        self.main_splitter.setStretchFactor(1, 5)
        self.main_splitter.setSizes([430, 980])

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(7)
        layout.addWidget(self.header_widget)
        layout.addWidget(self.main_splitter, 1)

        self._connect_signals()

    def resizeEvent(self, event) -> None:  # type: ignore[override]
        super().resizeEvent(event)
        if hasattr(self, "header_layout"):
            self._set_header_wrapped(event.size().width() < 1180)

    def _set_header_wrapped(self, wrapped: bool) -> None:
        resolved = bool(wrapped)
        if resolved == self._header_wrapped:
            return
        self._header_wrapped = resolved

        widgets = (
            self.page_title,
            self.new_from_fleet_button,
            self.open_game_button,
            self.quick_reference_button,
            self.dirty_label,
            self.save_button,
            self.save_as_button,
        )
        for widget in widgets:
            self.header_layout.removeWidget(widget)
        for column in range(8):
            self.header_layout.setColumnStretch(column, 0)

        center = Qt.AlignmentFlag.AlignVCenter
        if not resolved:
            self.header_layout.addWidget(self.page_title, 0, 0, alignment=center)
            self.header_layout.addWidget(self.new_from_fleet_button, 0, 1, alignment=center)
            self.header_layout.addWidget(self.open_game_button, 0, 2, alignment=center)
            self.header_layout.addWidget(self.quick_reference_button, 0, 3, alignment=center)
            self.header_layout.setColumnStretch(4, 1)
            self.header_layout.addWidget(self.dirty_label, 0, 5, alignment=center)
            self.header_layout.addWidget(self.save_button, 0, 6, alignment=center)
            self.header_layout.addWidget(self.save_as_button, 0, 7, alignment=center)
            return

        self.header_layout.addWidget(self.page_title, 0, 0, 1, 4, alignment=center)
        self.header_layout.setColumnStretch(4, 1)
        self.header_layout.addWidget(self.dirty_label, 0, 5, 1, 2, alignment=center)
        self.header_layout.addWidget(self.new_from_fleet_button, 1, 0, alignment=center)
        self.header_layout.addWidget(self.open_game_button, 1, 1, alignment=center)
        self.header_layout.addWidget(self.quick_reference_button, 1, 2, alignment=center)
        self.header_layout.setColumnStretch(3, 1)
        self.header_layout.addWidget(self.save_button, 1, 5, alignment=center)
        self.header_layout.addWidget(self.save_as_button, 1, 6, alignment=center)

    def _build_game_state_group(self) -> QGroupBox:
        self.game_name_edit = QLineEdit()
        self.game_name_edit.setPlaceholderText("Battle name")
        self.source_fleet_label = QLabel("No fleet loaded")
        self.source_fleet_label.setWordWrap(True)

        self.scenario_combo = QComboBox()
        self.scenario_combo.setMaxVisibleItems(32)
        self.scenario_combo.setMinimumContentsLength(18)
        self.scenario_combo.setSizeAdjustPolicy(
            QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon
        )
        self.scenario_combo.addItem("None", "")
        self.scenario_combo.addItem("Random Standard Scenario", "__random__")
        for category in SCENARIO_CATEGORIES:
            self.scenario_combo.insertSeparator(self.scenario_combo.count())
            for scenario in (item for item in SCENARIOS if item.category == category):
                self.scenario_combo.addItem(f"{category}: {scenario.name}", scenario.key)
                self.scenario_combo.setItemData(
                    self.scenario_combo.count() - 1,
                    scenario.display_text,
                    Qt.ItemDataRole.ToolTipRole,
                )

        self.scenario_map_button = QPushButton("Map")
        self.scenario_map_button.setMaximumWidth(72)
        self.scenario_map_button.setToolTip(
            "Show the printed deployment map for the selected scenario."
        )
        self.scenario_map_button.setEnabled(False)

        self.scenario_priority_combo = QComboBox()
        self.scenario_priority_combo.addItem("Select...", "")
        for priority in PRIORITY_LEVELS:
            self.scenario_priority_combo.addItem(priority, priority)
        self.random_priority_button = QPushButton("Random")
        self.random_priority_button.setToolTip(
            "Roll the published 2d6 random scenario Priority Level table."
        )
        self.random_priority_button.setMaximumWidth(82)

        self.player_role_combo = QComboBox()
        self.player_role_combo.addItem("Unspecified", "")
        self.player_role_combo.addItem("Attacker", "attacker")
        self.player_role_combo.addItem("Defender", "defender")
        self.random_role_button = QPushButton("Random")
        self.random_role_button.setToolTip("Randomly choose Attacker or Defender.")
        self.random_role_button.setMaximumWidth(82)

        # Retained as a hidden compatibility field for existing tests and saved
        # layouts. Scenario guidance now lives entirely in the active header.
        self.scenario_rules_label = QLabel("No scenario selected")
        self.scenario_rules_label.setWordWrap(True)
        self.scenario_rules_label.setObjectName("pageSubtitle")
        self.scenario_rules_label.hide()

        self.turn_spin = QSpinBox()
        self.turn_spin.setRange(1, 999)
        self.phase_combo = QComboBox()
        for phase in GamePhase:
            self.phase_combo.addItem(phase.value.replace("_", " ").title(), phase.value)
        self.turn_order_button = QPushButton("Turn Order")
        self.turn_order_button.setToolTip(TURN_SEQUENCE_HELP)
        self.advance_turn_button = QPushButton("Advance Turn")
        self.end_game_button = QPushButton("End Game")

        turn_phase_row = QHBoxLayout()
        turn_phase_row.addWidget(QLabel("Turn"))
        turn_phase_row.addWidget(self.turn_spin, 1)
        turn_phase_row.addWidget(QLabel("Phase"))
        turn_phase_row.addWidget(self.phase_combo, 2)
        turn_phase_row.addWidget(self.turn_order_button, 1)

        turn_buttons = QHBoxLayout()
        turn_buttons.addWidget(self.advance_turn_button, 1)
        turn_buttons.addWidget(self.end_game_button)

        scenario_grid = QGridLayout()
        scenario_grid.addWidget(self.scenario_combo, 0, 0, 1, 5)
        scenario_grid.addWidget(self.scenario_map_button, 0, 5)
        scenario_grid.addWidget(QLabel("Priority"), 1, 0)
        scenario_grid.addWidget(self.scenario_priority_combo, 1, 1)
        scenario_grid.addWidget(self.random_priority_button, 1, 2)
        scenario_grid.addWidget(QLabel("Role"), 1, 3)
        scenario_grid.addWidget(self.player_role_combo, 1, 4)
        scenario_grid.addWidget(self.random_role_button, 1, 5)
        self.scenario_group = _HelpGroupBox(
            "Scenario",
            "Scenario Rules",
            "Select a scenario to view its setup, special rules, game length, and victory conditions.",
        )
        self.scenario_group.setLayout(scenario_grid)

        grid = QGridLayout()
        grid.addWidget(QLabel("Game"), 0, 0)
        grid.addWidget(self.game_name_edit, 0, 1, 1, 3)
        grid.addWidget(QLabel("Fleet"), 1, 0)
        grid.addWidget(self.source_fleet_label, 1, 1, 1, 3)
        grid.addWidget(self.scenario_group, 2, 0, 1, 4)
        grid.addLayout(turn_phase_row, 3, 0, 1, 4)
        grid.addLayout(turn_buttons, 4, 0, 1, 4)
        group = QGroupBox("Game State")
        group.setLayout(grid)
        self.game_state_group = group
        return group

    def _build_roster_group(self) -> QGroupBox:
        self.unit_tree = QTreeWidget()
        self.unit_tree.setColumnCount(6)
        self.unit_tree.setHeaderLabels(
            ("Unit", "Type", "Status", "Ready", "Launched", "Lost")
        )
        self.unit_tree.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.unit_tree.setRootIsDecorated(True)
        self.unit_tree.setAlternatingRowColors(True)
        self.unit_tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        header = self.unit_tree.header()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        for column in (3, 4, 5):
            header.setSectionResizeMode(column, QHeaderView.ResizeMode.Fixed)
        self.unit_tree.setColumnWidth(3, 72)
        self.unit_tree.setColumnWidth(4, 88)
        self.unit_tree.setColumnWidth(5, 72)
        self.unit_tree.viewport().installEventFilter(self)
        self.unit_summary_label = QLabel("No game loaded")
        self.unit_summary_label.setWordWrap(True)

        layout = QVBoxLayout()
        layout.addWidget(self.unit_tree, 1)
        layout.addWidget(self.unit_summary_label)
        group = QGroupBox("Battle Roster")
        group.setLayout(layout)
        self.roster_group = group
        return group

    def _build_detail_panel(self) -> QScrollArea:
        self.unit_title = QLabel("Select a unit")
        self.unit_title.setObjectName("pageTitle")
        self.unit_subtitle = QLabel("")
        self.unit_subtitle.setObjectName("pageSubtitle")
        self.unit_subtitle.setWordWrap(True)
        self.unit_reference_label = QLabel("")
        self.unit_reference_label.setTextFormat(Qt.TextFormat.RichText)
        self.unit_reference_label.setWordWrap(True)
        self.unit_effects_label = QLabel("")
        self.unit_effects_label.setWordWrap(True)
        self.unit_effects_label.setObjectName("pageSubtitle")

        self.damage_editor = _TrackEditor("Damage", allow_negative=True)
        self.crew_editor = _TrackEditor("Crew")
        self.shields_editor = _TrackEditor("Shields")
        self.tracks_widget = QWidget()
        tracks = QHBoxLayout(self.tracks_widget)
        tracks.setContentsMargins(0, 0, 0, 0)
        tracks.setSpacing(6)
        tracks.addWidget(self.damage_editor, 1)
        tracks.addWidget(self.crew_editor, 1)
        tracks.addWidget(self.shields_editor, 1)

        self.fighter_overview_label = QLabel("")
        self.fighter_overview_label.setWordWrap(True)
        fighter_overview_layout = QVBoxLayout()
        fighter_overview_layout.addWidget(self.fighter_overview_label)
        self.fighter_overview_group = QGroupBox("Fighter Flight Status")
        self.fighter_overview_group.setLayout(fighter_overview_layout)
        self.fighter_overview_group.hide()

        status_and_critical_widget = QWidget()
        status_and_critical = QHBoxLayout(status_and_critical_widget)
        status_and_critical.setContentsMargins(0, 0, 0, 0)
        status_and_critical.setSpacing(6)
        status_and_critical.addWidget(self._build_status_group(), 1)
        status_and_critical.addWidget(self._build_critical_group(), 1)
        status_and_critical.setSizeConstraint(QLayout.SizeConstraint.SetMinimumSize)
        self.status_and_critical_layout = status_and_critical
        self.status_and_critical_widget = status_and_critical_widget

        self.traits_group = self._build_traits_group()

        self.detail_tabs = QTabWidget()
        self.detail_tabs.addTab(self._build_source_notes_group(), "Source Notes")
        self.detail_tabs.addTab(self._build_unit_notes_group(), "Unit Notes")
        self.detail_tabs.setMinimumHeight(165)
        self.detail_tabs.setMaximumHeight(190)

        self.unit_detail_widget = QWidget()
        detail_layout = QVBoxLayout(self.unit_detail_widget)
        detail_layout.setContentsMargins(6, 4, 6, 4)
        detail_layout.setSpacing(4)
        detail_layout.setSizeConstraint(QLayout.SizeConstraint.SetMinimumSize)
        detail_layout.addWidget(self.unit_title)
        detail_layout.addWidget(self.unit_subtitle)
        detail_layout.addWidget(self.unit_reference_label)
        detail_layout.addWidget(self.unit_effects_label)
        detail_layout.addWidget(self.fighter_overview_group)
        detail_layout.addWidget(self.tracks_widget)
        detail_layout.addWidget(self._build_weapons_group())
        detail_layout.addWidget(self.traits_group)
        detail_layout.addWidget(status_and_critical_widget)
        detail_layout.addWidget(self.detail_tabs)
        detail_layout.addStretch(1)

        # The original Tactical Assistant deliberately used a scrollable detail
        # pane.  Removing it forced Qt to shrink the Disposition and Critical
        # Results forms below their layout minimums, which made their controls
        # overlap on a real Windows display.  Preserve the compact tabs and
        # side-by-side combat groups, but let the page grow to its natural
        # height and scroll whenever the available viewport is shorter.
        self.detail_scroll = QScrollArea()
        self.detail_scroll.setWidgetResizable(True)
        self.detail_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.detail_scroll.setWidget(self.unit_detail_widget)
        self.detail_scroll.viewport().installEventFilter(self)
        return self.detail_scroll

    def _set_detail_mode(
        self,
        fighter: bool,
        craft_units: tuple[TacticalUnitState, ...] = (),
    ) -> None:
        """Switch between the full ship workspace and a fighter reference."""

        is_fighter = bool(fighter)
        self._fighter_detail_mode = is_fighter
        self._active_craft_unit_ids = tuple(unit.unit_id for unit in craft_units)
        self.fighter_overview_group.setVisible(is_fighter)
        self.tracks_widget.setVisible(not is_fighter)
        self.status_and_critical_widget.setVisible(not is_fighter)
        self.weapon_actions_widget.setVisible(not is_fighter)
        self.trait_actions_widget.setVisible(not is_fighter)
        self.detail_tabs.setTabVisible(1, not is_fighter)
        self._set_fighter_profile_columns(is_fighter)
        if is_fighter:
            self.detail_tabs.setCurrentIndex(0)
            ready = sum(unit.effective_craft_status == "ready" for unit in craft_units)
            launched = sum(unit.effective_craft_status == "launched" for unit in craft_units)
            lost = sum(unit.effective_craft_status == "lost" for unit in craft_units)
            total = len(craft_units)
            noun = "flight" if total == 1 else "flights"
            self.fighter_overview_label.setText(
                f"{total} {noun}  |  Ready {ready}  |  Launched {launched}  |  Lost {lost}"
            )
        else:
            self.fighter_overview_label.clear()

    def _set_fighter_profile_columns(self, fighter: bool) -> None:
        """Hide ship-only operational status columns in fighter references."""

        if hasattr(self, "weapon_tree"):
            self.weapon_tree.setColumnHidden(5, bool(fighter))
        if hasattr(self, "trait_tree") and self.trait_tree.columnCount() >= 2:
            self.trait_tree.setColumnHidden(1, bool(fighter))
        if hasattr(self, "trait_tree") and self.trait_tree.columnCount() >= 5:
            self.trait_tree.setColumnHidden(4, bool(fighter))

    def eventFilter(self, watched: QObject, event) -> bool:  # type: ignore[override]
        if (
            hasattr(self, "detail_scroll")
            and watched is self.detail_scroll.viewport()
            and event.type() == QEvent.Type.Resize
        ):
            narrow = event.size().width() < 760
            self._set_detail_groups_stacked(narrow)
            self._set_traits_two_column(not narrow)
        elif (
            hasattr(self, "unit_tree")
            and watched is self.unit_tree.viewport()
            and event.type() == QEvent.Type.Resize
        ):
            self._set_roster_columns_compact(event.size().width() < 600)
        return super().eventFilter(watched, event)

    def _set_roster_columns_compact(self, compact: bool) -> None:
        self.unit_tree.setColumnHidden(1, bool(compact))

    def _set_detail_groups_stacked(self, stacked: bool) -> None:
        resolved = bool(stacked)
        if resolved == self._detail_groups_stacked:
            return
        self._detail_groups_stacked = resolved
        direction = (
            QBoxLayout.Direction.TopToBottom
            if resolved
            else QBoxLayout.Direction.LeftToRight
        )
        self.status_and_critical_layout.setDirection(direction)
        self.status_and_critical_layout.invalidate()
        self.status_and_critical_widget.updateGeometry()
        self.unit_detail_widget.updateGeometry()

    def _set_traits_two_column(self, enabled: bool) -> None:
        resolved = bool(enabled)
        if resolved == self._traits_two_column:
            return
        selected_key = self._selected_trait_key()
        self._traits_two_column = resolved
        self.trait_tree.clear()
        self._configure_trait_columns()
        unit = self._selected_unit()
        if unit is not None:
            self._refresh_traits(unit, selected_key=selected_key)
        else:
            self._resize_trait_tree()

    def _build_status_group(self) -> QGroupBox:
        self.destroyed_checkbox = QCheckBox("Destroyed / Lost")
        self.destroyed_checkbox.setVisible(False)
        self.disposition_combo = QComboBox()
        for label, value in (
            ("Operational", UnitDisposition.OPERATIONAL.value),
            ("Running Adrift", UnitDisposition.ADRIFT.value),
            ("Destroyed", UnitDisposition.DESTROYED.value),
            ("Surrendered", UnitDisposition.SURRENDERED.value),
            ("Tactical Withdrawal", UnitDisposition.WITHDRAWN.value),
        ):
            self.disposition_combo.addItem(label, value)
            self.disposition_combo.setItemData(
                self.disposition_combo.count() - 1,
                DISPOSITION_DESCRIPTIONS[value],
                Qt.ItemDataRole.ToolTipRole,
            )
        self.disposition_description_label = QLabel(
            DISPOSITION_DESCRIPTIONS[UnitDisposition.OPERATIONAL.value]
        )
        self.disposition_description_label.setWordWrap(True)
        self.disposition_description_label.setObjectName("pageSubtitle")
        self.crew_quality_edit = QLineEdit()
        self.special_action_combo = QComboBox()
        self.special_action_combo.setMaxVisibleItems(24)
        self.special_action_rules_label = QLabel("")
        self.special_action_rules_label.setWordWrap(True)
        self.special_action_rules_label.setTextFormat(Qt.TextFormat.RichText)
        self.special_action_rules_label.setObjectName("pageSubtitle")
        self.threshold_status_label = QLabel("Operational")
        self.threshold_status_label.setWordWrap(True)
        self.damage_control_label = QLabel("")
        self.damage_control_label.setWordWrap(True)
        self.damage_control_label.setToolTip(DAMAGE_CONTROL_HELP)
        self.correct_crippled_button = QPushButton("Correct Crippled")
        self.correct_skeleton_button = QPushButton("Correct Skeleton")
        self.correct_crippled_button.setToolTip("Remove a mistakenly applied Crippled status. This is a correction, not a repair.")
        self.correct_skeleton_button.setToolTip("Remove a mistakenly applied Skeleton Crew status. This is a correction, not a repair.")
        correction_row = QHBoxLayout()
        correction_row.addWidget(self.correct_crippled_button)
        correction_row.addWidget(self.correct_skeleton_button)

        form = QFormLayout()
        form.addRow("Disposition", self.disposition_combo)
        form.addRow("", self.disposition_description_label)
        form.addRow("Crew Quality", self.crew_quality_edit)
        form.addRow("Special Action", self.special_action_combo)
        form.addRow("", self.special_action_rules_label)
        form.addRow("Thresholds", self.threshold_status_label)
        form.addRow("Correct Entry", correction_row)
        form.addRow("Damage Control", self.damage_control_label)
        group = _HelpGroupBox(
            "Disposition",
            "Stricken Ship Damage Table",
            DISPOSITION_DAMAGE_TABLE_HELP,
        )
        group.setLayout(form)
        self.status_group = group
        self.disposition_group = group
        return group

    def _build_critical_group(self) -> QGroupBox:
        self.critical_rule_combo = QComboBox()
        for rule in CRITICAL_RULES:
            self.critical_rule_combo.addItem(rule.display_label, rule.key)
            self.critical_rule_combo.setItemData(
                self.critical_rule_combo.count() - 1,
                f"Damage {rule.damage}; Crew {rule.crew}. {rule.effect}",
                Qt.ItemDataRole.ToolTipRole,
            )
        self.critical_damage_edit = QLineEdit()
        self.critical_damage_edit.setMaximumWidth(70)
        self.critical_damage_roll_button = QPushButton("Roll")
        self.critical_damage_roll_button.setMaximumWidth(58)
        self.critical_crew_edit = QLineEdit()
        self.critical_crew_edit.setMaximumWidth(70)
        self.critical_crew_roll_button = QPushButton("Roll")
        self.critical_crew_roll_button.setMaximumWidth(58)
        self.critical_target_combo = QComboBox()
        self.critical_target_combo_2 = QComboBox()
        self.critical_target_combo_2.setVisible(False)
        self.critical_multiplier_combo = QComboBox()
        for multiplier in range(1, 5):
            self.critical_multiplier_combo.addItem(f"x{multiplier}", multiplier)
        self.critical_multiplier_combo.setMaximumWidth(70)
        self.critical_multiplier_combo.setToolTip(
            "Multiply only the critical table's extra Damage and Crew. "
            "Record the attack's normal hit before applying this result."
        )
        self.critical_preview_label = QLabel("")
        self.critical_preview_label.setWordWrap(True)
        self.critical_preview_label.setObjectName("pageSubtitle")
        self.apply_critical_button = QPushButton("Apply Critical")
        self.undo_critical_button = QPushButton("Undo")
        self.undo_critical_button.setMaximumWidth(72)
        self.undo_critical_button.setToolTip("Undo the most recently applied critical result.")

        loss_row = QHBoxLayout()
        loss_row.addWidget(QLabel("Damage"))
        loss_row.addWidget(self.critical_damage_edit)
        loss_row.addWidget(self.critical_damage_roll_button)
        loss_row.addWidget(QLabel("Crew"))
        loss_row.addWidget(self.critical_crew_edit)
        loss_row.addWidget(self.critical_crew_roll_button)
        loss_row.addStretch(1)

        apply_row = QHBoxLayout()
        apply_row.addWidget(QLabel("Critical Multiplier"))
        apply_row.addWidget(self.critical_multiplier_combo)
        apply_row.addWidget(self.apply_critical_button, 1)
        apply_row.addWidget(self.undo_critical_button)

        self.critical_tree = QTreeWidget()
        self.critical_tree.setColumnCount(3)
        self.critical_tree.setHeaderLabels(("Critical", "Effect", "Status"))
        self.critical_tree.setRootIsDecorated(False)
        self.critical_tree.setAlternatingRowColors(True)
        self.critical_tree.setMinimumHeight(130)
        self.critical_tree.setMaximumHeight(160)
        crit_header = self.critical_tree.header()
        crit_header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        crit_header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        crit_header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.repair_critical_button = QPushButton("Mark Selected Repaired")

        layout = QVBoxLayout()
        layout.addWidget(self.critical_rule_combo)
        layout.addLayout(loss_row)
        layout.addWidget(self.critical_target_combo)
        layout.addWidget(self.critical_target_combo_2)
        layout.addWidget(self.critical_preview_label)
        layout.addLayout(apply_row)
        layout.addWidget(self.critical_tree)
        layout.addWidget(self.repair_critical_button)
        group = _HelpGroupBox(
            "Critical Results",
            "Critical Hit Tables",
            CRITICAL_TABLES_HELP,
        )
        group.setLayout(layout)
        self.critical_group = group
        return group

    def _build_weapons_group(self) -> QGroupBox:
        self.weapon_tree = QTreeWidget()
        self.weapon_tree.setColumnCount(6)
        self.weapon_tree.setHeaderLabels(("Arc", "Weapon", "Range", "AD", "Traits", "Status"))
        self.weapon_tree.setRootIsDecorated(False)
        self.weapon_tree.setAlternatingRowColors(True)
        self.weapon_tree.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        weapon_header = self.weapon_tree.header()
        weapon_header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        weapon_header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        weapon_header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        weapon_header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        weapon_header.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        weapon_header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        self.weapon_disable_button = QPushButton("Disable / Enable")
        self.weapon_destroy_button = QPushButton("Destroy / Restore")
        self.weapon_actions_widget = QWidget()
        button_row = QHBoxLayout(self.weapon_actions_widget)
        button_row.setContentsMargins(0, 0, 0, 0)
        button_row.addWidget(self.weapon_disable_button)
        button_row.addWidget(self.weapon_destroy_button)
        button_row.addStretch(1)
        layout = QVBoxLayout()
        layout.addWidget(self.weapon_tree)
        layout.addWidget(self.weapon_actions_widget)
        group = _HelpGroupBox("Weapons", "Attack Table", ATTACK_TABLE_HELP)
        group.setLayout(layout)
        self.weapons_group = group
        return group

    def _build_traits_group(self) -> QGroupBox:
        self.trait_tree = QTreeWidget()
        self.trait_tree.setRootIsDecorated(False)
        self.trait_tree.setAlternatingRowColors(True)
        self.trait_tree.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectItems)
        self.trait_tree.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._configure_trait_columns()
        self.trait_disable_button = QPushButton("Disable / Enable")
        self.trait_destroy_button = QPushButton("Destroy / Restore")
        self.trait_actions_widget = QWidget()
        button_row = QHBoxLayout(self.trait_actions_widget)
        button_row.setContentsMargins(0, 0, 0, 0)
        button_row.addWidget(self.trait_disable_button)
        button_row.addWidget(self.trait_destroy_button)
        button_row.addStretch(1)
        layout = QVBoxLayout()
        layout.addWidget(self.trait_tree)
        layout.addWidget(self.trait_actions_widget)
        group = QGroupBox("Traits - hover for rules")
        group.setLayout(layout)
        self.traits_group = group
        return group

    def _configure_trait_columns(self) -> None:
        if self._traits_two_column:
            self.trait_tree.setColumnCount(5)
            self.trait_tree.setHeaderLabels(("Trait", "Status", "", "Trait", "Status"))
            name_columns = {0, 3}
            divider_column = 2
        else:
            self.trait_tree.setColumnCount(2)
            self.trait_tree.setHeaderLabels(("Trait", "Status"))
            name_columns = {0}
            divider_column = None
        header = self.trait_tree.header()
        header.setMinimumSectionSize(4)
        for column in range(self.trait_tree.columnCount()):
            if column == divider_column:
                mode = QHeaderView.ResizeMode.Fixed
            elif column in name_columns:
                mode = QHeaderView.ResizeMode.Stretch
            else:
                mode = QHeaderView.ResizeMode.ResizeToContents
            header.setSectionResizeMode(column, mode)
        if divider_column is not None:
            header.resizeSection(divider_column, 6)
            self.trait_tree.headerItem().setBackground(
                divider_column,
                QBrush(_TRAIT_DIVIDER),
            )
        self._set_fighter_profile_columns(self._fighter_detail_mode)

    def _resize_weapon_tree(self) -> None:
        rows = self.weapon_tree.topLevelItemCount()
        row_height = self.weapon_tree.sizeHintForRow(0) if rows else -1
        if row_height <= 0:
            row_height = self.weapon_tree.fontMetrics().height() + 12
        header_height = max(28, self.weapon_tree.header().sizeHint().height())
        frame = self.weapon_tree.frameWidth() * 2
        height = header_height + max(1, rows) * row_height + frame + 4
        self.weapon_tree.setFixedHeight(height)
        self.weapons_group.updateGeometry()
        if hasattr(self, "unit_detail_widget"):
            self.unit_detail_widget.updateGeometry()

    def _resize_trait_tree(self) -> None:
        rows = self.trait_tree.topLevelItemCount()
        row_height = self.trait_tree.sizeHintForRow(0) if rows else -1
        if row_height <= 0:
            row_height = self.trait_tree.fontMetrics().height() + 12
        header_height = max(28, self.trait_tree.header().sizeHint().height())
        frame = self.trait_tree.frameWidth() * 2
        height = header_height + max(1, rows) * row_height + frame + 4
        self.trait_tree.setFixedHeight(height)
        self.traits_group.updateGeometry()
        if hasattr(self, "unit_detail_widget"):
            self.unit_detail_widget.updateGeometry()

    def _build_source_notes_group(self) -> QGroupBox:
        self.source_notes_box = QTextEdit()
        self.source_notes_box.setReadOnly(True)
        self.source_notes_box.setMinimumHeight(70)
        layout = QVBoxLayout()
        layout.addWidget(self.source_notes_box)
        group = QGroupBox("Source Notes")
        group.setLayout(layout)
        return group

    def _build_unit_notes_group(self) -> QGroupBox:
        self.unit_notes_edit = QTextEdit()
        self.unit_notes_edit.setPlaceholderText("Game-only notes for this unit...")
        self.unit_notes_edit.setMinimumHeight(90)
        layout = QVBoxLayout()
        layout.addWidget(self.unit_notes_edit)
        group = QGroupBox("Unit Notes")
        group.setLayout(layout)
        return group

    def _connect_signals(self) -> None:
        self.game_name_edit.editingFinished.connect(self._game_name_changed)
        self.turn_spin.valueChanged.connect(self._turn_changed)
        self.phase_combo.currentIndexChanged.connect(self._phase_changed)
        self.scenario_combo.currentIndexChanged.connect(self._scenario_changed)
        self.scenario_map_button.clicked.connect(self._show_scenario_map)
        self.scenario_priority_combo.currentIndexChanged.connect(self._scenario_priority_changed)
        self.random_priority_button.clicked.connect(self._randomize_scenario_priority)
        self.player_role_combo.currentIndexChanged.connect(self._player_role_changed)
        self.random_role_button.clicked.connect(self._randomize_player_role)
        self.turn_order_button.clicked.connect(self._show_turn_order)
        self.advance_turn_button.clicked.connect(self._advance_turn)
        self.end_game_button.clicked.connect(self._show_end_game_report)
        self.unit_tree.currentItemChanged.connect(self._unit_selection_changed)
        self.unit_tree.customContextMenuRequested.connect(self._show_unit_context_menu)
        self.damage_editor.current_changed.connect(self._damage_changed)
        self.crew_editor.current_changed.connect(self._crew_changed)
        self.shields_editor.current_changed.connect(self._shields_changed)
        self.destroyed_checkbox.toggled.connect(self._destroyed_changed)
        self.disposition_combo.currentIndexChanged.connect(self._disposition_changed)
        self.disposition_combo.currentIndexChanged.connect(self._update_disposition_description)
        self.correct_crippled_button.clicked.connect(self._correct_crippled_status)
        self.correct_skeleton_button.clicked.connect(self._correct_skeleton_status)
        self.crew_quality_edit.textChanged.connect(self._crew_quality_preview_changed)
        self.crew_quality_edit.editingFinished.connect(self._crew_quality_changed)
        self.special_action_combo.currentIndexChanged.connect(self._special_action_changed)
        self.special_action_combo.currentIndexChanged.connect(self._update_special_action_rules)
        self.unit_notes_edit.textChanged.connect(self._unit_notes_changed)
        self.weapon_disable_button.clicked.connect(self._toggle_weapon_disabled)
        self.weapon_destroy_button.clicked.connect(self._toggle_weapon_destroyed)
        self.trait_disable_button.clicked.connect(self._toggle_trait_disabled)
        self.trait_destroy_button.clicked.connect(self._toggle_trait_destroyed)
        self.critical_rule_combo.currentIndexChanged.connect(self._critical_rule_changed)
        self.critical_multiplier_combo.currentIndexChanged.connect(self._update_critical_preview)
        self.critical_damage_edit.textChanged.connect(self._update_critical_preview)
        self.critical_crew_edit.textChanged.connect(self._update_critical_preview)
        self.apply_critical_button.clicked.connect(self._apply_critical)
        self.undo_critical_button.clicked.connect(self._undo_last_critical)
        self.critical_damage_roll_button.clicked.connect(self._roll_critical_damage)
        self.critical_crew_roll_button.clicked.connect(self._roll_critical_crew)
        self.repair_critical_button.clicked.connect(self._repair_selected_critical)
        self.critical_tree.currentItemChanged.connect(lambda *_: self._update_repair_button())

    def _install_persistent_tooltips(self) -> None:
        for combo in (
            self.scenario_combo,
            self.disposition_combo,
            self.special_action_combo,
            self.critical_rule_combo,
        ):
            self._tooltip_filter.install_combo(combo)
        for tree in (self.unit_tree, self.weapon_tree, self.trait_tree, self.critical_tree):
            self._tooltip_filter.install_tree(tree)
        for widget in (
            self.scenario_group,
            self.disposition_group,
            self.critical_group,
            self.weapons_group,
            self.turn_order_button,
            self.unit_reference_label,
            self.damage_control_label,
        ):
            self._tooltip_filter.install_widget(widget)

    def _show_turn_order(self) -> None:
        _RulesDialog("Turn Order", TURN_SEQUENCE_HELP, self).exec()

    def _show_quick_reference(self) -> None:
        if self._quick_reference_dialog is None:
            self._quick_reference_dialog = _QuickReferenceDialog(
                getattr(self._context, "codex", None),
                self,
            )
        self._quick_reference_dialog.show()
        self._quick_reference_dialog.raise_()
        self._quick_reference_dialog.activateWindow()

    def _show_unit_context_menu(self, position) -> None:
        item = self.unit_tree.itemAt(position)
        if self._game is None or item is None:
            return
        unit_id = str(item.data(0, Qt.ItemDataRole.UserRole) or "")
        if not unit_id:
            return
        try:
            unit = self._game.get_unit(unit_id)
        except KeyError:
            return
        if unit.kind is not UnitKind.PLATFORM:
            return
        menu = QMenu(self.unit_tree)
        rename_action = menu.addAction("Rename Ship...")
        clear_action = menu.addAction("Clear Custom Name")
        clear_action.setEnabled(bool(unit.vessel_name))
        selected = menu.exec(self.unit_tree.viewport().mapToGlobal(position))
        if selected is rename_action:
            self._prompt_for_ship_name(unit)
        elif selected is clear_action:
            self._set_unit_vessel_name(unit.unit_id, "")

    def _prompt_for_ship_name(self, unit: TacticalUnitState) -> None:
        name, accepted = QInputDialog.getText(
            self,
            "Rename Ship",
            f"Ship name for {unit.platform_name}:",
            QLineEdit.EchoMode.Normal,
            unit.vessel_name,
        )
        if accepted:
            self._set_unit_vessel_name(unit.unit_id, name)

    def _set_unit_vessel_name(self, unit_id: str, name: str) -> None:
        if self._game is None:
            return
        unit = self._game.get_unit(unit_id)
        updated = unit.set_vessel_name(name)
        if updated.vessel_name == unit.vessel_name:
            return
        self._game = self._game.replace_unit(updated)
        self._set_dirty(True)
        self._populate_unit_tree(selected_unit_id=unit_id)

    def _update_disposition_description(self, index: int) -> None:
        value = str(self.disposition_combo.itemData(index) or "") if index >= 0 else ""
        self.disposition_description_label.setText(DISPOSITION_DESCRIPTIONS.get(value, ""))

    def _show_empty_state(self) -> None:
        self._game = None
        self._current_path = None
        self._set_detail_mode(False)
        self._unit_items.clear()
        self._craft_group_items.clear()
        self.unit_tree.clear()
        self._loading_controls = True
        try:
            self.game_name_edit.clear()
            self.source_fleet_label.setText("No fleet loaded")
            self.turn_spin.setValue(1)
            self.phase_combo.setCurrentIndex(0)
            self.scenario_combo.setCurrentIndex(0)
            self.scenario_priority_combo.setCurrentIndex(0)
            self.player_role_combo.setCurrentIndex(0)
            self.scenario_rules_label.setText("No scenario selected")
            self.unit_title.setText("Select New from Fleet or Open Game")
            self.unit_subtitle.setText("Fleet Builder files create independent per-unit battle state.")
            self.unit_reference_label.clear()
            self.unit_effects_label.clear()
            self.unit_effects_label.hide()
            self.damage_editor.set_track(TrackState())
            self.crew_editor.set_track(TrackState())
            self.shields_editor.set_track(TrackState())
            self.destroyed_checkbox.setChecked(False)
            self.disposition_combo.setCurrentIndex(0)
            self.disposition_description_label.setText(
                DISPOSITION_DESCRIPTIONS[UnitDisposition.OPERATIONAL.value]
            )
            self.correct_crippled_button.setEnabled(False)
            self.correct_skeleton_button.setEnabled(False)
            self.crew_quality_edit.clear()
            self.special_action_combo.clear()
            self.special_action_rules_label.clear()
            self.threshold_status_label.setText("Operational")
            self.damage_control_label.clear()
            self.weapon_tree.clear()
            self._resize_weapon_tree()
            self.trait_tree.clear()
            self._resize_trait_tree()
            self.critical_tree.clear()
            self.critical_damage_edit.clear()
            self.critical_crew_edit.clear()
            self.critical_multiplier_combo.setCurrentIndex(0)
            self.critical_preview_label.clear()
            self.undo_critical_button.setEnabled(False)
            self.source_notes_box.clear()
            self.unit_notes_edit.clear()
        finally:
            self._loading_controls = False
        self.unit_summary_label.setText("No game loaded")
        self.game_name_edit.setEnabled(False)
        self.turn_spin.setEnabled(False)
        self.phase_combo.setEnabled(False)
        self.scenario_combo.setEnabled(False)
        self.scenario_map_button.setEnabled(False)
        self.scenario_priority_combo.setEnabled(False)
        self.random_priority_button.setEnabled(False)
        self.player_role_combo.setEnabled(False)
        self.random_role_button.setEnabled(False)
        self.advance_turn_button.setEnabled(False)
        self.end_game_button.setEnabled(False)
        self.unit_detail_widget.setEnabled(False)
        self._set_dirty(False)
        self._update_file_buttons()

    def load_game_state(self, game: TacticalGameState, path: str | Path | None = None) -> None:
        self._game = game
        self._current_path = Path(path).resolve() if path is not None else None
        self.game_name_edit.setEnabled(True)
        self.turn_spin.setEnabled(True)
        self.phase_combo.setEnabled(True)
        self.scenario_combo.setEnabled(True)
        self.scenario_priority_combo.setEnabled(True)
        self.random_priority_button.setEnabled(True)
        self.player_role_combo.setEnabled(True)
        self.random_role_button.setEnabled(True)
        self.advance_turn_button.setEnabled(True)
        self.end_game_button.setEnabled(True)
        self.unit_detail_widget.setEnabled(True)

        self._loading_controls = True
        try:
            self.game_name_edit.setText(game.name)
            self.source_fleet_label.setText(game.source_fleet_name or game.source_fleet_id)
            self.turn_spin.setValue(game.turn_number)
            phase_index = self.phase_combo.findData(game.phase.value)
            self.phase_combo.setCurrentIndex(max(0, phase_index))
            scenario_index = self.scenario_combo.findData(game.scenario_key)
            self.scenario_combo.setCurrentIndex(max(0, scenario_index))
            priority_index = self.scenario_priority_combo.findData(game.scenario_priority)
            self.scenario_priority_combo.setCurrentIndex(max(0, priority_index))
            role_index = self.player_role_combo.findData(game.player_role)
            self.player_role_combo.setCurrentIndex(max(0, role_index))
            self._refresh_scenario_summary()
        finally:
            self._loading_controls = False

        self._populate_unit_tree()
        self._set_dirty(False)
        self._update_file_buttons()
        source = self._current_path.name if self._current_path else game.source_fleet_name
        self._context.status.set(f"Tactical game loaded: {source}")

    def create_game_from_fleet_path(self, path: str | Path) -> TacticalGameState:
        game = self._service.create_from_fleet_file(path)
        self.load_game_state(game)
        self._remember_fleet_folder(Path(path))
        self._set_dirty(True)
        return game

    def load_game_from_path(self, path: str | Path) -> TacticalGameState:
        game = self._service.load(path)
        self.load_game_state(game, path)
        self._remember_game_folder(Path(path))
        return game

    def save_game_to_path(self, path: str | Path) -> Path:
        if self._game is None:
            raise ValueError("No tactical game is loaded.")
        target = self._ensure_game_extension(Path(path))
        saved = self._service.save(self._game, target)
        self._current_path = Path(saved).resolve()
        self._remember_game_folder(self._current_path)
        self._set_dirty(False)
        self._context.status.set(f"Tactical game saved: {self._current_path.name}")
        self._context.notifications.info("Tactical Game Saved", str(self._current_path))
        return self._current_path

    def new_from_fleet(self) -> None:
        if not self.maybe_save():
            return
        selected, _ = QFileDialog.getOpenFileName(
            self,
            "Create Tactical Game from DFS Fleet",
            str(self._default_fleet_folder()),
            "DFS Fleet (*.dfs-fleet.json);;JSON Files (*.json)",
        )
        if not selected:
            return
        try:
            self.create_game_from_fleet_path(selected)
        except Exception as exc:
            QMessageBox.critical(self, "New Tactical Game", str(exc))

    def open_game(self) -> None:
        if not self.maybe_save():
            return
        selected, _ = QFileDialog.getOpenFileName(
            self,
            "Open DFS Tactical Game",
            str(self._default_game_folder()),
            "DFS Tactical Game (*.dfs-game.json);;JSON Files (*.json)",
        )
        if not selected:
            return
        try:
            self.load_game_from_path(selected)
        except Exception as exc:
            QMessageBox.critical(self, "Open Tactical Game", str(exc))

    def save_game(self, save_as: bool = False) -> bool:
        if self._game is None:
            return False
        target = self._current_path
        if save_as or target is None:
            suggested = self._default_game_folder() / self._suggested_game_filename()
            selected, _ = QFileDialog.getSaveFileName(
                self,
                "Save DFS Tactical Game",
                str(suggested),
                "DFS Tactical Game (*.dfs-game.json);;JSON Files (*.json)",
            )
            if not selected:
                return False
            target = Path(selected)
        try:
            self.save_game_to_path(target)
        except Exception as exc:
            QMessageBox.critical(self, "Save Tactical Game", str(exc))
            return False
        return True

    def maybe_save(self) -> bool:
        if self._game is None or not self._dirty:
            return True
        answer = QMessageBox.question(
            self,
            "Unsaved Tactical Game",
            "Save changes to the current tactical game?",
            QMessageBox.StandardButton.Save
            | QMessageBox.StandardButton.Discard
            | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Save,
        )
        if answer == QMessageBox.StandardButton.Cancel:
            return False
        if answer == QMessageBox.StandardButton.Save:
            return self.save_game()
        return True

    def confirm_close(self) -> bool:
        return self.maybe_save()

    def _populate_unit_tree(self, selected_unit_id: str | None = None) -> None:
        self.unit_tree.blockSignals(True)
        try:
            for editor in self._craft_group_editors:
                editor.deleteLater()
            self._craft_group_editors.clear()
            self.unit_tree.clear()
            self._unit_items.clear()
            self._craft_group_items.clear()
            if self._game is None:
                return

            purchased_craft_groups: dict[tuple[str, str], QTreeWidgetItem] = {}
            deferred: list[TacticalUnitState] = []
            for unit in self._game.units:
                if unit.parent_unit_id:
                    deferred.append(unit)
                    continue
                if unit.kind is UnitKind.CRAFT:
                    key = (unit.source_entry_id, unit.platform_name)
                    group = purchased_craft_groups.get(key)
                    if group is None:
                        siblings = [
                            item
                            for item in self._game.units
                            if item.parent_unit_id is None
                            and item.kind is UnitKind.CRAFT
                            and item.source_entry_id == unit.source_entry_id
                            and item.platform_name == unit.platform_name
                        ]
                        group = QTreeWidgetItem(self.unit_tree)
                        self._configure_craft_group_item(
                            group,
                            siblings,
                            "Purchased Craft",
                        )
                        self._install_craft_group_editor(group, siblings)
                        purchased_craft_groups[key] = group
                        self._craft_group_items[("", unit.platform_name)] = group
                        for sibling in siblings:
                            self._unit_items[sibling.unit_id] = group
                    continue

                item = QTreeWidgetItem(self.unit_tree)
                self._configure_unit_item(item, unit)
                self._unit_items[unit.unit_id] = item

            # Add carried platforms first so any craft assigned to an embarked
            # platform can still find its immediate parent.
            remaining_platforms = [unit for unit in deferred if unit.kind is UnitKind.PLATFORM]
            while remaining_platforms:
                pending: list[TacticalUnitState] = []
                progressed = False
                for unit in remaining_platforms:
                    parent = self._unit_items.get(unit.parent_unit_id or "")
                    if parent is None:
                        pending.append(unit)
                        continue
                    item = QTreeWidgetItem(parent)
                    self._configure_unit_item(item, unit)
                    self._unit_items[unit.unit_id] = item
                    progressed = True
                if progressed:
                    remaining_platforms = pending
                    continue
                for unit in pending:
                    item = QTreeWidgetItem(self.unit_tree)
                    self._configure_unit_item(item, unit)
                    self._unit_items[unit.unit_id] = item
                break

            carried_groups: dict[tuple[str, str], list[TacticalUnitState]] = {}
            for unit in deferred:
                if unit.kind is UnitKind.CRAFT:
                    carried_groups.setdefault(
                        (unit.parent_unit_id or "", unit.platform_name),
                        [],
                    ).append(unit)

            for key, siblings in carried_groups.items():
                parent_id, platform_name = key
                parent = self._unit_items.get(parent_id)
                group = QTreeWidgetItem(parent if parent is not None else self.unit_tree)
                self._configure_craft_group_item(group, siblings, "Carried Craft")
                self._craft_group_items[key] = group
                self._install_craft_group_editor(group, siblings)
                for unit in siblings:
                    self._unit_items[unit.unit_id] = group

            # Keep carriers open so their one-line fighter groups are visible.
            for index in range(self.unit_tree.topLevelItemCount()):
                top = self.unit_tree.topLevelItem(index)
                top.setExpanded(bool(top.data(0, Qt.ItemDataRole.UserRole)))

            target = self._unit_items.get(selected_unit_id or "")
            if target is None and self._game.units:
                target = self._unit_items.get(self._game.units[0].unit_id)
            if target is not None:
                ancestor = target.parent()
                while ancestor is not None:
                    ancestor.setExpanded(True)
                    ancestor = ancestor.parent()
                self.unit_tree.setCurrentItem(target)
        finally:
            self.unit_tree.blockSignals(False)
        self._update_summary()
        self._unit_selection_changed(self.unit_tree.currentItem(), None)

    @staticmethod
    def _craft_group_status(units: list[TacticalUnitState]) -> str:
        ready = sum(unit.effective_craft_status == "ready" for unit in units)
        launched = sum(unit.effective_craft_status == "launched" for unit in units)
        lost = sum(unit.effective_craft_status == "lost" for unit in units)
        return f"{ready} ready / {launched} launched / {lost} lost"

    def _configure_craft_group_item(
        self,
        item: QTreeWidgetItem,
        units: list[TacticalUnitState],
        type_label: str,
    ) -> None:
        """Make one selectable roster row represent every same-type flight."""

        if not units:
            return
        representative = units[0]
        unit_ids = tuple(unit.unit_id for unit in units)
        item.setData(0, Qt.ItemDataRole.UserRole, representative.unit_id)
        item.setData(0, _CRAFT_GROUP_IDS_ROLE, unit_ids)
        item.setText(0, f"{representative.platform_name} x{len(units)}")
        item.setText(1, type_label)
        item.setText(2, "")
        item.setToolTip(
            0,
            f"{representative.platform_name}\n"
            "Select this row to open the fighter reference. Use the Ready, "
            "Launched, and Lost controls to track individual flights.",
        )
        all_lost = all(unit.effective_craft_status == "lost" for unit in units)
        font = item.font(0)
        font.setStrikeOut(all_lost)
        for column in range(self.unit_tree.columnCount()):
            item.setFont(column, font)
            if all_lost:
                item.setForeground(column, _MUTED)

    def _install_craft_group_editor(
        self,
        item: QTreeWidgetItem,
        units: list[TacticalUnitState],
    ) -> None:
        editor = _CraftGroupEditor(self.unit_tree)
        ready = sum(unit.effective_craft_status == "ready" for unit in units)
        launched = sum(unit.effective_craft_status == "launched" for unit in units)
        lost = sum(unit.effective_craft_status == "lost" for unit in units)
        editor.set_counts(ready, launched, lost)
        unit_ids = tuple(unit.unit_id for unit in units)
        editor.counts_changed.connect(
            lambda ready_count, launched_count, lost_count, ids=unit_ids: self._set_craft_group_counts(
                ids,
                ready_count,
                launched_count,
                lost_count,
            )
        )
        self._craft_group_editors.append(editor)
        for column, control in zip((3, 4, 5), editor.controls):
            self.unit_tree.setItemWidget(item, column, control)
            self._tooltip_filter.install_widget(control)
            self._tooltip_filter.install_widget(control.decrement_button)
            self._tooltip_filter.install_widget(control.value_label)
            self._tooltip_filter.install_widget(control.increment_button)

    def _set_craft_group_counts(
        self,
        unit_ids: tuple[str, ...],
        ready: int,
        launched: int,
        lost: int,
    ) -> None:
        if self._loading_controls or self._game is None:
            return
        units = [self._game.get_unit(unit_id) for unit_id in unit_ids]
        if ready + launched + lost != len(units):
            return

        existing_lost = [unit for unit in units if unit.effective_craft_status == "lost"]
        lost_order = [
            *existing_lost,
            *(unit for unit in units if unit not in existing_lost and unit.effective_craft_status == "launched"),
            *(unit for unit in units if unit not in existing_lost and unit.effective_craft_status == "ready"),
        ]
        lost_ids = {unit.unit_id for unit in lost_order[:lost]}
        survivors = [unit for unit in units if unit.unit_id not in lost_ids]
        existing_launched = [
            unit for unit in survivors if unit.effective_craft_status == "launched"
        ]
        launched_order = [
            *existing_launched,
            *(unit for unit in survivors if unit not in existing_launched),
        ]
        launched_ids = {unit.unit_id for unit in launched_order[:launched]}

        updated_game = self._game
        for unit in units:
            if unit.unit_id in lost_ids:
                updated = unit.mark_destroyed(True)
            else:
                updated = unit.mark_destroyed(False)
                updated = updated.set_craft_status(
                    "launched" if unit.unit_id in launched_ids else "ready"
                )
            updated_game = updated_game.replace_unit(updated)
        self._game = updated_game
        self._set_dirty(True)
        selected = self._selected_unit()
        selected_id = selected.unit_id if selected is not None else unit_ids[0]
        self._populate_unit_tree(selected_unit_id=selected_id)

    def _configure_unit_item(self, item: QTreeWidgetItem, unit: TacticalUnitState) -> None:
        item.setData(0, Qt.ItemDataRole.UserRole, unit.unit_id)
        item.setText(0, self._roster_display_label(unit))
        item.setText(1, self._unit_type_label(unit))
        if unit.kind is UnitKind.CRAFT:
            item.setText(2, "")
            self._install_craft_status_combo(item, unit)
        else:
            existing = self.unit_tree.itemWidget(item, 2)
            if existing is not None:
                self.unit_tree.removeItemWidget(item, 2)
                existing.deleteLater()
            item.setText(2, self._unit_status_text(unit))
        tooltip = unit.platform_name
        if unit.vessel_name:
            tooltip += f"\nShip name: {unit.vessel_name}"
        item.setToolTip(0, tooltip)
        font = item.font(0)
        font.setStrikeOut(unit.is_destroyed or unit.is_surrendered or unit.is_withdrawn)
        for column in range(self.unit_tree.columnCount()):
            item.setFont(column, font)
            if unit.is_destroyed or unit.is_surrendered or unit.is_withdrawn:
                item.setForeground(column, _MUTED)

    def _install_craft_status_combo(
        self,
        item: QTreeWidgetItem,
        unit: TacticalUnitState,
    ) -> None:
        combo = self.unit_tree.itemWidget(item, 2)
        if not isinstance(combo, QComboBox):
            combo = QComboBox(self.unit_tree)
            combo.setMinimumContentsLength(8)
            combo.currentIndexChanged.connect(
                lambda index, unit_id=unit.unit_id, widget=combo: self._craft_status_changed(
                    unit_id,
                    str(widget.itemData(index) or ""),
                )
            )
            self.unit_tree.setItemWidget(item, 2, combo)
        combo.blockSignals(True)
        try:
            combo.clear()
            if unit.is_destroyed:
                combo.addItem("Lost", "lost")
                combo.setEnabled(False)
            else:
                combo.addItem("Ready", "ready")
                combo.addItem("Launched", "launched")
                combo.setCurrentIndex(
                    max(0, combo.findData(unit.effective_craft_status))
                )
                combo.setEnabled(True)
        finally:
            combo.blockSignals(False)

    def _craft_status_changed(self, unit_id: str, status: str) -> None:
        if self._loading_controls or self._game is None or status not in {"ready", "launched"}:
            return
        try:
            unit = self._game.get_unit(unit_id)
        except KeyError:
            return
        if unit.kind is UnitKind.CRAFT and unit.effective_craft_status != status:
            self._game = self._game.replace_unit(unit.set_craft_status(status))
            self._set_dirty(True)
            self._populate_unit_tree(selected_unit_id=unit.unit_id)

    @staticmethod
    def _roster_display_label(unit: TacticalUnitState) -> str:
        platform = (
            f"{unit.platform_name} #{unit.instance_number}"
            if unit.instance_number > 1
            else unit.platform_name
        )
        return f"{unit.vessel_name} — {platform}" if unit.vessel_name else platform

    @staticmethod
    def _unit_display_label(unit: TacticalUnitState) -> str:
        return TacticalAssistantPage._roster_display_label(unit)

    @staticmethod
    def _unit_type_label(unit: TacticalUnitState) -> str:
        if unit.kind is UnitKind.CRAFT:
            return "Craft"
        if unit.parent_unit_id:
            return "Embarked"
        return "Platform"

    @staticmethod
    def _unit_status_text(unit: TacticalUnitState) -> str:
        if unit.is_destroyed:
            return "Lost" if unit.kind is UnitKind.CRAFT else "Destroyed"
        if unit.kind is UnitKind.CRAFT:
            return unit.effective_craft_status.title()
        if unit.is_surrendered:
            return "Surrendered"
        if unit.is_withdrawn:
            return "Withdrawn"
        flags = []
        if (
            unit.kind is UnitKind.PLATFORM
            and unit.damage.current is not None
            and unit.damage.current <= 0
            and unit.disposition is UnitDisposition.OPERATIONAL
        ):
            flags.append("Stricken")
        if unit.is_adrift:
            flags.append("Adrift")
        elif unit.is_crippled:
            flags.append("Crippled")
        if unit.is_skeleton_crew:
            flags.append("Skeleton")
        tracks: list[str] = []
        if unit.damage.current is not None and unit.damage.maximum is not None:
            tracks.append(f"D {unit.damage.current}/{unit.damage.maximum}")
        if unit.crew.current is not None and unit.crew.maximum is not None:
            tracks.append(f"C {unit.crew.current}/{unit.crew.maximum}")
        if unit.shields.current is not None and unit.shields.maximum is not None:
            tracks.append(f"S {unit.shields.current}/{unit.shields.maximum}")
        return "  ".join((*flags, *tracks)) or "Ready"

    def _unit_selection_changed(self, current: QTreeWidgetItem | None, _previous: QTreeWidgetItem | None) -> None:
        if self._game is None or current is None:
            return
        unit_id = current.data(0, Qt.ItemDataRole.UserRole)
        if not unit_id:
            return
        try:
            unit = self._game.get_unit(str(unit_id))
        except KeyError:
            return
        self._load_unit_controls(
            unit,
            craft_units=self._craft_units_for_item(current),
        )

    def _craft_units_for_item(
        self,
        item: QTreeWidgetItem | None,
    ) -> tuple[TacticalUnitState, ...]:
        if self._game is None or item is None:
            return ()
        raw_ids = item.data(0, _CRAFT_GROUP_IDS_ROLE)
        if not isinstance(raw_ids, (tuple, list)):
            return ()
        units: list[TacticalUnitState] = []
        for unit_id in raw_ids:
            try:
                unit = self._game.get_unit(str(unit_id))
            except KeyError:
                continue
            if unit.kind is UnitKind.CRAFT:
                units.append(unit)
        return tuple(units)

    def _load_unit_controls(
        self,
        unit: TacticalUnitState,
        *,
        craft_units: tuple[TacticalUnitState, ...] = (),
    ) -> None:
        if unit.kind is UnitKind.CRAFT and not craft_units:
            craft_units = self._craft_units_for_item(self.unit_tree.currentItem())
        if unit.kind is UnitKind.CRAFT and not craft_units:
            craft_units = (unit,)
        self._set_detail_mode(unit.kind is UnitKind.CRAFT, craft_units)
        self._loading_controls = True
        try:
            if unit.kind is UnitKind.CRAFT:
                count = len(craft_units)
                self.unit_title.setText(
                    f"{unit.platform_name} x{count}" if count > 1 else unit.platform_name
                )
                subtitle_parts = ["Fighter reference"]
            else:
                self.unit_title.setText(self._unit_display_label(unit))
                subtitle_parts = [unit.platform_name]
            if unit.faction_name:
                subtitle_parts.append(unit.faction_name)
            if unit.fleet_name:
                subtitle_parts.append(unit.fleet_name)
            self.unit_subtitle.setText("  |  ".join(dict.fromkeys(subtitle_parts)))
            self._set_reference_stats(unit)
            self._set_effect_summary(unit)

            self.damage_editor.set_track(unit.damage)
            self.crew_editor.set_track(unit.crew)
            self.shields_editor.set_track(
                unit.shields,
                operational=unit.shields_online,
                operational_note=("Offline while Crippled" if unit.shields.available and not unit.shields_online else ""),
            )
            self.destroyed_checkbox.setChecked(unit.is_destroyed)
            disposition = unit.disposition.value
            if unit.is_destroyed:
                disposition = UnitDisposition.DESTROYED.value
            elif unit.is_adrift:
                disposition = UnitDisposition.ADRIFT.value
            disposition_index = self.disposition_combo.findData(disposition)
            self.disposition_combo.setCurrentIndex(max(0, disposition_index))
            self.disposition_combo.setEnabled(True)
            for row in range(self.disposition_combo.count()):
                model_item = self.disposition_combo.model().item(row)
                if model_item is None:
                    continue
                value = str(self.disposition_combo.itemData(row) or "")
                model_item.setEnabled(
                    unit.kind is UnitKind.PLATFORM
                    or value in {
                        UnitDisposition.OPERATIONAL.value,
                        UnitDisposition.DESTROYED.value,
                    }
                )
            self.crew_quality_edit.setText(unit.crew_quality)
            self._populate_special_actions(unit)
            self._set_threshold_status(unit)
            self._refresh_weapons(unit)
            self._refresh_traits(unit)
            self._refresh_criticals(unit)
            self.source_notes_box.setPlainText("\n".join(unit.source_notes))
            self.unit_notes_edit.setPlainText(unit.notes)
        finally:
            self._loading_controls = False

    def _set_reference_stats(self, unit: TacticalUnitState) -> None:
        parts: list[str] = []
        reference_stats = [
            ("Priority", unit.priority_level, unit.priority_level),
            ("Initiative", unit.initiative, unit.initiative),
            ("Speed", unit.speed, unit.effective_speed),
            ("Turn", unit.turn, unit.effective_turn),
            ("Hull", unit.hull, unit.hull),
        ]
        reference_stats.extend(
            (label, value, value) for label, value in fighter_reference_stats(unit)
        )
        reference_stats.append(("Troops", unit.troops, unit.effective_troops))

        for label, original, effective in reference_stats:
            if not original:
                continue
            modified = label in {"Speed", "Turn", "Troops"} and effective.replace("o", "°") != original.replace("o", "°")
            display_value = effective
            if label == "Speed" and unit.is_adrift:
                display_value = (
                    f'{effective} - Running Adrift: move {unit.adrift_movement}" '
                    "straight in the End Phase"
                )
            value = escape(display_value)
            if modified:
                value = f'<span style="color:{_MODIFIED_RED}; font-weight:700">{value}</span>'
            parts.append(f"<b>{escape(label)}</b> {value}")
        self.unit_reference_label.setText("&nbsp;&nbsp;|&nbsp;&nbsp;".join(parts))
        tooltip = []
        if unit.speed_is_modified:
            tooltip.append(f"Original Speed: {unit.speed}")
        if unit.turn_is_modified:
            tooltip.append(f"Original Turn: {unit.turn}")
        if unit.troops_are_modified:
            tooltip.append(f"Original Troops: {unit.troops}")
        if unit.is_adrift:
            tooltip.append(
                f'Running Adrift compulsory movement: {unit.adrift_movement}" straight in the End Phase.'
            )
        self.unit_reference_label.setToolTip("\n".join(tooltip))

    def _set_effect_summary(self, unit: TacticalUnitState) -> None:
        effects: list[str] = []
        if unit.is_crippled:
            effects.append(
                "Crippled: half Speed, reduced Turns, one weapon per arc, Shields offline; "
                "roll 4+ for each trait and mark destroyed results below."
            )
        if unit.is_skeleton_crew:
            if unit.has_flight_computer:
                effects.append("Skeleton Crew: Flight Computer ignores most penalties; Troops and Fleet Carrier remain affected.")
            else:
                effects.append("Skeleton Crew: no Special Actions, one weapon system, -2 Damage Control.")
        if unit.is_adrift:
            effects.append(
                f'Running Adrift: current Speed {unit.effective_speed}; move '
                f'{unit.adrift_movement}" straight in the End Phase.'
            )
        effects.extend(unit.firing_restrictions)
        text = "  ".join(dict.fromkeys(effects))
        self.unit_effects_label.setText(text)
        self.unit_effects_label.setVisible(bool(text))

    def _set_threshold_status(self, unit: TacticalUnitState) -> None:
        flags = []
        if unit.is_crippled:
            flags.append("Crippled")
        if unit.is_skeleton_crew:
            flags.append("Skeleton Crew")
        if unit.is_adrift:
            flags.append("Running Adrift")
        elif (
            unit.kind is UnitKind.PLATFORM
            and unit.damage.current is not None
            and unit.damage.current <= 0
            and unit.disposition is UnitDisposition.OPERATIONAL
        ):
            flags.append("Stricken - roll Disposition")
        self.threshold_status_label.setText(", ".join(flags) or "Operational")
        self.correct_crippled_button.setEnabled(unit.kind is UnitKind.PLATFORM and unit.is_crippled)
        self.correct_skeleton_button.setEnabled(unit.kind is UnitKind.PLATFORM and unit.is_skeleton_crew)
        current_turn = self._game.turn_number if self._game is not None else 1
        self.damage_control_label.setText(unit.damage_control_equation(current_turn))

    def _populate_special_actions(self, unit: TacticalUnitState) -> None:
        self.special_action_combo.blockSignals(True)
        try:
            self.special_action_combo.clear()
            selected_index = 0
            for availability in special_action_availability(unit):
                action = availability.action
                label = action.name
                index = self.special_action_combo.count()
                self.special_action_combo.addItem(label, action.name)
                tooltip = f"Crew Quality Check: {action.check}\n{action.effect}"
                if not availability.allowed:
                    tooltip += f"\nUnavailable: {availability.reason}"
                self.special_action_combo.setItemData(index, tooltip, Qt.ItemDataRole.ToolTipRole)
                self.special_action_combo.setItemData(
                    index,
                    {
                        "check": action.check,
                        "effect": action.effect,
                        "allowed": availability.allowed,
                        "reason": availability.reason,
                    },
                    _USER_ROLE + 1,
                )
                model_item = self.special_action_combo.model().item(index)
                if model_item is not None:
                    model_item.setEnabled(availability.allowed)
                if action.name == (unit.special_action or "None / Normal Operations"):
                    selected_index = index
            self.special_action_combo.setCurrentIndex(selected_index)
        finally:
            self.special_action_combo.blockSignals(False)
        self._update_special_action_rules(self.special_action_combo.currentIndex())

    def _update_special_action_rules(self, index: int) -> None:
        if index < 0:
            self.special_action_rules_label.clear()
            return
        data = self.special_action_combo.itemData(index, _USER_ROLE + 1)
        if not isinstance(data, dict):
            self.special_action_rules_label.clear()
            return
        check = str(data.get("check", "-"))
        check_text = self._crew_quality_check_equation(
            check,
            self.crew_quality_edit.text(),
        )
        text = (
            f"<b>Crew Quality Check:</b> {escape(check_text)}<br>"
            f"{escape(str(data.get('effect', '')))}"
        )
        if not data.get("allowed", True):
            text += (
                f"<br><span style='color:{_MODIFIED_RED}'><b>Unavailable:</b> "
                f"{escape(str(data.get('reason', '')))}</span>"
            )
        self.special_action_rules_label.setText(text)

    @staticmethod
    def _crew_quality_check_equation(check: str, crew_quality: str) -> str:
        """Expand numeric CQ checks with the entered score and die target."""

        target_match = re.fullmatch(r"\s*(\d+)\+?\s*", str(check or ""))
        if target_match is None:
            return str(check or "-")
        target = int(target_match.group(1))
        cq_text = str(crew_quality or "").strip()
        equation = f"Roll 1D6 + CQ {cq_text or '?'}; {target}+ succeeds"
        cq_match = re.search(r"-?\d+", cq_text)
        if cq_match is None:
            return equation + "."
        required = target - int(cq_match.group())
        if required <= 1:
            die_note = "need 1+ on the die"
        elif required <= 6:
            die_note = f"need {required}+ on the die"
        else:
            die_note = f"need {required}+ on the die; another modifier is required"
        return f"{equation} ({die_note})."

    def _refresh_weapons(self, unit: TacticalUnitState) -> None:
        selected_key = self._selected_tree_key(self.weapon_tree)
        self.weapon_tree.clear()
        selected_item = None
        for weapon in unit.weapons:
            item = QTreeWidgetItem(self.weapon_tree)
            item.setData(0, Qt.ItemDataRole.UserRole, weapon.weapon_key)
            item.setText(0, weapon.arc)
            item.setText(1, weapon.name)
            item.setText(2, weapon.range_value)
            effective_ad = unit.effective_attack_dice(weapon)
            item.setText(3, effective_ad)
            item.setText(4, weapon.traits)
            status = unit.weapon_status(weapon.weapon_key)
            item.setText(5, status)
            inactive = unit.weapon_is_inactive(weapon.weapon_key)
            font = item.font(1)
            font.setStrikeOut(inactive)
            for column in range(6):
                item.setFont(column, font)
                if inactive:
                    item.setForeground(column, _MUTED)
            if effective_ad != weapon.attack_dice:
                item.setForeground(3, QColor(_MODIFIED_RED))
                ad_font = item.font(3)
                ad_font.setBold(True)
                item.setFont(3, ad_font)
                item.setToolTip(3, f"Original AD: {weapon.attack_dice}")
            tooltip = self._weapon_tooltip(weapon.name, weapon.traits)
            if tooltip:
                for column in range(1, 5):
                    item.setToolTip(column, tooltip)
            if selected_key == weapon.weapon_key:
                selected_item = item
        if selected_item is not None:
            self.weapon_tree.setCurrentItem(selected_item)
        self._resize_weapon_tree()
        self.weapon_disable_button.setEnabled(bool(unit.weapons))
        self.weapon_destroy_button.setEnabled(bool(unit.weapons))

    def _refresh_traits(
        self,
        unit: TacticalUnitState,
        *,
        selected_key: str | None = None,
    ) -> None:
        if selected_key is None:
            selected_key = self._selected_trait_key()
        self.trait_tree.clear()
        selected_cell: tuple[QTreeWidgetItem, int] | None = None
        column_pairs = 2 if self._traits_two_column else 1
        for index in range(0, len(unit.traits), column_pairs):
            item = QTreeWidgetItem(self.trait_tree)
            if self._traits_two_column:
                item.setBackground(2, QBrush(_TRAIT_DIVIDER))
            for pair in range(column_pairs):
                trait_index = index + pair
                if trait_index >= len(unit.traits):
                    break
                trait = unit.traits[trait_index]
                name_column = 0 if pair == 0 else 3
                status_column = name_column + 1
                for column in (name_column, status_column):
                    item.setData(column, Qt.ItemDataRole.UserRole, trait.trait_key)
                item.setText(name_column, trait.name)
                status = unit.trait_status(trait.trait_key)
                item.setText(status_column, status)
                inactive = (
                    unit.trait_is_inactive(trait.trait_key)
                    or status.startswith("Offline")
                )
                font = item.font(name_column)
                font.setStrikeOut(inactive)
                for column in (name_column, status_column):
                    item.setFont(column, font)
                    if inactive:
                        item.setForeground(column, _MUTED)
                tooltip = self._trait_tooltip(trait.name)
                if tooltip:
                    item.setToolTip(name_column, tooltip)
                    item.setToolTip(status_column, tooltip)
                if selected_key == trait.trait_key:
                    selected_cell = item, name_column
        if selected_cell is not None:
            item, column = selected_cell
            self.trait_tree.setCurrentItem(item, column)
        self._resize_trait_tree()
        self.trait_disable_button.setEnabled(bool(unit.traits))
        self.trait_destroy_button.setEnabled(bool(unit.traits))

    def _refresh_criticals(self, unit: TacticalUnitState) -> None:
        selected_id = self._selected_tree_key(self.critical_tree)
        self.critical_tree.clear()
        selected_item = None
        current_turn = self._game.turn_number if self._game is not None else 1
        for critical in unit.critical_hits:
            item = QTreeWidgetItem(self.critical_tree)
            item.setData(0, Qt.ItemDataRole.UserRole, critical.critical_id)
            prefix = f"{critical.system} {critical.roll}".strip()
            item.setText(0, f"{prefix} - {critical.label}" if prefix else critical.label)
            target = ", ".join(critical.target_labels)
            effect = critical.effect + (f" [{target}]" if target else "")
            loss_summary = f"{critical.damage_loss} Damage / {critical.crew_loss} Crew"
            if critical.damage_multiplier > 1:
                loss_summary += f" (x{critical.damage_multiplier})"
            effect = f"{effect} | {loss_summary}" if effect else loss_summary
            item.setText(1, effect)
            status = critical.repair_status(current_turn)
            item.setText(2, status)
            if critical.repaired:
                font = item.font(0)
                font.setStrikeOut(True)
                for column in range(3):
                    item.setFont(column, font)
                    item.setForeground(column, _MUTED)
            if selected_id == critical.critical_id:
                selected_item = item
        if selected_item is not None:
            self.critical_tree.setCurrentItem(selected_item)
        self._critical_rule_changed(self.critical_rule_combo.currentIndex())
        self.undo_critical_button.setEnabled(bool(unit.critical_hits))
        self._update_repair_button()

    def _trait_tooltip(self, trait_name: str) -> str:
        codex = getattr(self._context, "codex", None)
        if codex is None:
            return trait_name
        try:
            entry = codex.get(trait_name)
        except Exception:
            entry = None
        if entry is None:
            return trait_name
        source = f"\n\nSource: {entry.source}" if entry.source else ""
        return f"{entry.title}\n\n{entry.text}{source}"

    def _weapon_tooltip(self, weapon_name: str, traits: str) -> str:
        """Return every Codex rule represented by a weapon row.

        The former implementation called ``first_for_weapon`` and therefore
        stopped after the first recognized weapon trait. The complete list is
        now joined into one tooltip while retaining compatibility with older
        Codex service implementations.
        """

        codex = getattr(self._context, "codex", None)
        if codex is None:
            return ""
        entries = ()
        try:
            resolver = getattr(codex, "all_for_weapon", None)
            if callable(resolver):
                entries = tuple(resolver(weapon_name, traits))
            else:
                entry = codex.first_for_weapon(weapon_name, traits)
                entries = (entry,) if entry is not None else ()
        except Exception:
            entries = ()
        sections: list[str] = []
        for entry in entries:
            if entry is None:
                continue
            source = f"\nSource: {entry.source}" if entry.source else ""
            sections.append(f"{entry.title}\n\n{entry.text}{source}")
        return "\n\n------------------------------\n\n".join(sections)

    def _critical_rule_changed(self, _index: int) -> None:
        unit = self._selected_unit()
        key = self.critical_rule_combo.currentData()
        if unit is None or not key:
            self.apply_critical_button.setEnabled(False)
            self.critical_damage_roll_button.setEnabled(False)
            self.critical_crew_roll_button.setEnabled(False)
            self.critical_preview_label.clear()
            return
        rule = CRITICAL_RULE_BY_KEY[str(key)]
        self.critical_damage_edit.setText(str(rule.fixed_damage) if rule.fixed_damage is not None else "")
        self.critical_crew_edit.setText(str(rule.fixed_crew) if rule.fixed_crew is not None else "")
        self.critical_damage_edit.setPlaceholderText(rule.damage)
        self.critical_crew_edit.setPlaceholderText(rule.crew)
        self.critical_damage_roll_button.setEnabled("D" in rule.damage.upper())
        self.critical_crew_roll_button.setEnabled("D" in rule.crew.upper())
        self.critical_damage_roll_button.setToolTip(f"Roll {rule.damage}")
        self.critical_crew_roll_button.setToolTip(f"Roll {rule.crew}")
        targets = critical_targets(unit, rule)
        self._fill_target_combo(
            self.critical_target_combo,
            targets,
            visible=rule.target_count >= 1,
            allow_random=bool(rule.target_kind),
        )
        self._fill_target_combo(
            self.critical_target_combo_2,
            targets,
            visible=rule.target_count >= 2,
            allow_random=bool(rule.target_kind),
        )
        self.apply_critical_button.setEnabled(True)
        self._update_critical_preview()

    def _critical_multiplier(self) -> int:
        return int(self.critical_multiplier_combo.currentData() or 1)

    def _update_critical_preview(self, *_args) -> None:
        multiplier = self._critical_multiplier()
        self.apply_critical_button.setText(f"Apply Critical x{multiplier}")
        try:
            extra_damage = int(self.critical_damage_edit.text().strip())
            extra_crew = int(self.critical_crew_edit.text().strip())
        except ValueError:
            self.critical_preview_label.setText(
                "Enter or roll the critical Damage and Crew values to preview the total."
            )
            return
        total_damage = max(0, extra_damage) * multiplier
        total_crew = max(0, extra_crew) * multiplier
        self.critical_preview_label.setText(
            f"Critical applied: {total_damage} Damage and {total_crew} Crew "
            f"(critical result only, x{multiplier}; normal hit recorded separately)."
        )

    @staticmethod
    def _fill_target_combo(
        combo: QComboBox,
        targets: tuple[tuple[str, str], ...],
        *,
        visible: bool,
        allow_random: bool = False,
    ) -> None:
        combo.clear()
        combo.setVisible(visible)
        if not visible:
            return
        if not targets:
            combo.addItem("No eligible target", "")
            combo.setEnabled(False)
            return
        combo.setEnabled(True)
        if allow_random:
            combo.addItem("Random", "__random__")
        for key, label in targets:
            combo.addItem(label, key)

    def _apply_critical(self) -> None:
        unit = self._selected_unit()
        key = self.critical_rule_combo.currentData()
        if unit is None or not key or self._game is None:
            return
        rule = CRITICAL_RULE_BY_KEY[str(key)]
        try:
            damage = int(self.critical_damage_edit.text().strip())
            crew = int(self.critical_crew_edit.text().strip())
        except ValueError:
            QMessageBox.warning(
                self,
                "Apply Critical",
                f"Enter the rolled Damage and Crew totals for {rule.damage} / {rule.crew}.",
            )
            return
        try:
            target_keys, target_labels = self._resolved_critical_targets(unit, rule)
        except ValueError as exc:
            QMessageBox.warning(self, "Apply Critical", str(exc))
            return
        try:
            updated = apply_critical_rule(
                unit,
                str(key),
                damage_loss=damage,
                crew_loss=crew,
                target_keys=target_keys,
                target_labels=target_labels,
                applied_turn=self._game.turn_number,
                damage_multiplier=self._critical_multiplier(),
                include_solid_hit=False,
            )
        except ValueError as exc:
            QMessageBox.warning(self, "Apply Critical", str(exc))
            return
        self.critical_multiplier_combo.setCurrentIndex(0)
        self._replace_selected_unit(updated, reload_controls=True)
        self._sync_destroyed_checkbox(updated)

    def _resolved_critical_targets(self, unit: TacticalUnitState, rule) -> tuple[list[str], list[str]]:
        if not rule.target_count:
            return [], []
        available = list(critical_targets(unit, rule))
        if len(available) < rule.target_count:
            raise ValueError(
                f"{rule.label} requires {rule.target_count} eligible target(s), "
                f"but only {len(available)} remain."
            )

        selected: list[tuple[str, str]] = []
        for combo in (self.critical_target_combo, self.critical_target_combo_2):
            if not combo.isVisible():
                continue
            key = str(combo.currentData() or "")
            if key == "__random__":
                choices = [item for item in available if item not in selected]
                selected.append(random.SystemRandom().choice(choices))
                continue
            match = next((item for item in available if item[0] == key), None)
            if match is not None and match not in selected:
                selected.append(match)

        if len(selected) < rule.target_count:
            remaining = [item for item in available if item not in selected]
            selected.extend(random.SystemRandom().sample(remaining, rule.target_count - len(selected)))
        selected = selected[: rule.target_count]
        return [item[0] for item in selected], [item[1] for item in selected]

    def _roll_critical_damage(self) -> None:
        key = self.critical_rule_combo.currentData()
        if not key:
            return
        rule = CRITICAL_RULE_BY_KEY[str(key)]
        try:
            self.critical_damage_edit.setText(str(roll_loss_expression(rule.damage)))
        except ValueError as exc:
            QMessageBox.warning(self, "Roll Critical Damage", str(exc))

    def _roll_critical_crew(self) -> None:
        key = self.critical_rule_combo.currentData()
        if not key:
            return
        rule = CRITICAL_RULE_BY_KEY[str(key)]
        try:
            self.critical_crew_edit.setText(str(roll_loss_expression(rule.crew)))
        except ValueError as exc:
            QMessageBox.warning(self, "Roll Critical Crew", str(exc))

    def _undo_last_critical(self) -> None:
        unit = self._selected_unit()
        if unit is None or not unit.critical_hits:
            return
        updated = unit.undo_last_critical()
        self._replace_selected_unit(updated, reload_controls=True)
        self._sync_destroyed_checkbox(updated)

    def _repair_selected_critical(self) -> None:
        unit = self._selected_unit()
        item = self.critical_tree.currentItem()
        if unit is None or item is None:
            return
        critical_id = str(item.data(0, Qt.ItemDataRole.UserRole) or "")
        critical = next((hit for hit in unit.critical_hits if hit.critical_id == critical_id), None)
        if critical is None or critical.repaired:
            return
        if not critical.repairable:
            QMessageBox.information(self, "Critical Repair", "Vital Systems critical hits cannot be repaired.")
            return
        current_turn = self._game.turn_number if self._game is not None else 1
        if not critical.can_repair_on_turn(current_turn):
            QMessageBox.information(
                self,
                "Critical Repair",
                "This critical is New and cannot be repaired until the next turn.",
            )
            return
        updated = unit.set_critical_repaired(
            critical_id,
            True,
            current_turn=current_turn,
        )
        self._replace_selected_unit(updated, reload_controls=True)

    def _update_repair_button(self) -> None:
        unit = self._selected_unit()
        item = self.critical_tree.currentItem()
        enabled = False
        if unit is not None and item is not None:
            critical_id = str(item.data(0, Qt.ItemDataRole.UserRole) or "")
            critical = next((hit for hit in unit.critical_hits if hit.critical_id == critical_id), None)
            current_turn = self._game.turn_number if self._game is not None else 1
            enabled = bool(critical and critical.can_repair_on_turn(current_turn))
        self.repair_critical_button.setEnabled(enabled)

    def _toggle_weapon_disabled(self) -> None:
        unit = self._selected_unit()
        key = self._selected_tree_key(self.weapon_tree)
        if unit is None or not key:
            return
        weapon = next(item for item in unit.weapons if item.weapon_key == key)
        self._replace_selected_unit(unit.set_weapon_disabled(key, not weapon.disabled), reload_controls=True)

    def _toggle_weapon_destroyed(self) -> None:
        unit = self._selected_unit()
        key = self._selected_tree_key(self.weapon_tree)
        if unit is None or not key:
            return
        weapon = next(item for item in unit.weapons if item.weapon_key == key)
        self._replace_selected_unit(unit.set_weapon_destroyed(key, not weapon.destroyed), reload_controls=True)

    def _toggle_trait_disabled(self) -> None:
        unit = self._selected_unit()
        key = self._selected_trait_key()
        if unit is None or not key:
            return
        trait = next(item for item in unit.traits if item.trait_key == key)
        self._replace_selected_unit(unit.set_trait_disabled(key, not trait.disabled), reload_controls=True)

    def _toggle_trait_destroyed(self) -> None:
        unit = self._selected_unit()
        key = self._selected_trait_key()
        if unit is None or not key:
            return
        trait = next(item for item in unit.traits if item.trait_key == key)
        self._replace_selected_unit(unit.set_trait_destroyed(key, not trait.destroyed), reload_controls=True)

    def _selected_trait_key(self) -> str:
        item = self.trait_tree.currentItem()
        if item is None:
            return ""
        column = max(0, self.trait_tree.currentColumn())
        return str(item.data(column, Qt.ItemDataRole.UserRole) or "")

    @staticmethod
    def _selected_tree_key(tree: QTreeWidget) -> str:
        item = tree.currentItem()
        return str(item.data(0, Qt.ItemDataRole.UserRole) or "") if item is not None else ""

    def _selected_unit(self) -> TacticalUnitState | None:
        if self._game is None:
            return None
        item = self.unit_tree.currentItem()
        if item is None:
            return None
        unit_id = item.data(0, Qt.ItemDataRole.UserRole)
        if not unit_id:
            return None
        try:
            return self._game.get_unit(str(unit_id))
        except KeyError:
            return None

    def _replace_selected_unit(self, unit: TacticalUnitState, *, reload_controls: bool = False) -> None:
        if self._game is None:
            return
        self._game = self._game.replace_unit(unit)
        self._set_dirty(True)

        # Independently purchased craft are displayed beneath a synthetic group
        # whose status is derived from all sibling flights. Rebuild that small
        # roster view after any individual flight changes so Ready/Launched/Lost
        # totals and the selected row stay synchronized.
        if unit.kind is UnitKind.CRAFT:
            self._populate_unit_tree(selected_unit_id=unit.unit_id)
            if reload_controls:
                self._load_unit_controls(self._game.get_unit(unit.unit_id))
            return

        item = self._unit_items.get(unit.unit_id)
        if item is not None:
            self._configure_unit_item(item, unit)
        self._update_summary()
        if reload_controls:
            self._load_unit_controls(unit)

    def _damage_changed(self, value: int) -> None:
        if self._loading_controls:
            return
        unit = self._selected_unit()
        if unit is None or not unit.damage.available:
            return
        updated = unit.set_damage_current(value)
        self._replace_selected_unit(updated, reload_controls=True)
        self._sync_destroyed_checkbox(updated)

    def _crew_changed(self, value: int) -> None:
        if self._loading_controls:
            return
        unit = self._selected_unit()
        if unit is None or not unit.crew.available:
            return
        self._replace_selected_unit(unit.set_crew_current(value), reload_controls=True)

    def _shields_changed(self, value: int) -> None:
        if self._loading_controls:
            return
        unit = self._selected_unit()
        if unit is None or not unit.shields.available:
            return
        self._replace_selected_unit(unit.set_shields_current(value), reload_controls=True)

    def _destroyed_changed(self, checked: bool) -> None:
        if self._loading_controls:
            return
        unit = self._selected_unit()
        if unit is None:
            return
        updated = unit.mark_destroyed(checked)
        self._replace_selected_unit(updated, reload_controls=True)
        self._sync_destroyed_checkbox(updated)

    def _sync_destroyed_checkbox(self, unit: TacticalUnitState) -> None:
        self.destroyed_checkbox.blockSignals(True)
        try:
            self.destroyed_checkbox.setChecked(unit.is_destroyed)
        finally:
            self.destroyed_checkbox.blockSignals(False)

    def _crew_quality_preview_changed(self, value: str) -> None:
        if self._loading_controls:
            return
        unit = self._selected_unit()
        if unit is None or unit.kind is UnitKind.CRAFT:
            return
        preview = unit.set_crew_quality(value)
        current_turn = self._game.turn_number if self._game is not None else 1
        self.damage_control_label.setText(preview.damage_control_equation(current_turn))
        self._update_special_action_rules(self.special_action_combo.currentIndex())

    def _crew_quality_changed(self) -> None:
        if self._loading_controls:
            return
        unit = self._selected_unit()
        if unit is not None and self.crew_quality_edit.text().strip() != unit.crew_quality:
            self._replace_selected_unit(unit.set_crew_quality(self.crew_quality_edit.text()))

    def _special_action_changed(self, index: int) -> None:
        if self._loading_controls or index < 0:
            return
        unit = self._selected_unit()
        if unit is None:
            return
        action = str(self.special_action_combo.itemData(index) or "")
        normalized = "" if action == "None / Normal Operations" else action
        if normalized != unit.special_action:
            self._replace_selected_unit(unit.set_special_action(normalized), reload_controls=False)

    def _unit_notes_changed(self) -> None:
        if self._loading_controls:
            return
        unit = self._selected_unit()
        if unit is not None and self.unit_notes_edit.toPlainText() != unit.notes:
            self._replace_selected_unit(unit.set_notes(self.unit_notes_edit.toPlainText()))

    def _game_name_changed(self) -> None:
        if self._loading_controls or self._game is None:
            return
        name = self.game_name_edit.text().strip()
        if not name:
            self.game_name_edit.setText(self._game.name)
            return
        if name != self._game.name:
            self._game = self._game.rename(name)
            self._set_dirty(True)

    def _turn_changed(self, value: int) -> None:
        if self._loading_controls or self._game is None:
            return
        if value != self._game.turn_number:
            self._game = self._game.set_turn_number(value)
            self._set_dirty(True)
            selected = self._selected_unit()
            if selected is not None:
                self._load_unit_controls(self._game.get_unit(selected.unit_id))

    def _phase_changed(self, index: int) -> None:
        if self._loading_controls or self._game is None or index < 0:
            return
        phase = GamePhase(str(self.phase_combo.itemData(index)))
        if phase is not self._game.phase:
            self._game = self._game.set_phase(phase)
            self._set_dirty(True)

    def _scenario_changed(self, index: int) -> None:
        if self._loading_controls or self._game is None or index < 0:
            return
        key = str(self.scenario_combo.itemData(index) or "")
        if key == "__random__":
            selected = random_scenario()
            key = selected.key
            self._loading_controls = True
            try:
                self.scenario_combo.setCurrentIndex(self.scenario_combo.findData(key))
            finally:
                self._loading_controls = False
        if key != self._game.scenario_key:
            self._game = self._game.set_scenario(key)
            self._set_dirty(True)
        self._refresh_scenario_summary()

    def _scenario_priority_changed(self, index: int) -> None:
        if self._loading_controls or self._game is None or index < 0:
            return
        value = str(self.scenario_priority_combo.itemData(index) or "")
        if value != self._game.scenario_priority:
            self._game = self._game.set_scenario_priority(value)
            self._set_dirty(True)
        self._refresh_scenario_summary()

    def _player_role_changed(self, index: int) -> None:
        if self._loading_controls or self._game is None or index < 0:
            return
        value = str(self.player_role_combo.itemData(index) or "")
        if value != self._game.player_role:
            self._game = self._game.set_player_role(value)
            self._set_dirty(True)
        self._refresh_scenario_summary()

    def _randomize_scenario_priority(self) -> None:
        value = random_priority_level()
        index = self.scenario_priority_combo.findData(value)
        if index >= 0:
            self.scenario_priority_combo.setCurrentIndex(index)

    def _randomize_player_role(self) -> None:
        value = random_player_role()
        index = self.player_role_combo.findData(value)
        if index >= 0:
            self.player_role_combo.setCurrentIndex(index)

    def _refresh_scenario_summary(self) -> None:
        empty_help = (
            "Select a scenario to view its setup, special rules, game length, "
            "and victory conditions."
        )
        if self._game is None:
            self.scenario_rules_label.setText("No scenario selected")
            self.scenario_rules_label.setToolTip(empty_help)
            self.scenario_group.set_help_content("Scenario Rules", empty_help)
            self.scenario_map_button.setEnabled(False)
            return
        scenario = SCENARIO_BY_KEY.get(self._game.scenario_key)
        if scenario is None:
            self.scenario_rules_label.setText("No scenario selected")
            self.scenario_rules_label.setToolTip(empty_help)
            self.scenario_group.set_help_content("Scenario Rules", empty_help)
            self.scenario_map_button.setEnabled(False)
            return
        summary = f"{scenario.game_length}  {scenario.victory}"
        self.scenario_rules_label.setText(summary)
        self.scenario_rules_label.setToolTip(scenario.display_text)
        self.scenario_group.set_help_content(f"{scenario.name} - Scenario Rules", scenario.display_text)
        map_path = self._scenario_map_path(scenario.key)
        has_map = map_path is not None and map_path.is_file()
        self.scenario_map_button.setEnabled(has_map)
        self.scenario_map_button.setToolTip(
            "Show the printed deployment map."
            if has_map
            else "No separate printed deployment map is available for this scenario."
        )

    def _scenario_map_path(self, scenario_key: str) -> Path | None:
        filename = SCENARIO_MAP_FILES.get(str(scenario_key or ""))
        if not filename:
            return None
        relative = Path("scenario_maps") / filename
        resolver = getattr(self._context.resources, "path", None)
        if callable(resolver):
            return Path(resolver(relative))
        return Path(self._context.resources.project_root) / "resources" / relative

    def _show_scenario_map(self) -> None:
        if self._game is None:
            return
        scenario = SCENARIO_BY_KEY.get(self._game.scenario_key)
        if scenario is None:
            return
        map_path = self._scenario_map_path(scenario.key)
        if map_path is None or not map_path.is_file():
            return
        _ScenarioMapDialog(
            f"{scenario.name} - Deployment Map",
            map_path,
            self,
        ).exec()

    def _disposition_changed(self, index: int) -> None:
        if self._loading_controls or index < 0:
            return
        unit = self._selected_unit()
        if unit is None:
            return
        disposition = UnitDisposition(str(self.disposition_combo.itemData(index)))
        if unit.kind is UnitKind.CRAFT and disposition not in {
            UnitDisposition.OPERATIONAL,
            UnitDisposition.DESTROYED,
        }:
            return
        if disposition is not unit.disposition or (
            disposition is UnitDisposition.DESTROYED and not unit.destroyed
        ):
            self._replace_selected_unit(unit.set_disposition(disposition), reload_controls=True)

    def _correct_crippled_status(self) -> None:
        unit = self._selected_unit()
        if unit is None or not unit.is_crippled:
            return
        answer = QMessageBox.question(
            self,
            "Correct Crippled Status",
            "Remove Crippled status as a data-entry correction? This is not a Damage Control repair.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if answer == QMessageBox.StandardButton.Yes:
            self._replace_selected_unit(unit.correct_crippled_status(), reload_controls=True)

    def _correct_skeleton_status(self) -> None:
        unit = self._selected_unit()
        if unit is None or not unit.is_skeleton_crew:
            return
        answer = QMessageBox.question(
            self,
            "Correct Skeleton Crew Status",
            "Remove Skeleton Crew status as a data-entry correction? This is not a Crew recovery effect.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if answer == QMessageBox.StandardButton.Yes:
            self._replace_selected_unit(unit.correct_skeleton_crew_status(), reload_controls=True)

    def _advance_turn(self) -> None:
        if self._game is None:
            return
        selected = self._selected_unit()
        self._game = self._game.advance_turn()
        self._loading_controls = True
        try:
            self.turn_spin.setValue(self._game.turn_number)
            index = self.phase_combo.findData(self._game.phase.value)
            self.phase_combo.setCurrentIndex(max(0, index))
        finally:
            self._loading_controls = False
        if selected is not None:
            self._load_unit_controls(self._game.get_unit(selected.unit_id))
        self._set_dirty(True)
        self._context.status.set(f"Turn {self._game.turn_number}: {self._game.phase.value.title()}")

    def _show_end_game_report(self) -> None:
        if self._game is None:
            return
        dialog = _BattleReportDialog(self._game, self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        self._game = self._game.end_game(
            victory_points=dialog.victory_points_spin.value(),
            opponent_victory_points=dialog.opponent_points_spin.value(),
            notes=dialog.notes_edit.toPlainText(),
        )
        self._loading_controls = True
        try:
            index = self.phase_combo.findData(GamePhase.END.value)
            self.phase_combo.setCurrentIndex(max(0, index))
        finally:
            self._loading_controls = False
        self._set_dirty(True)
        self._context.status.set(
            f"Battle ended: {self._game.battle_result} "
            f"({self._game.victory_points}-{self._game.opponent_victory_points} VP)"
        )

    def _update_summary(self) -> None:
        if self._game is None:
            self.unit_summary_label.setText("No game loaded")
            return
        platforms = sum(1 for unit in self._game.units if unit.kind is UnitKind.PLATFORM)
        craft = sum(1 for unit in self._game.units if unit.kind is UnitKind.CRAFT)
        destroyed = sum(1 for unit in self._game.units if unit.is_destroyed)
        launched = sum(
            1
            for unit in self._game.units
            if unit.kind is UnitKind.CRAFT and unit.effective_craft_status == "launched"
        )
        self.unit_summary_label.setText(
            f"{platforms} platforms  |  {craft} craft  |  "
            f"{launched} launched  |  {destroyed} destroyed/lost  |  "
            f"{len(self._game.units)} total units"
        )

    def _set_dirty(self, dirty: bool) -> None:
        self._dirty = bool(dirty and self._game is not None)
        self.dirty_label.setText("* Unsaved changes" if self._dirty else "")
        self._update_file_buttons()

    def _update_file_buttons(self) -> None:
        loaded = self._game is not None
        self.save_button.setEnabled(loaded and self._dirty)
        self.save_as_button.setEnabled(loaded)

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

    def _default_game_folder(self) -> Path:
        configured = self._context.settings.get_str("tactical/default_folder", "").strip()
        folder = self._context.resources.writable_folder(
            configured,
            self._context.resources.game_files_root,
        )
        if not configured or Path(configured).expanduser().resolve() != folder:
            self._context.settings.set_value("tactical/default_folder", str(folder))
            self._context.settings.sync()
        return folder

    def _remember_game_folder(self, path: Path) -> None:
        self._context.settings.set_value("tactical/default_folder", str(path.parent.resolve()))
        self._context.settings.sync()

    def _suggested_game_filename(self) -> str:
        name = self._game.name if self._game is not None else "Untitled Battle"
        safe = re.sub(r"[^A-Za-z0-9._ -]+", "_", name).strip(" .") or "Untitled Battle"
        return f"{safe}{self.GAME_EXTENSION}"

    def _ensure_game_extension(self, path: Path) -> Path:
        if str(path).casefold().endswith(self.GAME_EXTENSION):
            return path
        return Path(str(path) + self.GAME_EXTENSION)
