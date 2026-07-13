"""Application-wide notification publisher."""
from __future__ import annotations
from dataclasses import dataclass
from PySide6.QtCore import QObject, Signal


@dataclass(frozen=True, slots=True)
class Notification:
    level: str
    title: str
    message: str


class NotificationService(QObject):
    published = Signal(object)

    def publish(self, level: str, title: str, message: str) -> None:
        self.published.emit(Notification(level, title, message))

    def info(self, title: str, message: str) -> None:
        self.publish("info", title, message)

    def success(self, title: str, message: str) -> None:
        self.publish("success", title, message)

    def warning(self, title: str, message: str) -> None:
        self.publish("warning", title, message)

    def error(self, title: str, message: str) -> None:
        self.publish("error", title, message)
