"""Launch the DFS desktop application.

Run from the project Python folder with::

    python dfs_desktop.py
"""

from __future__ import annotations

import sys
import time

try:
    from PySide6.QtCore import Qt, QTimer, QSettings
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


APP_VERSION = "2.1.0-alpha2"
MINIMUM_SPLASH_MS = 3000


def _make_splash(system_name: str) -> QSplashScreen:
    pixmap = QPixmap(620, 330)
    pixmap.fill(Qt.GlobalColor.white)
    splash = QSplashScreen(pixmap)
    label = QLabel(
        "<div style='text-align:center'>"
        "<div style='font-size:30px;font-weight:700'>Dee's Fighting Ships</div>"
        "<div style='font-size:17px;color:#475569'>Tactical Reference System</div>"
        "<div style='font-size:14px;color:#64748b;margin-top:14px'>"
        f"{system_name}</div>"
        f"<div style='font-size:11px;color:#94a3b8;margin-top:12px'>Version {APP_VERSION}</div>"
        "</div>",
        splash,
    )
    label.setGeometry(40, 42, 540, 190)
    label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    return splash


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("Dee's Fighting Ships")
    app.setApplicationVersion(APP_VERSION)
    app.setOrganizationName("DFS")
    app.setStyleSheet(APPLICATION_STYLESHEET)

    settings = QSettings()
    selected_system = settings.value("application/game_system", "b5_acta_2e", type=str)
    system_names = {
        "b5_acta_2e": "Babylon 5: A Call to Arms",
        "victory_at_sea": "Victory at Sea",
    }
    splash = _make_splash(system_names.get(selected_system, ""))
    splash_started = time.monotonic()
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

    splash.showMessage(
        "Platform database ready  •  Loading presentation engine…",
        Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignHCenter,
        Qt.GlobalColor.darkGray,
    )
    app.processEvents()
    window = MainWindow(services, f"Database: {database_path.name}")

    # Timed status changes make a fast startup readable without delaying a slow one.
    QTimer.singleShot(
        900,
        lambda: splash.showMessage(
            "Platform database ready  •  Presentation engine ready  •  Loading workspace…",
            Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignHCenter,
            Qt.GlobalColor.darkGray,
        ),
    )
    QTimer.singleShot(
        2000,
        lambda: splash.showMessage(
            "Ready",
            Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignHCenter,
            Qt.GlobalColor.darkGray,
        ),
    )

    elapsed_ms = int((time.monotonic() - splash_started) * 1000)
    remaining_ms = max(0, MINIMUM_SPLASH_MS - elapsed_ms)

    def reveal_window() -> None:
        window.show()
        splash.finish(window)

    QTimer.singleShot(remaining_ms, reveal_window)
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
