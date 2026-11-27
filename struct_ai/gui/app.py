"""Lightweight PySide6 desktop bootstrap; no engineering computation. Units: logical px."""

from __future__ import annotations

import sys

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QFontDatabase, QGuiApplication, QIcon
from PySide6.QtWidgets import QApplication

from struct_ai.resources import resource_path

_FONT_REGISTERED = False


def configure_application(app: QApplication) -> None:
    """Load bundled Inter with Segoe UI fallback; Qt6 provides high-DPI support. Units: px."""
    global _FONT_REGISTERED
    app.setApplicationName("struct_ai")
    app.setOrganizationName("struct_ai")
    app.setOrganizationDomain("struct-ai.local")
    app.setStyle("Fusion")
    if not _FONT_REGISTERED:
        font_id = QFontDatabase.addApplicationFont(
            str(resource_path("gui/resources/fonts/Inter-Variable.ttf"))
        )
        if font_id < 0:
            raise RuntimeError("Bundled Inter font could not be loaded; resource selftest failed")
        _FONT_REGISTERED = True
    font = QFont()
    font.setFamilies(["Inter", "Segoe UI", "sans-serif"])
    font.setPixelSize(14)
    app.setFont(font)
    app.setWindowIcon(QIcon(str(resource_path("gui/resources/app-icon.svg"))))


def main() -> int:
    """Start the diagnostic-only desktop app. Units: engine-supplied outputs."""
    from struct_ai.gui.spike_window import SpikeWindow
    from struct_ai.services import engine_service

    QGuiApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    app = QApplication(sys.argv)
    configure_application(app)
    engine_service.initialise_logging()
    window = SpikeWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
