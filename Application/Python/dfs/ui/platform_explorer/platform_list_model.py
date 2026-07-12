"""Compact list model and delegate for Platform Explorer results."""

from __future__ import annotations

from PySide6.QtCore import QAbstractListModel, QModelIndex, QRect, QSize, Qt
from PySide6.QtGui import QFont, QFontMetrics, QPainter, QPalette
from PySide6.QtWidgets import QStyle, QStyledItemDelegate, QStyleOptionViewItem

from dfs.domain.catalog import PlatformSummary


class PlatformListModel(QAbstractListModel):
    def __init__(self) -> None:
        super().__init__()
        self._platforms: list[PlatformSummary] = []

    def set_platforms(self, platforms: list[PlatformSummary]) -> None:
        self.beginResetModel()
        self._platforms = list(platforms)
        self.endResetModel()

    def platform_at(self, row: int) -> PlatformSummary | None:
        if 0 <= row < len(self._platforms):
            return self._platforms[row]
        return None

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:  # noqa: N802
        return 0 if parent.isValid() else len(self._platforms)

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole):
        platform = self.platform_at(index.row()) if index.isValid() else None
        if platform is None:
            return None
        if role == Qt.ItemDataRole.DisplayRole:
            return platform.name
        if role == Qt.ItemDataRole.UserRole:
            return platform.ship_id
        if role == Qt.ItemDataRole.ToolTipRole:
            fleets = ", ".join(platform.fleet_names) or "No fleet profile"
            priorities = ", ".join(platform.priority_levels) or "—"
            service = ", ".join(platform.in_service_values) or "—"
            return (
                f"{platform.name}\n"
                f"{platform.faction_name}\n"
                f"Fleet / Era: {fleets}\n"
                f"Priority: {priorities}\n"
                f"In Service: {service}"
            )
        return None


class PlatformListDelegate(QStyledItemDelegate):
    """Draw a readable two-line navigation item instead of database columns."""

    H_PADDING = 12
    V_PADDING = 8
    ROW_HEIGHT = 58

    def sizeHint(self, option: QStyleOptionViewItem, index: QModelIndex) -> QSize:  # noqa: N802
        return QSize(max(option.rect.width(), 220), self.ROW_HEIGHT)

    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index: QModelIndex) -> None:
        model = index.model()
        platform = model.platform_at(index.row()) if hasattr(model, "platform_at") else None
        if platform is None:
            super().paint(painter, option, index)
            return

        painter.save()
        selected = bool(option.state & QStyle.StateFlag.State_Selected)
        hovered = bool(option.state & QStyle.StateFlag.State_MouseOver)
        palette = option.palette

        if selected:
            background = palette.color(QPalette.ColorRole.Highlight)
        elif hovered:
            background = palette.color(QPalette.ColorRole.AlternateBase)
        else:
            background = palette.color(QPalette.ColorRole.Base)
        painter.fillRect(option.rect, background)

        name_color = (
            palette.color(QPalette.ColorRole.HighlightedText)
            if selected else palette.color(QPalette.ColorRole.Text)
        )
        meta_color = (
            palette.color(QPalette.ColorRole.HighlightedText)
            if selected else palette.color(QPalette.ColorRole.PlaceholderText)
        )

        text_rect = option.rect.adjusted(self.H_PADDING, self.V_PADDING, -self.H_PADDING, -self.V_PADDING)
        name_font = QFont(option.font)
        name_font.setBold(True)
        name_metrics = QFontMetrics(name_font)
        name = name_metrics.elidedText(platform.name, Qt.TextElideMode.ElideRight, text_rect.width())
        painter.setFont(name_font)
        painter.setPen(name_color)
        painter.drawText(
            QRect(text_rect.left(), text_rect.top(), text_rect.width(), 22),
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
            name,
        )

        profile_label = (
            f"{platform.profile_count} profiles" if platform.profile_count != 1 else "1 profile"
        )
        meta = f"{platform.faction_name}  ·  {profile_label}"
        meta_font = QFont(option.font)
        meta_font.setPointSize(max(meta_font.pointSize() - 1, 8))
        meta_metrics = QFontMetrics(meta_font)
        meta = meta_metrics.elidedText(meta, Qt.TextElideMode.ElideRight, text_rect.width())
        painter.setFont(meta_font)
        painter.setPen(meta_color)
        painter.drawText(
            QRect(text_rect.left(), text_rect.top() + 24, text_rect.width(), 18),
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
            meta,
        )

        line_color = palette.color(QPalette.ColorRole.Midlight)
        painter.setPen(line_color)
        painter.drawLine(option.rect.bottomLeft(), option.rect.bottomRight())
        painter.restore()
