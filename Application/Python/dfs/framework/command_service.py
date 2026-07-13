"""Small command registry shared by menus, shortcuts and future palette."""
from __future__ import annotations
from collections.abc import Callable
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Command:
    id: str
    label: str
    callback: Callable[[], None]
    shortcut: str | None = None


class CommandService:
    def __init__(self) -> None:
        self._commands: dict[str, Command] = {}

    def register(self, command: Command) -> None:
        if command.id in self._commands:
            raise ValueError(f"DFS command already registered: {command.id}")
        self._commands[command.id] = command

    def execute(self, command_id: str) -> None:
        try:
            command = self._commands[command_id]
        except KeyError as exc:
            raise KeyError(f"Unknown DFS command: {command_id}") from exc
        command.callback()

    def list_commands(self) -> tuple[Command, ...]:
        return tuple(sorted(self._commands.values(), key=lambda item: item.label.lower()))
