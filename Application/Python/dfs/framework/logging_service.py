"""Central DFS logging configuration."""
from __future__ import annotations
import logging
from pathlib import Path


class LoggingService:
    def __init__(self, log_path: Path) -> None:
        log_path.parent.mkdir(parents=True, exist_ok=True)
        self.log_path = log_path
        self._logger = logging.getLogger("dfs")
        self._logger.setLevel(logging.INFO)
        if not self._logger.handlers:
            handler = logging.FileHandler(log_path, encoding="utf-8")
            handler.setFormatter(logging.Formatter(
                "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
            ))
            self._logger.addHandler(handler)

    def get_logger(self, name: str | None = None) -> logging.Logger:
        return logging.getLogger(f"dfs.{name}") if name else self._logger
