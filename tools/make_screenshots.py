"""Capture real M0b desktop states offscreen; never inject fake results. Units: logical px."""

from __future__ import annotations

import argparse
import json
import multiprocessing
import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def main() -> int:
    """Render both themes/sizes with widget.grab and actual solver runs. Units: logical px."""
    parser = argparse.ArgumentParser(description="Render the M0b diagnostic, not future M13 pages")
    parser.add_argument("--output", type=Path, default=Path("docs/screenshots/m0b"))
    parser.add_argument("--scale", choices=("1", "1.25", "1.5"), default="1")
    parser.add_argument("--sizes", default="1366x768,1920x1080")
    parser.add_argument("--checked-only", action="store_true")
    args = parser.parse_args()
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    os.environ["QT_SCALE_FACTOR"] = args.scale

    # Lazy imports keep spawned solver children free of GUI imports.
    from PySide6.QtCore import QEventLoop, QSettings, QTimer
    from PySide6.QtWidgets import QApplication

    from struct_ai.gui.app import configure_application
    from struct_ai.gui.spike_window import SpikeWindow

    app = QApplication([])
    configure_application(app)
    args.output.mkdir(parents=True, exist_ok=True)
    manifest = []
    with tempfile.TemporaryDirectory(prefix="struct-ai-screenshots-") as temporary:
        for theme in ("light", "dark"):
            for dimensions in args.sizes.split(","):
                width, height = map(int, dimensions.split("x"))
                settings = QSettings(
                    str(Path(temporary) / "preferences.ini"), QSettings.Format.IniFormat
                )
                window = SpikeWindow(settings=settings, theme=theme)
                window.resize(width, height)
                window.show()
                app.processEvents()
                states = ["checked"] if args.checked_only else ["idle", "checked"]
                for state in states:
                    if state == "checked":
                        window.start_diagnostic()
                        loop = QEventLoop()
                        window.worker.finished.connect(loop.quit)
                        timeout = QTimer()
                        timeout.setSingleShot(True)
                        timeout.timeout.connect(loop.quit)
                        timeout.start(20_000)
                        loop.exec()
                        timeout.stop()
                        if window.current_run is None:
                            raise RuntimeError(
                                "No successful screenshot result: " + window.status_text.text()
                            )
                    app.processEvents()
                    for tile in window.kpis:
                        if tile.value.width() < tile.value.fontMetrics().horizontalAdvance(
                            tile.value.text()
                        ):
                            raise RuntimeError(
                                "A key KPI is clipped; do not publish this screenshot"
                            )
                    pixmap = window.grab()
                    name = f"{theme}-{dimensions}-scale-{args.scale}-{state}.png"
                    if not pixmap.save(str(args.output / name)):
                        raise OSError(f"Could not write screenshot {name}")
                    manifest.append(
                        {
                            "file": name,
                            "theme": theme,
                            "state": state,
                            "logical_size": [width, height],
                            "pixel_size": [pixmap.width(), pixmap.height()],
                            "device_pixel_ratio": pixmap.devicePixelRatio(),
                            "result_hash": window.current_run.result_hash
                            if window.current_run
                            else None,
                            "evidence": (
                                "Actual PySide6 widget.grab; checked states run "
                                "the real isolated OpenSees service"
                            ),
                        }
                    )
                window.close()
    (args.output / f"manifest-scale-{args.scale}.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    print(f"Saved {len(manifest)} real desktop captures to {args.output}")
    return 0


if __name__ == "__main__":
    multiprocessing.freeze_support()
    raise SystemExit(main())
