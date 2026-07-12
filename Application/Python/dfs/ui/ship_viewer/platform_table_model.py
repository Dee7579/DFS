"""Qt table model for platform catalog results."""

from __future__ import annotations

from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt

from dfs.domain.catalog import PlatformSummary


class PlatformTableModel(QAbstractTableModel):
    HEADERS = ("Platform", "Faction", "Fleet / Era", "Priority", "In Service")

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

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:  # noqa: N802
        return 0 if parent.isValid() else len(self.HEADERS)

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.ItemDataRole.DisplayRole):  # noqa: N802
        if role == Qt.ItemDataRole.DisplayRole and orientation == Qt.Orientation.Horizontal:
            if 0 <= section < len(self.HEADERS):
                return self.HEADERS[section]
        return None

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole):
        if not index.isValid() or not (0 <= index.row() < len(self._platforms)):
            return None
        platform = self._platforms[index.row()]
        if role == Qt.ItemDataRole.UserRole:
            return platform.ship_id
        if role == Qt.ItemDataRole.ToolTipRole:
            if index.column() == 4:
                return "\n".join(platform.in_service_values) or "—"
            return None
        if role != Qt.ItemDataRole.DisplayRole:
            return None
        values = (
            platform.name,
            platform.faction_name,
            ", ".join(platform.fleet_names),
            ", ".join(platform.priority_levels),
            ", ".join(platform.in_service_values),
        )
        return values[index.column()]
