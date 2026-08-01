"""Android/tablet entry point for Dee's Fighting Ships."""

from __future__ import annotations

from pathlib import Path
import sys
import traceback

from PySide6.QtCore import QCoreApplication, QStandardPaths, QTimer, QUrl
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine


STARTUP_ERROR_QML = b"""
import QtQuick
import QtQuick.Window

Window {
    width: 1100
    height: 700
    visible: true
    color: "#172331"
    title: "DFS Companion - Startup Error"

    Flickable {
        anchors.fill: parent
        anchors.margins: 32
        contentWidth: width
        contentHeight: errorText.implicitHeight
        clip: true

        Text {
            id: errorText
            width: parent.width
            text: "DFS could not finish starting.\n\n" + dfsStartupError
            color: "#ffffff"
            font.pixelSize: 20
            wrapMode: Text.WrapAnywhere
            textFormat: Text.PlainText
        }
    }
}
"""


def _load_companion(engine: QQmlApplicationEngine, data_root: Path):
    """Create the shared DFS services lazily so bootstrap failures stay visible."""

    from PySide6.QtQuickControls2 import QQuickStyle

    from dfs.app_paths import DatabaseNotFoundError, find_database_path
    from dfs.mobile.application import build_mobile_context
    from dfs.mobile.bundled_database import materialize_bundled_database
    from dfs.mobile.controller import MobileController
    from dfs.mobile.session import MobileSession

    QQuickStyle.setStyle("Basic")
    try:
        database_path = find_database_path(Path(__file__))
    except DatabaseNotFoundError:
        database_path = materialize_bundled_database(
            data_root / "Certified Data" / "dfs.db"
        )

    context = build_mobile_context(database_path)
    controller = MobileController(MobileSession(context, data_root))
    engine.rootContext().setContextProperty("dfsMobile", controller)
    qml_path = Path(__file__).resolve().parent / "qml" / "Main.qml"
    qml_warnings: list[str] = []

    def collect_warnings(warnings) -> None:
        qml_warnings.extend(error.toString() for error in warnings)

    engine.warnings.connect(collect_warnings)
    engine.load(QUrl.fromLocalFile(str(qml_path)))
    if not engine.rootObjects():
        detail = "\n".join(qml_warnings) or f"Qt could not load {qml_path}."
        raise RuntimeError(detail)
    return controller


def _show_startup_error(
    app: QGuiApplication,
    detail: str,
    *,
    smoke_test: bool,
) -> int:
    """Keep a readable diagnostic on screen instead of returning to the launcher."""

    print(detail, file=sys.stderr)
    engine = QQmlApplicationEngine()
    engine.rootContext().setContextProperty("dfsStartupError", detail[-12000:])
    engine.loadData(STARTUP_ERROR_QML, QUrl("inmemory:/DFSStartupError.qml"))
    if not engine.rootObjects():
        return 2
    if smoke_test:
        QTimer.singleShot(250, app.quit)
    return app.exec()


def main() -> int:
    QCoreApplication.setOrganizationName("DFS Project")
    QCoreApplication.setOrganizationDomain("deesfightingships.local")
    QCoreApplication.setApplicationName("DFS Companion")
    app = QGuiApplication(sys.argv)
    smoke_test = "--mobile-smoke-test" in sys.argv

    data_root = Path(
        QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppDataLocation)
    )

    try:
        engine = QQmlApplicationEngine()
        controller = _load_companion(engine, data_root)
    except Exception:
        return _show_startup_error(
            app,
            traceback.format_exc(),
            smoke_test=smoke_test,
        )
    if smoke_test:
        QTimer.singleShot(250, app.quit)
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
