"""M0b presentation only; no engineering logic or building design. Units: engine-supplied."""

from __future__ import annotations

import logging
import traceback
from typing import Any

from PySide6.QtCore import QSettings, QSortFilterProxyModel, Qt
from PySide6.QtGui import QCloseEvent, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QAbstractButton,
    QAbstractItemView,
    QApplication,
    QDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLineEdit,
    QMainWindow,
    QPlainTextEdit,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QScrollBar,
    QTableView,
    QVBoxLayout,
    QWidget,
)

from struct_ai.gui.models.checks_table import ChecksTableModel
from struct_ai.gui.theme.stylesheet import stylesheet
from struct_ai.gui.theme.tokens import ThemeName
from struct_ai.gui.widgets.error_dialog import ErrorDialog
from struct_ai.gui.widgets.primitives import CantileverSchematic, Card, KpiTile, StatusChip, label
from struct_ai.gui.workers.diagnostic_worker import DiagnosticWorker
from struct_ai.services import engine_service


class SpikeWindow(QMainWindow):
    """Real service-backed diagnostic, NOT the future M13 building UI. Units: source payload."""

    def __init__(
        self, *, settings: QSettings | None = None, theme: ThemeName | None = None
    ) -> None:
        """Create an empty-result desktop workspace with explicit capability limits. Units: px."""
        super().__init__()
        self.setWindowTitle("struct_ai — Solver diagnostic · NOT FOR BUILDING DESIGN")
        self.setMinimumSize(1100, 700)
        self.resize(1366, 768)
        self.setAccessibleName("struct_ai diagnostic workspace")
        self.settings = settings if settings is not None else QSettings()
        self.worker: DiagnosticWorker | None = None
        self.current_run: engine_service.DiagnosticRun | None = None
        self.error_dialog: ErrorDialog | None = None
        self._dialogs: list[QDialog] = []
        self.fields: dict[str, QLineEdit] = {}
        self._build_ui()
        stored_theme = self.settings.value("appearance/theme")
        system_dark = QApplication.styleHints().colorScheme() == Qt.ColorScheme.Dark
        selected = theme or (
            stored_theme
            if stored_theme in ("light", "dark")
            else "dark"
            if system_dark
            else "light"
        )
        self.apply_theme(selected, persist=False)
        self._shortcut = QShortcut(QKeySequence("Ctrl+R"), self)
        self._shortcut.activated.connect(self.start_diagnostic)

    def _build_ui(self) -> None:
        """Compose presentation cards and actions. Units: logical px; input units in labels."""
        root = QWidget()
        root.setObjectName("workspace")
        outer = QVBoxLayout(root)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)
        body = QHBoxLayout()
        body.setSpacing(0)
        sidebar = self._sidebar()
        body.addWidget(sidebar)
        main = QVBoxLayout()
        main.setSpacing(0)
        main.addWidget(self._topbar())
        scroll = QScrollArea()
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setWidgetResizable(True)
        scroll.setAccessibleName("Diagnostic workspace scroll area")
        scroll.verticalScrollBar().setAccessibleName("Diagnostic workspace vertical scroll")
        scroll.horizontalScrollBar().setAccessibleName("Diagnostic workspace horizontal scroll")
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(24, 16, 24, 16)
        layout.setSpacing(8)
        banner = QFrame()
        banner.setObjectName("scopeBanner")
        banner_layout = QHBoxLayout(banner)
        banner_layout.setContentsMargins(16, 10, 16, 10)
        banner_layout.addWidget(label("!   DIAGNOSTIC ONLY", "caption"))
        banner_layout.addWidget(
            label("No building analysis or IS-code design is implemented.", "caption"), 1
        )
        layout.addWidget(banner)
        self.usage_warning = StatusChip("Unverified constants warning", "warning")
        self.usage_warning.setWordWrap(True)
        self.usage_warning.hide()
        layout.addWidget(self.usage_warning)
        top_cards = QHBoxLayout()
        top_cards.setSpacing(16)
        top_cards.addWidget(self._input_card(), 0)
        top_cards.addWidget(self._result_card(), 1)
        layout.addLayout(top_cards)
        layout.addWidget(self._checks_card(), 1)
        scroll.setWidget(content)
        main.addWidget(scroll, 1)
        body.addLayout(main, 1)
        outer.addLayout(body, 1)
        footer = QFrame()
        footer.setObjectName("footer")
        footer_layout = QHBoxLayout(footer)
        footer_layout.setContentsMargins(24, 10, 24, 10)
        footer_layout.addWidget(
            label(
                "DRAFT: must be reviewed and sealed by a licensed structural engineer.", "caption"
            ),
            1,
        )
        footer_layout.addWidget(label("LOCAL DIAGNOSTIC  /  NO LLM LOADED", "caption"))
        outer.addWidget(footer)
        self.setCentralWidget(root)
        for scrollbar in self.table.findChildren(QScrollBar):
            if not scrollbar.accessibleName():
                scrollbar.setAccessibleName("Diagnostic table header scroll")
        for button in self.table.findChildren(QAbstractButton):
            if not button.accessibleName():
                button.setAccessibleName("Select all diagnostic check rows")
        self.setTabOrder(self.run_button, self.theme_button)
        previous = self.theme_button
        for field in self.fields.values():
            self.setTabOrder(previous, field)
            previous = field
        self.setTabOrder(previous, self.table)

    def _sidebar(self) -> QFrame:
        """Present only implemented navigation; building design is visibly disabled. Units: px."""
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(196)
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(16, 24, 16, 24)
        layout.setSpacing(8)
        layout.addWidget(label("struct_ai", "brand"))
        layout.addWidget(label("ENGINEERING, TRACEABLE.", "caption"))
        layout.addSpacing(24)
        layout.addWidget(label("WORKSPACE", "eyebrow"))
        current = QPushButton("Solver diagnostic")
        current.setProperty("nav", True)
        current.setProperty("active", True)
        current.setAccessibleName("Solver diagnostic page")
        current.clicked.connect(lambda: self.run_button.setFocus())
        layout.addWidget(current)
        self.catalogue_button = QPushButton("Code catalogue")
        self.catalogue_button.setProperty("nav", True)
        self.catalogue_button.setAccessibleName("Open unverified code catalogue")
        self.catalogue_button.clicked.connect(self.show_catalogue)
        layout.addWidget(self.catalogue_button)
        self.building_button = QPushButton("Building design")
        self.building_button.setProperty("nav", True)
        self.building_button.setAccessibleName("Building design, not implemented")
        self.building_button.setEnabled(False)
        self.building_button.setToolTip(
            "Not implemented. M1 and later engineering milestones are incomplete."
        )
        layout.addWidget(self.building_button)
        layout.addSpacing(24)
        layout.addWidget(label("M0b", "title"))
        layout.addWidget(label("Packaging spike", "muted"))
        layout.addWidget(
            label(
                "A small, real analysis to test the solver and desktop distribution.",
                "caption",
                wrap=True,
            )
        )
        layout.addStretch()
        layout.addWidget(StatusChip("ASSISTANT OFF", "info"), alignment=Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(
            label("No Ollama integration yet. This diagnostic needs no LLM.", "caption", wrap=True)
        )
        layout.addSpacing(16)
        self.copy_diagnostics_button = QPushButton("Copy diagnostics")
        self.copy_diagnostics_button.setAccessibleName("Copy local engine and package diagnostics")
        self.copy_diagnostics_button.clicked.connect(self.copy_diagnostics)
        layout.addWidget(self.copy_diagnostics_button)
        self.sidebar_note = label(
            f"Engine {engine_service.get_engine_status().version} · internal test",
            "caption",
            wrap=True,
        )
        layout.addWidget(self.sidebar_note)
        return sidebar

    def _topbar(self) -> QFrame:
        """Create run/cancel/theme controls, distinct from production design. Units: px."""
        topbar = QFrame()
        topbar.setObjectName("topbar")
        layout = QHBoxLayout(topbar)
        layout.setContentsMargins(24, 16, 24, 16)
        title = QVBoxLayout()
        title.setSpacing(4)
        title.addWidget(label("WORKSPACE  /  PACKAGING SPIKE", "caption"))
        title.addWidget(label("Solver diagnostic", "title"))
        layout.addLayout(title)
        layout.addStretch()
        self.state_chip = StatusChip("READY", "info")
        layout.addWidget(self.state_chip)
        self.theme_button = QPushButton("Dark theme")
        self.theme_button.setAccessibleName("Toggle light and dark theme")
        self.theme_button.clicked.connect(self.toggle_theme)
        layout.addWidget(self.theme_button)
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.setAccessibleName("Cancel active solver diagnostic")
        self.cancel_button.clicked.connect(self.cancel_diagnostic)
        self.cancel_button.hide()
        layout.addWidget(self.cancel_button)
        self.run_button = QPushButton("Run diagnostic")
        self.run_button.setProperty("primary", True)
        self.run_button.setAccessibleName("Run real two-node OpenSees diagnostic")
        self.run_button.setToolTip(
            "Ctrl+R · Runs OpenSees and independent checks, not building design"
        )
        self.run_button.clicked.connect(self.start_diagnostic)
        layout.addWidget(self.run_button)
        return topbar

    def _input_card(self) -> Card:
        """Render service-supplied synthetic inputs, with no engineering defaults. Units: labels."""
        card = Card()
        card.setFixedWidth(316)
        card.content.addWidget(label("01   Synthetic inputs", "subtitle"))
        card.content.addWidget(label("Software benchmark · not building data", "caption"))
        grid = QGridLayout()
        grid.setHorizontalSpacing(16)
        grid.setVerticalSpacing(8)
        inputs = engine_service.diagnostic_example_input().model_dump()
        definitions = (
            ("length_m", "Length · m", 0, 0, 1),
            ("force_kn", "Signed tip force · kN", 0, 1, 1),
            ("area_m2", "Area · m²", 1, 0, 1),
            ("inertia_m4", "Second moment · m⁴", 1, 1, 1),
            ("elastic_modulus_kn_m2", "Elastic modulus · kN/m²", 2, 0, 2),
        )
        for key, title, row, column, span in definitions:
            cell = QVBoxLayout()
            cell.setSpacing(4)
            field_label = label(title, "caption")
            field = QLineEdit(str(inputs[key]))
            field.setObjectName(key)
            field.setAccessibleName(title)
            field.setToolTip(
                "Explicit synthetic input. Use a decimal point. Validated by the service."
            )
            field_label.setBuddy(field)
            field.textChanged.connect(self.invalidate_result)
            self.fields[key] = field
            cell.addWidget(field_label)
            cell.addWidget(field)
            grid.addLayout(cell, row, column, 1, span)
        card.content.addLayout(grid)
        card.content.addStretch()
        card.content.addWidget(
            label("Fixed base · elastic member · no self-weight", "caption", wrap=True)
        )
        return card

    def _result_card(self) -> Card:
        """Reserve a schematic and KPIs for real returned observations. Units: labels."""
        card = Card()
        header = QHBoxLayout()
        header.addWidget(label("02   Two-node cantilever", "subtitle"), 1)
        header.addWidget(StatusChip("2D · 3 DOF / NODE", "info"))
        card.content.addLayout(header)
        self.schematic = CantileverSchematic()
        card.content.addWidget(self.schematic, 1)
        metrics = QHBoxLayout()
        metrics.setSpacing(16)
        self.displacement = KpiTile("Tip displacement · global X", "m")
        self.reaction = KpiTile("Base reaction · global X", "kN")
        self.moment = KpiTile("Base moment · global Z", "kN·m")
        self.kpis = (self.displacement, self.reaction, self.moment)
        for tile in self.kpis:
            metrics.addWidget(tile, 1)
        card.content.addLayout(metrics)
        return card

    def _checks_card(self) -> Card:
        """Use a model/proxy table of the same CheckResults used by the engine. Units: per row."""
        card = Card()
        header = QHBoxLayout()
        header.addWidget(label("03   Independent verification", "subtitle"), 1)
        self.result_chip = StatusChip("NOT RUN", "info")
        header.addWidget(self.result_chip)
        card.content.addLayout(header)
        self.status_text = label(
            "Run the diagnostic to compare OpenSees with a closed-form solution.",
            "caption",
            wrap=True,
        )
        card.content.addWidget(self.status_text)
        self.progress = QProgressBar()
        self.progress.setAccessibleName("Diagnostic progress")
        self.progress.setRange(0, 0)
        self.progress.setTextVisible(False)
        self.progress.hide()
        card.content.addWidget(self.progress)
        self.checks_model = ChecksTableModel()
        self.proxy = QSortFilterProxyModel(self)
        self.proxy.setSourceModel(self.checks_model)
        self.proxy.setSortRole(Qt.ItemDataRole.UserRole)
        self.table = QTableView()
        self.table.setModel(self.proxy)
        self.table.setAccessibleName("Independent diagnostic checks")
        self.table.horizontalHeader().setAccessibleName("Sortable diagnostic check columns")
        self.table.verticalHeader().setAccessibleName("Diagnostic check row numbers")
        self.table.horizontalScrollBar().setAccessibleName("Checks horizontal scroll")
        self.table.verticalScrollBar().setAccessibleName("Checks vertical scroll")
        self.table.setSortingEnabled(True)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setShowGrid(False)
        self.table.verticalHeader().hide()
        self.table.verticalHeader().setDefaultSectionSize(28)
        self.table.horizontalHeader().setDefaultAlignment(
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
        )
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table.setMinimumHeight(155)
        self.table.sortByColumn(-1, Qt.SortOrder.AscendingOrder)
        card.content.addWidget(self.table, 1)
        self.provenance_text = label(
            "No results yet · No engineering code constants used", "caption", wrap=True
        )
        card.content.addWidget(self.provenance_text)
        return card

    def apply_theme(self, theme: ThemeName, *, persist: bool = True) -> None:
        """Style all presentation elements and optionally remember the user's choice. Units: px."""
        self.theme = theme
        self.setStyleSheet(stylesheet(theme))
        self.theme_button.setText("Light theme" if theme == "dark" else "Dark theme")
        self.schematic.theme = theme
        self.schematic.update()
        self.checks_model.theme = theme
        self.table.viewport().update()
        if persist:
            self.settings.setValue("appearance/theme", theme)
            self.settings.sync()
            if self.settings.status() != QSettings.Status.NoError:
                raise OSError("Theme preference could not be saved")

    def toggle_theme(self) -> None:
        """Switch between the two token palettes. Units: none."""
        self.apply_theme("dark" if self.theme == "light" else "light")

    def invalidate_result(self, *args: object) -> None:
        """Never leave stale results alongside edited inputs. Units: no arithmetic performed."""
        self.current_run = None
        self.usage_warning.hide()
        self.checks_model.set_checks(())
        for tile in self.kpis:
            tile.show_value("—")
        self.result_chip.set_status("NOT RUN", "info")
        self.state_chip.set_status("READY", "info")
        self.status_text.setText("Inputs changed. Run again to produce a new verified diagnostic.")
        self.provenance_text.setText("No current result · No building design is available")

    def _set_running(self, running: bool) -> None:
        """Control UI state only; never choose engine checks. Units: none."""
        self.run_button.setEnabled(not running)
        self.cancel_button.setVisible(running)
        self.progress.setVisible(running)
        for field in self.fields.values():
            field.setEnabled(not running)

    def start_diagnostic(self) -> None:
        """Submit text to the service-owned process without blocking the UI. Units: labels."""
        if self.worker is not None:
            if self.worker.running:
                return
            self.worker.close()
            self.worker.deleteLater()
        self.invalidate_result()
        self._set_running(True)
        self.state_chip.set_status("RUNNING", "info")
        self.status_text.setText("Starting isolated solver process…")
        self.worker = DiagnosticWorker(self)
        self.worker.progressed.connect(self.status_text.setText)
        self.worker.succeeded.connect(self.show_result)
        self.worker.failed.connect(self.show_error)
        self.worker.cancelled.connect(self.show_cancelled)
        self.worker.finished.connect(lambda: self._set_running(False))
        try:
            self.worker.start({key: field.text() for key, field in self.fields.items()})
        except Exception as error:
            self._set_running(False)
            self.show_error(
                {
                    "type": type(error).__name__,
                    "message": str(error),
                    "clause": "WORKER STARTUP (software failure)",
                    "value": type(error).__name__,
                    "limit": "an available spawned service process",
                },
                traceback.format_exc(),
            )

    def cancel_diagnostic(self) -> None:
        """Request service cancellation; no result is manufactured. Units: none."""
        if self.worker is not None:
            self.status_text.setText("Cancelling isolated solver process…")
            self.worker.cancel()

    def show_result(self, run: engine_service.DiagnosticRun) -> None:
        """Render exactly the immutable service payload. Units: m, kN, kN·m as supplied."""
        self.current_run = run
        values = run.result.observations
        self.displacement.show_value(f"{values.tip_displacement_m:.6f}")
        self.reaction.show_value(f"{values.support_fx_kn:.3f}")
        self.moment.show_value(f"{values.support_mz_kn_m:.3f}")
        self.checks_model.set_checks(run.result.checks)
        self.result_chip.set_status("DIAGNOSTIC PASSED", "success")
        self.state_chip.set_status("CHECKED", "success")
        self.status_text.setText(
            "Analytical response and global equilibrium checked. "
            "These are numerical-error ratios, not structural utilisations."
        )
        warning = run.result.code_usage.warning
        if warning is not None:
            self.usage_warning.set_status(warning, "warning")
            self.usage_warning.show()
        self.provenance_text.setText(
            warning
            or (
                f"No code constants used · OpenSees {run.result.solver_version} · "
                f"SHA-256 {run.result_hash[:16]}…"
            )
        )
        self.provenance_text.setToolTip(
            f"Full canonical result hash: {run.result_hash}\n"
            f"Code data: {run.result.code_usage.data_digest}"
        )

    def show_error(self, error: dict[str, Any], technical_details: str) -> None:
        """Preserve complete engine error context and offer a copy action. Units: source error."""
        self.invalidate_result()
        self.state_chip.set_status("ERROR", "danger")
        self.result_chip.set_status("NO RESULT", "danger")
        self.status_text.setText(error["message"])
        logging.getLogger("struct_ai").error("%s\n%s", error, technical_details)
        self.error_dialog = ErrorDialog(error, technical_details, self)
        self.error_dialog.setWindowModality(Qt.WindowModality.WindowModal)
        self.error_dialog.show()

    def show_cancelled(self, message: str) -> None:
        """Show cancellation distinctly from success and failure. Units: none."""
        self.invalidate_result()
        self.state_chip.set_status("CANCELLED", "warning")
        self.status_text.setText(message)

    def show_catalogue(self) -> None:
        """Present the actual service inventory; never imply zero means verified. Units: records."""
        try:
            audit = engine_service.list_code_constants()
            text = (
                "No engineering code constants implemented.\n\n"
                "The four code catalogues are deliberately empty. Building design is unavailable.\n"
                "An empty catalogue is NOT evidence of verified design."
                if not audit.records
                else audit.model_dump_json(indent=2)
            )
            self._show_text("Code catalogue · unverified inventory", text)
        except Exception as error:
            details = (
                error.as_dict()
                if hasattr(error, "as_dict")
                else {
                    "type": type(error).__name__,
                    "message": str(error),
                    "clause": "CODE AUDIT",
                    "value": type(error).__name__,
                    "limit": "valid packaged code catalogues",
                }
            )
            self.show_error(details, traceback.format_exc())

    def _show_text(self, title: str, text: str) -> None:
        """Open an accessible read-only information drawer/dialog. Units: text-specific."""
        dialog = QDialog(self)
        dialog.setWindowTitle(title)
        dialog.setAccessibleName(title)
        dialog.resize(640, 340)
        layout = QVBoxLayout(dialog)
        box = QPlainTextEdit(text)
        box.setReadOnly(True)
        box.setAccessibleName(title)
        layout.addWidget(box)
        close = QPushButton("Close")
        close.setAccessibleName(f"Close {title}")
        close.clicked.connect(dialog.accept)
        layout.addWidget(close)
        self._dialogs.append(dialog)
        dialog.show()

    def copy_diagnostics(self) -> None:
        """Copy operational information only at the user's request. Units: none."""
        QApplication.clipboard().setText(engine_service.get_diagnostics_text())
        self.sidebar_note.setText("Diagnostics copied to clipboard.")

    def closeEvent(self, event: QCloseEvent) -> None:
        """Reap the Qt worker before destruction; expose any shutdown failure. Units: none."""
        try:
            if self.worker is not None:
                self.worker.close()
        except Exception as error:
            event.ignore()
            self.show_error(
                {
                    "type": type(error).__name__,
                    "message": str(error),
                    "clause": "WORKER SHUTDOWN (software failure)",
                    "value": type(error).__name__,
                    "limit": "a stopped Qt worker and no surviving solver child",
                },
                traceback.format_exc(),
            )
            return
        super().closeEvent(event)
