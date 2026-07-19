"""Reusable Fleet Builder knowledge panel.

Sprint 002D.3.5 implements the Rules tab first.  Additional tabs can be added
without changing the Fleet Builder's outer layout.
"""
from __future__ import annotations

from collections import defaultdict
from html import escape

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTabWidget,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

from dfs.domain.fleet import ValidationSeverity


class FleetKnowledgePanel(QWidget):
    """Context-sensitive information panel for a fleet or selected platform."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._all_records: list[dict] = []
        self._subject = "Fleet"
        self._developer = False

        title = QLabel("Knowledge Panel")
        title.setObjectName("pageTitle")
        self.subject_label = QLabel("Fleet")
        self.subject_label.setObjectName("pageSubtitle")
        self.status_label = QLabel("No rules evaluated")
        self.status_label.setWordWrap(True)

        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Search rules, sources, or Rule IDs…")
        self.search_edit.textChanged.connect(self._render)

        self.developer_check = QCheckBox("Developer details")
        self.developer_check.toggled.connect(self._set_developer)
        self.failures_button = QPushButton("Show failures")
        self.failures_button.setCheckable(True)
        self.failures_button.toggled.connect(self._render)

        controls = QHBoxLayout()
        controls.addWidget(self.search_edit, 1)
        controls.addWidget(self.failures_button)
        controls.addWidget(self.developer_check)

        self.rules_browser = QTextBrowser()
        self.rules_browser.setOpenExternalLinks(False)
        self.rules_browser.setMinimumWidth(330)

        tabs = QTabWidget()
        rules_page = QWidget()
        rules_layout = QVBoxLayout(rules_page)
        rules_layout.setContentsMargins(8, 8, 8, 8)
        rules_layout.addLayout(controls)
        rules_layout.addWidget(self.rules_browser, 1)
        tabs.addTab(rules_page, "Rules")

        placeholder = QTextBrowser()
        placeholder.setHtml(
            "<h3>Knowledge Panel Framework</h3>"
            "<p>Ship details, weapons, notes, and Codex links will use this shared panel in later sprints.</p>"
        )
        tabs.addTab(placeholder, "Overview")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.addWidget(title)
        layout.addWidget(self.subject_label)
        layout.addWidget(self.status_label)
        layout.addWidget(tabs, 1)

    def clear(self, subject: str = "Fleet") -> None:
        self._subject = subject
        self._all_records = []
        self.subject_label.setText(subject)
        self.status_label.setText("No rules evaluated")
        self.rules_browser.setHtml("<p>Select a platform or build a fleet to inspect its construction rules.</p>")

    def set_rule_records(self, subject: str, records: list[dict]) -> None:
        self._subject = subject
        self._all_records = records
        self.subject_label.setText(subject)
        self._render()

    def _set_developer(self, checked: bool) -> None:
        self._developer = checked
        self._render()

    def _render(self, *_args) -> None:
        query = self.search_edit.text().strip().lower()
        failures_only = self.failures_button.isChecked()
        records = []
        for record in self._all_records:
            if failures_only and record.get("status") == "pass":
                continue
            haystack = " ".join(
                str(record.get(key, ""))
                for key in ("title", "explanation", "rule_id", "source", "category")
            ).lower()
            if query and query not in haystack:
                continue
            records.append(record)

        totals = defaultdict(int)
        for record in self._all_records:
            totals[record.get("status", "pass")] += 1
        checked = len(self._all_records)
        self.status_label.setText(
            f"{checked} rules checked  •  {totals['pass']} passed  •  "
            f"{totals['advisory']} advisory  •  {totals['failed']} failed"
        )

        if not records:
            self.rules_browser.setHtml("<p>No rules match the current filter.</p>")
            return

        blocks: list[str] = []
        for index, record in enumerate(records, start=1):
            status = record.get("status", "pass")
            symbol = {"pass": "✓", "advisory": "⚠", "failed": "✗"}.get(status, "•")
            label = {"pass": "PASS", "advisory": "ADVISORY", "failed": "FAILED"}.get(status, status.upper())
            remedies = record.get("remedies") or ()
            remedy_html = ""
            if remedies:
                remedy_html = "<p><b>How to make this legal</b></p><ul>" + "".join(
                    f"<li>{escape(str(item))}</li>" for item in remedies
                ) + "</ul>"
            metadata = (
                f"<p><b>Rule ID:</b> {escape(str(record.get('rule_id', '—')))}<br>"
                f"<b>Source:</b> {escape(str(record.get('source', '—')))}</p>"
            )
            if self._developer:
                metadata += (
                    f"<p><b>Evaluation order:</b> {index}<br>"
                    f"<b>Category:</b> {escape(str(record.get('category', '—')))}<br>"
                    f"<b>Status:</b> {label}</p>"
                )
            blocks.append(
                "<div style='margin-bottom:14px'>"
                f"<h3>{symbol} {escape(str(record.get('title', 'Construction Rule')))}</h3>"
                f"<p><b>{label}</b></p>"
                f"<p>{escape(str(record.get('explanation', ''))).replace(chr(10), '<br>')}</p>"
                f"{remedy_html}{metadata}</div><hr>"
            )
        self.rules_browser.setHtml("".join(blocks))
