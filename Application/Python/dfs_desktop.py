"""Launch the DFS desktop application.

Run from the project Python folder with::

    python dfs_desktop.py
"""

from __future__ import annotations

import sys

try:
    from PySide6.QtCore import Qt, QTimer
    from PySide6.QtGui import QPixmap
    from PySide6.QtWidgets import QApplication, QLabel, QMessageBox, QSplashScreen
except ModuleNotFoundError as exc:
    raise SystemExit(
        "PySide6 is required for the DFS desktop application. Install it with:\n"
        "    python -m pip install PySide6"
    ) from exc

from dfs.app_paths import DatabaseNotFoundError, find_database_path
from dfs.bootstrap import build_application_services
from dfs.ui.main_window import MainWindow
from dfs.ui.theme import APPLICATION_STYLESHEET


def _make_splash() -> QSplashScreen:
    pixmap = QPixmap(620, 300)
    pixmap.fill(Qt.GlobalColor.white)
    splash = QSplashScreen(pixmap)
    label = QLabel(
        "<div style='text-align:center'>"
        "<div style='font-size:30px;font-weight:700'>Dee's Fighting Ships</div>"
        "<div style='font-size:17px;color:#475569'>Tactical Reference System</div>"
        "<div style='font-size:14px;color:#64748b;margin-top:14px'>"
        "Babylon 5: A Call to Arms</div>"
        "</div>",
        splash,
    )
    label.setGeometry(40, 55, 540, 150)
    label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    return splash


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("Dee's Fighting Ships")
    app.setApplicationVersion("2.0.0-alpha2")
    app.setOrganizationName("DFS")
    app.setStyleSheet(APPLICATION_STYLESHEET)

    splash = _make_splash()
    splash.show()
    splash.showMessage(
        "Loading platform database…",
        Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignHCenter,
        Qt.GlobalColor.darkGray,
    )
    app.processEvents()

    try:
        database_path = find_database_path()
        services = build_application_services(database_path)
    except (DatabaseNotFoundError, OSError) as exc:
        splash.close()
        QMessageBox.critical(None, "DFS database not found", str(exc))
        return 1

    window = MainWindow(services, f"Database: {database_path.name}")
    window.show()
    splash.finish(window)
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
