"""Launch the DFS desktop application."""
from __future__ import annotations

import sqlite3
import sys
import time

try:
    from PySide6.QtCore import Qt, QTimer
    from PySide6.QtGui import QPixmap
    from PySide6.QtWidgets import QApplication, QLabel, QMessageBox, QSplashScreen
except ModuleNotFoundError as exc:
    raise SystemExit(
        "PySide6 is required for the DFS desktop application. Install it with:\n"
        "    python -m pip install PySide6"
    ) from exc

from dfs.app_paths import (
    DatabaseNotFoundError,
    build_application_paths,
    find_database_path,
)
from dfs.bootstrap import build_application_context
from dfs.framework.settings_service import SettingsService
from dfs.ui.main_window import MainWindow

APP_VERSION = "2.4.0-alpha25"


def _run_release_smoke_test() -> int:
    """Verify that a packaged build can read every required runtime payload."""

    try:
        database_path = find_database_path()
        paths = build_application_paths(__file__)
        if not paths.resources_root.joinpath("scenario_maps").is_dir():
            raise FileNotFoundError("Packaged scenario maps are missing.")
        if not any(paths.resources_root.joinpath("scenario_maps").glob("*.png")):
            raise FileNotFoundError("Packaged scenario map images are missing.")
        if not paths.reference_sheets_root.is_dir():
            raise FileNotFoundError("Packaged master reference sheets are missing.")
        if not any(paths.reference_sheets_root.rglob("*.pdf")):
            raise FileNotFoundError("Packaged master reference sheet PDFs are missing.")

        connection = sqlite3.connect(
            f"file:{database_path.as_posix()}?mode=ro",
            uri=True,
        )
        try:
            result = connection.execute("PRAGMA integrity_check").fetchone()
        finally:
            connection.close()
        if result is None or result[0] != "ok":
            raise OSError("Packaged DFS database failed its integrity check.")
    except (DatabaseNotFoundError, OSError, sqlite3.Error) as exc:
        if sys.stderr is not None:
            print(f"DFS release smoke test failed: {exc}", file=sys.stderr)
        return 1
    return 0


def _make_splash(system_name: str) -> QSplashScreen:
    pixmap = QPixmap(620, 330)
    pixmap.fill(Qt.GlobalColor.white)
    splash = QSplashScreen(pixmap)
    label = QLabel(
        "<div style='text-align:center'>"
        "<div style='font-size:30px;font-weight:700'>Dee's Fighting Ships</div>"
        "<div style='font-size:17px;color:#475569'>Tactical Reference System</div>"
        f"<div style='font-size:14px;color:#64748b;margin-top:14px'>{system_name}</div>"
        f"<div style='font-size:11px;color:#94a3b8;margin-top:12px'>Version {APP_VERSION}</div>"
        "</div>", splash,
    )
    label.setGeometry(40, 42, 540, 190)
    label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    return splash


def main() -> int:
    if "--release-smoke-test" in sys.argv:
        return _run_release_smoke_test()

    app = QApplication(sys.argv)
    app.setApplicationName("Dee's Fighting Ships")
    app.setApplicationVersion(APP_VERSION)
    app.setOrganizationName("DFS")

    settings = SettingsService()
    selected_system = settings.default_game_system
    system_names = {
        "b5_acta_2e": "Babylon 5: A Call to Arms",
        "victory_at_sea": "Victory at Sea",
    }
    splash = _make_splash(system_names.get(selected_system, ""))
    splash_started = time.monotonic()
    if settings.show_splash:
        splash.show()
        splash.showMessage(
            "Loading platform database…",
            Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignHCenter,
            Qt.GlobalColor.darkGray,
        )
        app.processEvents()

    try:
        database_path = find_database_path()
        context = build_application_context(database_path, settings)
        context.theme.apply(app)
        context.logging.get_logger("startup").info("Starting DFS %s", APP_VERSION)
    except (DatabaseNotFoundError, OSError) as exc:
        splash.close()
        QMessageBox.critical(None, "DFS database not found", str(exc))
        return 1

    window = MainWindow(context, f"Database: {database_path.name}")

    if not settings.show_splash:
        window.show()
        return app.exec()

    splash.showMessage(
        "Platform database ready  •  Loading application framework…",
        Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignHCenter,
        Qt.GlobalColor.darkGray,
    )
    QTimer.singleShot(1200, lambda: splash.showMessage(
        "Application framework ready  •  Loading workspace…",
        Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignHCenter,
        Qt.GlobalColor.darkGray,
    ))
    QTimer.singleShot(2200, lambda: splash.showMessage(
        "Ready",
        Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignHCenter,
        Qt.GlobalColor.darkGray,
    ))

    elapsed_ms = int((time.monotonic() - splash_started) * 1000)
    remaining_ms = max(0, settings.splash_duration_ms - elapsed_ms)

    def reveal_window() -> None:
        window.show()
        splash.finish(window)

    QTimer.singleShot(remaining_ms, reveal_window)
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
