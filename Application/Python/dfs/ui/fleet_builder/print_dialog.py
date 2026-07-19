"""Selective fleet printing with named fleet-sheet generation and real page sizes."""
from __future__ import annotations

from datetime import datetime
from pathlib import Path

from PySide6.QtCore import QMarginsF, Qt, QSize
from PySide6.QtGui import QPageLayout, QPageSize, QPainter
from PySide6.QtPrintSupport import QPrintDialog, QPrinter
from PySide6.QtWidgets import (
    QAbstractItemView, QCheckBox, QComboBox, QDialog, QHBoxLayout, QHeaderView,
    QLabel, QMessageBox, QPushButton, QSpinBox, QTableWidget, QTableWidgetItem,
    QVBoxLayout,
)

try:
    from PySide6.QtPdf import QPdfDocument
except ImportError:  # pragma: no cover
    QPdfDocument = None

from dfs.services.fleet.print_planner import FleetPrintItem
from dfs.services.fleet.print_composer import PreparedFleetDocument


class FleetPrintDialog(QDialog):
    """Choose, generate, and print fleet sheets without touching master PDFs."""

    def __init__(self, context, fleet, fleet_path: Path | None = None, parent=None) -> None:
        super().__init__(parent)
        self._context = context
        self._fleet = fleet
        self._fleet_path = Path(fleet_path) if fleet_path else None
        self._items = context.fleet_prints.plan(fleet)
        self.printed_item_keys: tuple[str, ...] = ()
        self.setWindowTitle(f"Print Fleet - {fleet.name}")
        self.resize(1050, 700)

        layout = QVBoxLayout(self)
        title = QLabel("Select Fleet Sheets")
        title.setObjectName("platformTitle")
        layout.addWidget(title)
        intro = QLabel(
            "Choose the fleet roster, individual ship sheets, and unique fighter/craft references to include. "
            "Named ship sheets are generated as fleet-specific copies; master reference PDFs are never overwritten."
        )
        intro.setWordWrap(True)
        layout.addWidget(intro)
        duplex_note = QLabel(
            "PRINTING: Use US Letter paper, duplex printing, and Flip on long edge. "
            "DFS preserves each ship sheet at its intended size; taller sheets print alone instead of being shrunk. "
            "Fighter references are imposed four-up with mirrored backs for cutting."
        )
        duplex_note.setWordWrap(True)
        duplex_note.setObjectName("secondaryText")
        layout.addWidget(duplex_note)

        controls = QHBoxLayout()
        controls.addWidget(QLabel("Sheet style"))
        self.style_combo = QComboBox()
        for style in context.documents.list_styles():
            self.style_combo.addItem(style.label, style.style_id)
        controls.addWidget(self.style_combo)
        controls.addStretch(1)
        self.select_all_button = QPushButton("Select All")
        self.select_none_button = QPushButton("Select None")
        self.select_unprinted_button = QPushButton("Select Unprinted")
        controls.addWidget(self.select_all_button)
        controls.addWidget(self.select_none_button)
        controls.addWidget(self.select_unprinted_button)
        layout.addLayout(controls)

        self.table = QTableWidget(len(self._items), 6)
        self.table.setHorizontalHeaderLabels(("Print", "Type", "Platform", "Ship Name / Use", "In Fleet", "Copies"))
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        layout.addWidget(self.table, 1)

        for row, item in enumerate(self._items):
            check = QCheckBox()
            check.setChecked(not item.already_printed)
            check.setProperty("item_key", item.item_key)
            self.table.setCellWidget(row, 0, check)
            kind_label = {"roster": "Fleet roster", "ship": "Ship", "craft": "Craft reference"}.get(item.kind, item.kind.title())
            self.table.setItem(row, 1, QTableWidgetItem(kind_label))
            self.table.setItem(row, 2, QTableWidgetItem(item.platform_name))
            if item.kind == "roster":
                use = "Fleet summary, roster, included craft, and validation"
            elif item.vessel_name:
                use = item.vessel_name
            else:
                use = "Unique fleet reference" if item.kind == "craft" else "Unnamed vessel"
            if item.already_printed:
                use += "  -  previously printed"
            self.table.setItem(row, 3, QTableWidgetItem(use))
            if item.kind == "craft":
                represented = f"{item.quantity_represented} flights"
            elif item.kind == "roster":
                represented = f"{item.quantity_represented} entries"
            else:
                represented = str(item.quantity_represented)
            self.table.setItem(row, 4, QTableWidgetItem(represented))
            copies = QSpinBox()
            copies.setRange(1, 99)
            copies.setValue(item.copies)
            copies.setEnabled(item.kind == "ship")
            self.table.setCellWidget(row, 5, copies)

        footer = QHBoxLayout()
        footer.addStretch(1)
        cancel = QPushButton("Cancel")
        self.print_button = QPushButton("Generate Letter Packet and Print...")
        footer.addWidget(cancel)
        footer.addWidget(self.print_button)
        layout.addLayout(footer)

        cancel.clicked.connect(self.reject)
        self.print_button.clicked.connect(self._print_selected)
        self.select_all_button.clicked.connect(lambda: self._set_all(True))
        self.select_none_button.clicked.connect(lambda: self._set_all(False))
        self.select_unprinted_button.clicked.connect(self._select_unprinted)

    def _checkbox(self, row: int) -> QCheckBox:
        return self.table.cellWidget(row, 0)

    def _set_all(self, checked: bool) -> None:
        for row in range(self.table.rowCount()):
            self._checkbox(row).setChecked(checked)

    def _select_unprinted(self) -> None:
        for row, item in enumerate(self._items):
            self._checkbox(row).setChecked(not item.already_printed)

    def _selected(self):
        return [
            (item, self.table.cellWidget(row, 5).value())
            for row, item in enumerate(self._items)
            if self._checkbox(row).isChecked()
        ]

    def _sheet_folder(self) -> Path:
        if self._fleet_path:
            base = self._fleet_path.parent / self._fleet_path.name.removesuffix(".dfs-fleet.json")
        else:
            root = self._context.settings.get_str("fleet/default_folder", "").strip()
            base_root = Path(root) if root else self._context.resources.project_root / "fleets"
            safe_name = "".join(ch if ch.isalnum() or ch in "-_ " else "_" for ch in self._fleet.name).strip() or "Untitled Fleet"
            base = base_root / safe_name
        folder = base / "sheets"
        folder.mkdir(parents=True, exist_ok=True)
        return folder

    def _prepare_documents(self, selected):
        style_id = str(self.style_combo.currentData() or "dfs_standard")
        folder = self._sheet_folder()
        printable = []
        missing = []
        for item, copies in selected:
            try:
                if item.kind == "roster":
                    roster_path = folder / "Fleet_Roster.pdf"
                    generated = self._context.fleet_rosters.generate(self._fleet, roster_path)
                    printable.append((item, 1, generated.path))
                else:
                    generated = self._context.fleet_sheets.generate(
                        item, style_id=style_id, output_folder=folder
                    )
                    printable.append((item, copies, generated.path))
            except Exception as exc:
                missing.append(f"{item.display_name}: {exc}")
        return printable, missing

    def _packet_folder(self) -> Path:
        folder = self._sheet_folder().parent / "print_packets"
        folder.mkdir(parents=True, exist_ok=True)
        return folder

    def _packet_path(self) -> Path:
        safe_fleet = "".join(
            ch if ch.isalnum() or ch in "-_ " else "_"
            for ch in self._fleet.name
        ).strip() or "Untitled Fleet"
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return self._packet_folder() / f"{safe_fleet}__print_packet__{timestamp}.pdf"

    def _print_packet(self, packet_path: Path) -> bool:
        document = QPdfDocument(self)
        if document.load(str(packet_path)) != QPdfDocument.Error.None_:
            document.close()
            QMessageBox.warning(self, "Print Fleet", "The Letter print packet could not be opened.")
            return False

        printer = QPrinter(QPrinter.PrinterMode.HighResolution)
        printer.setPageSize(QPageSize(QPageSize.PageSizeId.Letter))
        printer.setPageOrientation(QPageLayout.Orientation.Portrait)
        printer.setPageMargins(QMarginsF(0, 0, 0, 0), QPageLayout.Unit.Point)
        dialog = QPrintDialog(printer, self)
        dialog.setWindowTitle("Print DFS Fleet Packet - Letter")
        if dialog.exec() != QDialog.DialogCode.Accepted:
            document.close()
            return False

        painter = QPainter(printer)
        try:
            for page in range(document.pageCount()):
                if page:
                    printer.newPage()
                page_rect = printer.pageRect(QPrinter.Unit.DevicePixel)
                target = QSize(int(page_rect.width()), int(page_rect.height()))
                image = document.render(page, target)
                painter.drawImage(page_rect, image)
        finally:
            painter.end()
            document.close()
        return True

    def _print_selected(self) -> None:
        selected = self._selected()
        if not selected:
            QMessageBox.information(self, "Print Fleet", "Select at least one sheet to print.")
            return
        if QPdfDocument is None:
            QMessageBox.warning(self, "Print Fleet", "Qt PDF support is unavailable.")
            return

        printable, missing = self._prepare_documents(selected)
        if missing:
            preview = "\n".join(f"- {name}" for name in missing[:12])
            more = "\n..." if len(missing) > 12 else ""
            QMessageBox.warning(
                self,
                "Fleet Sheet Generation",
                "The following sheets could not be prepared:\n\n" + preview + more,
            )
            if not printable:
                return

        prepared = [
            PreparedFleetDocument(item=item, copies=copies, path=path)
            for item, copies, path in printable
        ]
        try:
            packet = self._context.fleet_composer.compose(prepared, self._packet_path())
        except Exception as exc:
            QMessageBox.critical(
                self,
                "Fleet Print Packet",
                f"The Letter print packet could not be generated.\n\n{exc}",
            )
            return

        if not packet.page_count:
            QMessageBox.information(self, "Print Fleet", "No printable pages were generated.")
            return

        if self._print_packet(packet.path):
            self.printed_item_keys = packet.item_keys
            self._context.status.set(f"Fleet print packet created: {packet.path.name}")
            self.accept()
