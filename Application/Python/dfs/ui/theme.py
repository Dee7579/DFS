"""Centralized DFS desktop theme."""

from __future__ import annotations


APPLICATION_STYLESHEET = """
QMainWindow, QWidget {
    font-family: "Segoe UI";
    font-size: 10pt;
}
QWidget#sidebar {
    background: #1f2937;
    color: #f9fafb;
}
QLabel#appName {
    color: #ffffff;
    font-size: 22pt;
    font-weight: 700;
    padding: 14px 8px;
}
QLabel#appTagline {
    color: #94a3b8;
    font-size: 8pt;
    font-weight: 600;
    padding: 0 8px 14px 8px;
}
QLabel#databaseLabel {
    color: #9ca3af;
    font-size: 8pt;
    padding: 10px 4px;
}
QListWidget#navigation {
    background: transparent;
    border: none;
    color: #d1d5db;
    outline: none;
}
QListWidget#navigation::item {
    padding: 11px 12px;
    border-radius: 5px;
}
QListWidget#navigation::item:selected {
    background: #374151;
    color: white;
}
QListWidget#navigation::item:disabled {
    color: #6b7280;
}
QLabel#dashboardTitle {
    font-size: 30pt;
    font-weight: 700;
}
QLabel#dashboardSubtitle, QLabel#pageSubtitle, QLabel#platformSubtitle, QLabel#aboutSubtitle {
    color: #6b7280;
}
QLabel#pageTitle {
    font-size: 22pt;
    font-weight: 700;
}
QLabel#platformTitle {
    font-size: 18pt;
    font-weight: 650;
}
QLabel#resultCount {
    font-weight: 600;
    color: #374151;
}
QLabel#activeFilterSummary {
    color: #64748b;
    font-size: 9pt;
}
QPushButton#moduleButton {
    min-height: 110px;
    min-width: 200px;
    padding: 18px;
    text-align: left;
    font-size: 11pt;
}
QFrame#filterPanel {
    background: #f3f4f6;
    border-radius: 7px;
}
QGroupBox {
    font-weight: 600;
    margin-top: 8px;
    padding-top: 8px;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 8px;
    padding: 0 3px;
}
QLineEdit, QComboBox, QSpinBox, QPushButton {
    min-height: 28px;
}
QTableView, QTableWidget, QListWidget {
    border: 1px solid #d1d5db;
    border-radius: 4px;
}
QHeaderView::section {
    background: #e5e7eb;
    padding: 6px;
    border: none;
    border-right: 1px solid #d1d5db;
}
QFrame#statCard {
    background: #f8fafc;
    border: 1px solid #dbe3ec;
    border-radius: 6px;
}
QLabel#statCardCaption {
    color: #64748b;
    font-size: 8pt;
    font-weight: 600;
}
QLabel#statCardValue {
    color: #111827;
    font-size: 14pt;
    font-weight: 700;
}
QFrame#profileDetails {
    background: #ffffff;
    border: 1px solid #e5e7eb;
    border-radius: 6px;
    padding: 6px;
}
QSplitter::handle {
    background: #e5e7eb;
    margin: 0 2px;
    border-left: 1px solid #cbd5e1;
    border-right: 1px solid #f8fafc;
}
QSplitter::handle:hover {
    background: #94a3b8;
    border-left: 1px solid #64748b;
    border-right: 1px solid #cbd5e1;
}
QLabel#dashboardStats {
    color: #475569;
    font-size: 11pt;
    font-weight: 600;
    padding-top: 8px;
}
QLabel#aboutTitle {
    font-size: 24pt;
    font-weight: 700;
}
QLabel#aboutCaption {
    color: #64748b;
    font-weight: 600;
    padding-right: 18px;
}
QLabel#aboutCredit {
    color: #475569;
    padding: 8px;
}
QListView {
    border: 1px solid #d1d5db;
    border-radius: 4px;
    outline: none;
}
QListView::item {
    border: none;
}
"""

# Splitter handles are intentionally wider than Qt defaults so they are easy
# to grab on high-resolution displays. The bordered center stripe provides a
# visible resize affordance without competing with the workspace.

# Phase 3E / 2.1 application-shell additions.
APPLICATION_STYLESHEET += """
QLabel#gameSystemCaption {
    color: #94a3b8;
    font-size: 8pt;
    font-weight: 600;
    padding: 4px 8px 0 8px;
}
QComboBox#gameSystemSelector {
    margin: 0 8px 8px 8px;
    padding: 5px 8px;
    background: #111827;
    color: #f9fafb;
    border: 1px solid #475569;
    border-radius: 5px;
}
QComboBox#gameSystemSelector QAbstractItemView {
    background: #ffffff;
    color: #111827;
    selection-background-color: #0f766e;
}
QFrame#dashboardCard {
    background: #ffffff;
    border: 1px solid #dbe3ec;
    border-radius: 8px;
    min-height: 190px;
    padding: 10px;
}
QLabel#dashboardCardTitle {
    color: #111827;
    font-size: 13pt;
    font-weight: 700;
    padding-bottom: 8px;
}
QLabel#dashboardCardBody {
    color: #475569;
    font-size: 10pt;
    line-height: 1.35;
}
QPushButton#primaryDashboardAction {
    background: #0f766e;
    color: white;
    border: none;
    border-radius: 6px;
    padding: 10px 18px;
    font-weight: 650;
}
QPushButton#primaryDashboardAction:hover {
    background: #115e59;
}
QPushButton#continueButton {
    text-align: left;
    padding: 12px;
    min-height: 56px;
    background: #f8fafc;
    border: 1px solid #cbd5e1;
    border-radius: 6px;
    font-weight: 600;
}
QPushButton#recentPlatformButton {
    text-align: left;
    padding: 5px 8px;
    background: transparent;
    border: none;
    color: #0f766e;
}
QPushButton#recentPlatformButton:hover {
    text-decoration: underline;
}
"""

# Phase 3F / Platform Explorer completion additions.
APPLICATION_STYLESHEET += """
QLabel#codexTitle {
    font-size: 16pt;
    font-weight: 700;
    color: #111827;
}
QLabel#codexMeta {
    color: #64748b;
    padding-bottom: 6px;
}
QTextBrowser {
    background: #ffffff;
    border: 1px solid #dbe3ec;
    border-radius: 6px;
    padding: 10px;
}
"""

# Phase 3G / final Platform Explorer polish.
APPLICATION_STYLESHEET += """
QDialog#codexPopover {
    background: #ffffff;
    border: 1px solid #94a3b8;
    border-radius: 8px;
}
QLabel#codexPopoverTitle {
    font-size: 15pt;
    font-weight: 700;
    color: #111827;
}
QLabel#codexPopoverMeta {
    color: #64748b;
    padding-bottom: 4px;
}
"""
