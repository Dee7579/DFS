"""Android/tablet entry point for Dee's Fighting Ships."""

from __future__ import annotations

from pathlib import Path
import sys

from PySide6.QtCore import QCoreApplication, QStandardPaths, QTimer, QUrl
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine

from dfs.app_paths import DatabaseNotFoundError, find_database_path
from dfs.mobile.application import build_mobile_context
from dfs.mobile.bundled_database import materialize_bundled_database
from dfs.mobile.controller import MobileController
from dfs.mobile.session import MobileSession


def main() -> int:
    QCoreApplication.setOrganizationName("DFS Project")
    QCoreApplication.setOrganizationDomain("deesfightingships.local")
    QCoreApplication.setApplicationName("DFS Companion")
    app = QGuiApplication(sys.argv)

    data_root = Path(
        QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppDataLocation)
    )

    try:
        database_path = find_database_path(Path(__file__))
    except DatabaseNotFoundError:
        try:
            database_path = materialize_bundled_database(
                data_root / "Certified Data" / "dfs.db"
            )
        except Exception as exc:
            print(str(exc), file=sys.stderr)
            return 2
    context = build_mobile_context(database_path)
    controller = MobileController(MobileSession(context, data_root))

    engine = QQmlApplicationEngine()
    engine.rootContext().setContextProperty("dfsMobile", controller)
    qml_path = Path(__file__).resolve().parent / "qml" / "Main.qml"
    engine.load(QUrl.fromLocalFile(str(qml_path)))
    if not engine.rootObjects():
        return 3
    if "--mobile-smoke-test" in sys.argv:
        QTimer.singleShot(250, app.quit)
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
