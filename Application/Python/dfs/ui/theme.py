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
}
QSplitter::handle:hover {
    background: #cbd5e1;
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
