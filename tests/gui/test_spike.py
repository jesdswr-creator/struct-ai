import ast
from pathlib import Path

from PySide6.QtCore import QSettings, Qt, QTimer
from PySide6.QtWidgets import QAbstractButton, QAbstractItemView, QLineEdit, QScrollArea, QScrollBar

from struct_ai.gui.spike_window import SpikeWindow


def run_actual_diagnostic(window, qtbot):
    qtbot.mouseClick(window.run_button, Qt.MouseButton.LeftButton)
    qtbot.waitUntil(
        lambda: window.current_run is not None and window.run_button.isEnabled(), timeout=20_000
    )


def test_initial_window_has_no_fake_results(window):
    assert window.current_run is None
    assert window.checks_model.rowCount() == 0
    assert all(tile.value.text() == "—" for tile in window.kpis)
    assert not window.building_button.isEnabled()
    assert "Not implemented" in window.building_button.toolTip()
    assert window.result_chip.text() == "NOT RUN"


def test_real_run_populates_only_returned_results_without_freezing(window, qtbot):
    ticks = []
    timer = QTimer(window)
    timer.setInterval(5)
    timer.timeout.connect(lambda: ticks.append(True))
    timer.start()
    run_actual_diagnostic(window, qtbot)
    timer.stop()
    run = window.current_run
    assert window.checks_model.checks == run.result.checks
    assert window.checks_model.rowCount() == 5
    assert window.displacement.value.text() == f"{run.result.observations.tip_displacement_m:.6f}"
    assert window.state_chip.text() == "CHECKED"
    assert ticks, "UI event loop did not tick while the actual solver process ran"
    assert "not structural utilisations" in window.status_text.text()
    assert run.result_hash[:16] in window.provenance_text.text()


def test_engine_error_is_visible_with_context_and_copy(window, qtbot, qapp):
    window.fields["length_m"].setText("0")
    qtbot.mouseClick(window.run_button, Qt.MouseButton.LeftButton)
    qtbot.waitUntil(lambda: window.error_dialog is not None, timeout=20_000)
    dialog = window.error_dialog
    assert dialog.isVisible()
    assert dialog.error["type"] == "InputOutOfRange"
    assert "clause" in dialog.context.toPlainText()
    assert "value" in dialog.context.toPlainText()
    assert "limit" in dialog.context.toPlainText()
    assert window.current_run is None
    assert window.checks_model.rowCount() == 0
    qtbot.mouseClick(dialog.details_toggle, Qt.MouseButton.LeftButton)
    assert dialog.technical_box.isVisible()
    assert "Traceback" in dialog.technical_box.toPlainText()
    qtbot.mouseClick(dialog.copy_button, Qt.MouseButton.LeftButton)
    assert "InputOutOfRange" in qapp.clipboard().text()
    dialog.close()


def test_cancel_real_worker_publishes_no_result(window, qtbot):
    qtbot.mouseClick(window.run_button, Qt.MouseButton.LeftButton)
    qtbot.mouseClick(window.cancel_button, Qt.MouseButton.LeftButton)
    qtbot.waitUntil(
        lambda: window.state_chip.text() == "CANCELLED" and window.run_button.isEnabled(),
        timeout=10_000,
    )
    assert window.current_run is None
    assert window.checks_model.rowCount() == 0
    assert "No result" in window.status_text.text()
    run_actual_diagnostic(window, qtbot)
    assert window.current_run is not None


def test_editing_input_invalidates_all_old_results(window, qtbot):
    run_actual_diagnostic(window, qtbot)
    window.fields["force_kn"].setText("6")
    assert window.current_run is None
    assert all(tile.value.text() == "—" for tile in window.kpis)
    assert window.checks_model.rowCount() == 0
    assert "Run again" in window.status_text.text()


def test_theme_toggle_is_remembered(window, qtbot):
    qtbot.mouseClick(window.theme_button, Qt.MouseButton.LeftButton)
    assert window.theme == "dark"
    assert window.settings.value("appearance/theme") == "dark"
    settings = QSettings(window.settings.fileName(), QSettings.Format.IniFormat)
    reopened = SpikeWindow(settings=settings)
    qtbot.addWidget(reopened)
    assert reopened.theme == "dark"
    assert reopened.current_run is None
    reopened.close()


def test_catalogue_and_copy_diagnostics_are_real_actions(window, qtbot, qapp):
    qtbot.mouseClick(window.catalogue_button, Qt.MouseButton.LeftButton)
    assert window._dialogs[-1].isVisible()
    qtbot.mouseClick(window.copy_diagnostics_button, Qt.MouseButton.LeftButton)
    assert "building design NOT implemented" in qapp.clipboard().text()
    assert "not loaded" in qapp.clipboard().text()
    window._dialogs[-1].close()


def test_interactive_controls_have_accessible_names(window):
    interactive = (QAbstractButton, QAbstractItemView, QLineEdit, QScrollArea, QScrollBar)
    unnamed = [
        type(widget).__name__
        for widget in window.findChildren(object)
        if isinstance(widget, interactive) and not widget.accessibleName()
    ]
    assert unnamed == []


def test_kpi_values_fit_at_minimum_window_size(window, qtbot, qapp):
    window.resize(1100, 700)
    run_actual_diagnostic(window, qtbot)
    qapp.processEvents()
    for tile in window.kpis:
        assert tile.value.width() >= tile.value.fontMetrics().horizontalAdvance(tile.value.text())
        assert tile.value.height() >= tile.value.fontMetrics().height()


def test_gui_has_no_import_of_solver_or_design_modules():
    gui = Path(__file__).resolve().parents[2] / "struct_ai/gui"
    forbidden = ("openseespy", "struct_ai.arms", "struct_ai.design", "struct_ai.codes")
    for path in gui.rglob("*.py"):
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if isinstance(node, ast.ImportFrom):
                assert not (node.module or "").startswith(forbidden), path
            elif isinstance(node, ast.Import):
                assert all(not name.name.startswith(forbidden) for name in node.names), path
