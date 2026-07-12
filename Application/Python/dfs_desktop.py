"""Launch the DFS desktop application.

Run from the project Python folder with::

    python dfs_desktop.py
"""

from __future__ import annotations

import sys

try:
    from PySide6.QtWidgets import QApplication, QMessageBox
except ModuleNotFoundError as exc:  # Friendly guidance before importing GUI modules.
    raise SystemExit(
        "PySide6 is required for the DFS desktop application. Install it with:\n"
        "    python -m pip install PySide6"
    ) from exc

from dfs.app_paths import DatabaseNotFoundError, find_database_path
from dfs.bootstrap import build_application_services
from dfs.ui.main_window import MainWindow
from dfs.ui.theme import APPLICATION_STYLESHEET


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("Dee's Fighting Ships")
    app.setOrganizationName("DFS")
    app.setStyleSheet(APPLICATION_STYLESHEET)

    try:
        database_path = find_database_path()
        services = build_application_services(database_path)
    except (DatabaseNotFoundError, OSError) as exc:
        QMessageBox.critical(None, "DFS database not found", str(exc))
        return 1

    window = MainWindow(services, f"Database: {database_path.name}")
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
