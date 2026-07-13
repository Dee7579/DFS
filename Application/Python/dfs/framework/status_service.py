"""Application-wide status publisher."""
from __future__ import annotations
from PySide6.QtCore import QObject, Signal


class StatusService(QObject):
    changed = Signal(str)

    def __init__(self) -> None:
        super().__init__()
        self._message = "Ready"

    @property
    def message(self) -> str:
        return self._message

    def set(self, message: str) -> None:
        self._message = message.strip() or "Ready"
        self.changed.emit(self._message)

    def ready(self) -> None:
        self.set("Ready")
