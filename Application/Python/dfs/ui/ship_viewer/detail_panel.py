"""Platform detail presentation with profile, PDF preview, and printing."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QSettings, QSize, Qt, QUrl, Signal
from PySide6.QtGui import QDesktopServices, QPainter
from PySide6.QtPrintSupport import QPrintDialog, QPrinter
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QFormLayout,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QListWidget,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

try:
    from PySide6.QtPdf import QPdfDocument
    from PySide6.QtPdfWidgets import QPdfView
except ImportError:  # pragma: no cover - depends on PySide6 build
    QPdfDocument = None
    QPdfView = None

from dfs.domain.catalog import PlatformDetail, PlatformProfile
from dfs.services.document_service import DocumentReference, DocumentService


class _StatCard(QFrame):
    def __init__(self, caption: str) -> None:
        super().__init__()
        self.setObjectName("statCard")
        self.caption = QLabel(caption.upper())
        self.caption.setObjectName("statCardCaption")
        self.value = QLabel("—")
        self.value.setObjectName("statCardValue")
        self.value.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(2)
        layout.addWidget(self.caption)
        layout.addWidget(self.value)


class PlatformDetailPanel(QWidget):
    profile_changed = Signal(int)

    def __init__(self, documents: DocumentService) -> None:
        super().__init__()
        self._documents = documents
        self._platform: PlatformDetail | None = None
        self._document_ref: DocumentReference | None = None
        self._settings = QSettings()

        self.title = QLabel("Select a platform")
        self.title.setObjectName("platformTitle")
        self.title.setWordWrap(True)
        self.subtitle = QLabel("")
        self.subtitle.setObjectName("platformSubtitle")
        self.subtitle.setWordWrap(True)

        self.profile_combo = QComboBox()
        self.profile_combo.currentIndexChanged.connect(self._show_selected_profile)

        self.tabs = QTabWidget()
        self.overview_tab = QWidget()
        self.weapons_tab = QWidget()
        self.notes_tab = QWidget()
        self.pdf_tab = QWidget()
        self.tabs.addTab(self.overview_tab, "Profile")
        self.tabs.addTab(self.weapons_tab, "Weapons")
        self.tabs.addTab(self.notes_tab, "Notes")
        self.tabs.addTab(self.pdf_tab, "PDF")

        self._build_overview()
        self._build_weapons()
        self._build_notes()
        self._build_pdf()

        layout = QVBoxLayout(self)
        layout.addWidget(self.title)
        layout.addWidget(self.subtitle)
        layout.addWidget(self.profile_combo)
        layout.addWidget(self.tabs, 1)

    def _build_overview(self) -> None:
        overview_layout = QVBoxLayout(self.overview_tab)
        cards = QGridLayout()
        cards.setSpacing(8)
        self.stat_cards: dict[str, _StatCard] = {}
        for index, (key, caption) in enumerate((
            ("priority", "Priority"), ("initiative", "Initiative"),
            ("speed", "Speed"), ("turn", "Turn"), ("hull", "Hull"),
            ("damage", "Damage"), ("crew", "Crew"), ("troops", "Troops"),
        )):
            card = _StatCard(caption)
            self.stat_cards[key] = card
            cards.addWidget(card, index // 4, index % 4)
        overview_layout.addLayout(cards)

        details_frame = QFrame()
        details_frame.setObjectName("profileDetails")
        self.details = QFormLayout(details_frame)
        self.detail_labels: dict[str, QLabel] = {}
        for key, caption in (("fleet", "Fleet / Era"), ("craft", "Craft"),
                             ("service", "In Service"), ("source", "Source"),
                             ("traits", "Traits")):
            label = QLabel("—")
            label.setWordWrap(True)
            label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            self.detail_labels[key] = label
            self.details.addRow(caption, label)
        overview_layout.addWidget(details_frame)
        overview_layout.addStretch(1)

    def _build_weapons(self) -> None:
        layout = QVBoxLayout(self.weapons_tab)
        self.weapons_table = QTableWidget(0, 5)
        self.weapons_table.setHorizontalHeaderLabels(("Weapon", "Range", "Arc", "AD", "Traits"))
        self.weapons_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.weapons_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.weapons_table.setAlternatingRowColors(True)
        self.weapons_table.verticalHeader().setVisible(False)
        self.weapons_table.verticalHeader().setDefaultSectionSize(29)
        header = self.weapons_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        for column in (1, 2, 3):
            header.setSectionResizeMode(column, QHeaderView.ResizeMode.ResizeToContents)
        layout.addWidget(self.weapons_table)

    def _build_notes(self) -> None:
        layout = QVBoxLayout(self.notes_tab)
        self.notes_list = QListWidget()
        self.notes_list.setWordWrap(True)
        layout.addWidget(self.notes_list)

    def _build_pdf(self) -> None:
        layout = QVBoxLayout(self.pdf_tab)
        controls = QHBoxLayout()
        self.style_combo = QComboBox()
        for style in self._documents.list_styles():
            self.style_combo.addItem(style.label, style.style_id)
        remembered = self._settings.value("ship_viewer/pdf_style", "dfs_standard")
        index = self.style_combo.findData(remembered)
        if index >= 0:
            self.style_combo.setCurrentIndex(index)
        self.refresh_pdf_button = QPushButton("Refresh")
        self.zoom_out_button = QPushButton("−")
        self.zoom_out_button.setToolTip("Zoom out")
        self.zoom_in_button = QPushButton("+")
        self.zoom_in_button.setToolTip("Zoom in")
        self.fit_width_button = QPushButton("Fit Width")
        self.fit_page_button = QPushButton("Fit Page")
        self.open_pdf_button = QPushButton("Open Externally")
        self.print_pdf_button = QPushButton("Print Sheet")
        controls.addWidget(QLabel("Sheet Style"))
        controls.addWidget(self.style_combo)
        controls.addWidget(self.refresh_pdf_button)
        controls.addStretch(1)
        controls.addWidget(self.zoom_out_button)
        controls.addWidget(self.zoom_in_button)
        controls.addWidget(self.fit_width_button)
        controls.addWidget(self.fit_page_button)
        controls.addWidget(self.open_pdf_button)
        controls.addWidget(self.print_pdf_button)
        layout.addLayout(controls)

        self.pdf_status = QLabel("Select a platform profile to locate its generated sheet.")
        self.pdf_status.setWordWrap(True)
        layout.addWidget(self.pdf_status)

        if QPdfDocument is not None and QPdfView is not None:
            self.pdf_document = QPdfDocument(self)
            self.pdf_view = QPdfView()
            self.pdf_view.setDocument(self.pdf_document)
            self.pdf_view.setPageMode(QPdfView.PageMode.MultiPage)
            layout.addWidget(self.pdf_view, 1)
        else:
            self.pdf_document = None
            self.pdf_view = None
            unavailable = QLabel(
                "Embedded PDF support is unavailable in this PySide6 installation. "
                "Open Externally and Print Sheet remain available."
            )
            unavailable.setWordWrap(True)
            layout.addWidget(unavailable, 1)

        self.style_combo.currentIndexChanged.connect(self._style_changed)
        self.refresh_pdf_button.clicked.connect(self._refresh_pdf)
        self.zoom_out_button.clicked.connect(lambda: self._zoom(0.8))
        self.zoom_in_button.clicked.connect(lambda: self._zoom(1.25))
        self.fit_width_button.clicked.connect(self._fit_width)
        self.fit_page_button.clicked.connect(self._fit_page)
        self.open_pdf_button.clicked.connect(self._open_external)
        self.print_pdf_button.clicked.connect(self._print_sheet)
        self._set_pdf_buttons(False)

    def _set_pdf_buttons(self, enabled: bool) -> None:
        self.open_pdf_button.setEnabled(enabled)
        self.print_pdf_button.setEnabled(enabled)
        self.zoom_out_button.setEnabled(enabled and self.pdf_view is not None)
        self.zoom_in_button.setEnabled(enabled and self.pdf_view is not None)
        self.fit_width_button.setEnabled(enabled and self.pdf_view is not None)
        self.fit_page_button.setEnabled(enabled and self.pdf_view is not None)

    def clear(self) -> None:
        self._platform = None
        self._document_ref = None
        self.title.setText("Select a platform")
        self.subtitle.clear()
        self.profile_combo.clear()
        for card in self.stat_cards.values():
            card.value.setText("—")
        for label in self.detail_labels.values():
            label.setText("—")
        self.weapons_table.setRowCount(0)
        self.notes_list.clear()
        self.pdf_status.setText("Select a platform profile to locate its generated sheet.")
        if self.pdf_document is not None:
            self.pdf_document.close()
        self._set_pdf_buttons(False)

    def set_platform(self, platform: PlatformDetail) -> None:
        self._platform = platform
        self.title.setText(platform.name)
        self.subtitle.setText(f"{platform.ship_class}  •  {platform.faction_name}")
        self.profile_combo.blockSignals(True)
        self.profile_combo.clear()
        for profile in platform.profiles:
            self.profile_combo.addItem(f"{profile.fleet_name} — {profile.priority_level}", profile.profile_id)
        self.profile_combo.blockSignals(False)
        if platform.profiles:
            self.profile_combo.setCurrentIndex(0)
            self._display_profile(platform.profiles[0])
        else:
            self.clear()

    def _selected_profile(self) -> PlatformProfile | None:
        if self._platform is None:
            return None
        index = self.profile_combo.currentIndex()
        if 0 <= index < len(self._platform.profiles):
            return self._platform.profiles[index]
        return None

    def _show_selected_profile(self, index: int) -> None:
        if self._platform is None or not (0 <= index < len(self._platform.profiles)):
            return
        profile = self._platform.profiles[index]
        self._display_profile(profile)
        self.profile_changed.emit(profile.profile_id)

    def _display_profile(self, profile: PlatformProfile) -> None:
        values = {"priority": profile.priority_level, "initiative": profile.initiative,
                  "speed": profile.speed, "turn": profile.turn, "hull": profile.hull,
                  "damage": profile.damage, "crew": profile.crew, "troops": profile.troops}
        for key, card in self.stat_cards.items():
            card.value.setText(values.get(key) or "—")

        detail_values = {"fleet": profile.fleet_name, "craft": profile.craft,
                         "service": profile.in_service, "source": profile.source_book,
                         "traits": ", ".join(profile.traits) if profile.traits else "—"}
        for key, label in self.detail_labels.items():
            label.setText(detail_values.get(key) or "—")

        self.weapons_table.setRowCount(len(profile.weapons))
        for row_index, weapon in enumerate(profile.weapons):
            for column, value in enumerate((weapon.name, weapon.range_value, weapon.arc,
                                            weapon.attack_dice, weapon.traits)):
                item = QTableWidgetItem(value)
                if column in (1, 2, 3):
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.weapons_table.setItem(row_index, column, item)

        self.notes_list.clear()
        self.notes_list.addItems(profile.notes or ("No platform-specific notes.",))
        self._refresh_pdf()

    def _style_changed(self) -> None:
        self._settings.setValue("ship_viewer/pdf_style", self.style_combo.currentData())
        self._refresh_pdf()

    def _refresh_pdf(self) -> None:
        profile = self._selected_profile()
        if self._platform is None or profile is None:
            return
        self._documents.refresh()
        style_id = str(self.style_combo.currentData() or "dfs_standard")
        self._document_ref = self._documents.find_sheet(
            style_id=style_id,
            file_name=self._platform.file_name,
            platform_name=self._platform.name,
            faction_name=self._platform.faction_name,
            fleet_name=profile.fleet_name,
        )
        if self._document_ref is None:
            self.pdf_status.setText(
                "No generated sheet was found for this profile and style. "
                "Generate the PDFs, then press Refresh."
            )
            if self.pdf_document is not None:
                self.pdf_document.close()
            self._set_pdf_buttons(False)
            return

        self.pdf_status.setText(str(self._document_ref.path))
        if self.pdf_document is not None:
            self.pdf_document.close()
            self.pdf_document.load(str(self._document_ref.path))
            self._fit_width()
        self._set_pdf_buttons(True)

    def _zoom(self, multiplier: float) -> None:
        if self.pdf_view is not None:
            self.pdf_view.setZoomMode(QPdfView.ZoomMode.Custom)
            self.pdf_view.setZoomFactor(max(0.1, min(8.0, self.pdf_view.zoomFactor() * multiplier)))

    def _fit_width(self) -> None:
        if self.pdf_view is not None:
            self.pdf_view.setZoomMode(QPdfView.ZoomMode.FitToWidth)

    def _fit_page(self) -> None:
        if self.pdf_view is not None:
            self.pdf_view.setZoomMode(QPdfView.ZoomMode.FitInView)

    def _open_external(self) -> None:
        if self._document_ref is not None:
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(self._document_ref.path)))

    def _print_sheet(self) -> None:
        if self._document_ref is None or QPdfDocument is None:
            QMessageBox.information(self, "Print Sheet", "No printable PDF is loaded.")
            return
        document = QPdfDocument(self)
        if document.load(str(self._document_ref.path)) != QPdfDocument.Error.None_:
            QMessageBox.warning(self, "Print Sheet", "The selected PDF could not be loaded.")
            return
        printer = QPrinter(QPrinter.PrinterMode.HighResolution)
        dialog = QPrintDialog(printer, self)
        dialog.setWindowTitle(f"Print {self._platform.name if self._platform else 'DFS Sheet'}")
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        painter = QPainter(printer)
        try:
            page_rect = printer.pageRect(QPrinter.Unit.DevicePixel)
            target_size = QSize(int(page_rect.width()), int(page_rect.height()))
            for page in range(document.pageCount()):
                if page > 0:
                    printer.newPage()
                image = document.render(page, target_size)
                scaled = image.size().scaled(target_size, Qt.AspectRatioMode.KeepAspectRatio)
                x = page_rect.x() + (page_rect.width() - scaled.width()) // 2
                y = page_rect.y() + (page_rect.height() - scaled.height()) // 2
                painter.drawImage(x, y, image.scaled(scaled, Qt.AspectRatioMode.KeepAspectRatio,
                                                     Qt.TransformationMode.SmoothTransformation))
        finally:
            painter.end()
            document.close()
