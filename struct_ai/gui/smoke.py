"""A real GUI+worker frozen smoke test, not a mocked UI. Units: engine-supplied."""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

from PySide6.QtCore import QSettings, QTimer
from PySide6.QtWidgets import QApplication

from struct_ai.gui.app import configure_application
from struct_ai.gui.spike_window import SpikeWindow
from struct_ai.services import engine_service


def run_gui_selftest(output: Path) -> int:
    """Show the real window, run its isolated service job, and save evidence. Units: payload."""
    app = QApplication([])
    configure_application(app)
    with tempfile.TemporaryDirectory(prefix="struct_ai-gui-selftest-") as temporary:
        settings = QSettings(str(Path(temporary) / "preferences.ini"), QSettings.Format.IniFormat)
        window = SpikeWindow(settings=settings, theme="light")
        window.show()
        state = {"timed_out": False}
        timeout = QTimer()
        timeout.setSingleShot(True)

        def on_timeout() -> None:
            """Abort rather than reporting a stalled GUI as successful. Units: none."""
            state["timed_out"] = True
            app.exit(2)

        def begin() -> None:
            """Exercise the actual UI action and service-owned worker. Units: field suffixes."""
            window.start_diagnostic()
            if window.worker is not None and window.worker.running:
                window.worker.finished.connect(app.quit)
            else:
                app.exit(2)

        timeout.timeout.connect(on_timeout)
        timeout.start(30_000)
        QTimer.singleShot(0, begin)
        app.exec()
        timeout.stop()
        passed = window.current_run is not None and not state["timed_out"]
        if passed:
            run = window.current_run
            evidence = {
                "kind": "M0B_GUI_SELFTEST",
                "status": "PASS",
                "frozen": bool(getattr(sys, "frozen", False)),
                "qt_platform": app.platformName(),
                "result_hash": run.result_hash,
                "table_rows": window.checks_model.rowCount(),
                "checks": [check.model_dump(mode="json") for check in run.result.checks],
                "building_design_available": False,
                "note": "Real GUI and spawned OpenSees worker; NOT clean-VM certification",
            }
        else:
            evidence = {
                "kind": "M0B_GUI_SELFTEST",
                "status": "FAIL",
                "frozen": bool(getattr(sys, "frozen", False)),
                "timed_out": state["timed_out"],
                "message": window.status_text.text(),
            }
        engine_service.write_diagnostic_evidence(output, evidence)
        window.close()
        return 0 if passed else 2
