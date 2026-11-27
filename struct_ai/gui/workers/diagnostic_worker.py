"""Qt-thread adapter for service-owned isolated solver jobs. Units: event payloads."""

from __future__ import annotations

import logging
import traceback
from typing import Any

from PySide6.QtCore import QObject, QThread, Signal, Slot

from struct_ai.services import engine_service


class _ServiceThread(QThread):
    """Own process startup, polling and cleanup off the GUI thread. Units: payload-specific."""

    event_ready = Signal(object)
    infrastructure_failed = Signal(object, str)

    def __init__(self, parent: QObject) -> None:
        """Create a one-shot thread; form text is copied before it starts. Units: none."""
        super().__init__(parent)
        self.setObjectName("struct_ai service supervisor")
        self.fields: dict[str, str] = {}

    def _report_failure(self, error: Exception) -> None:
        """Forward infrastructure failures with their traceback, never hide them. Units: none."""
        logging.getLogger("struct_ai").error("Qt service worker failed", exc_info=True)
        self.infrastructure_failed.emit(
            {
                "type": type(error).__name__,
                "message": str(error),
                "clause": "QT WORKER LIFECYCLE (software constraint, not an IS-code clause)",
                "value": type(error).__name__,
                "limit": "successful service-process startup, communication and cleanup",
            },
            traceback.format_exc(),
        )

    def run(self) -> None:
        """Supervise only service APIs; OpenSees stays in its own process. Units: poll 20 ms."""
        job = None
        try:
            if self.isInterruptionRequested():
                return
            job = engine_service.start_diagnostic_job(self.fields)
            while not job.finished:
                if self.isInterruptionRequested():
                    job.cancel()
                    return  # finally reaps it, even if a terminal message was already sent.
                for event in job.poll():
                    self.event_ready.emit(event)
                if not job.finished:
                    self.msleep(20)
        except Exception as error:
            self._report_failure(error)
        finally:
            if job is not None:
                try:
                    job.close()
                except Exception as error:
                    self._report_failure(error)


class DiagnosticWorker(QObject):
    """Main-thread signal adapter around a QThread supervising the service. Units: payloads."""

    progressed = Signal(str)
    succeeded = Signal(object)
    failed = Signal(object, str)
    cancelled = Signal(str)
    finished = Signal()

    def __init__(self, parent: QObject | None = None) -> None:
        """Wire queued delivery to the UI; no process is owned by this QObject. Units: none."""
        super().__init__(parent)
        self._thread = _ServiceThread(self)
        self._thread.event_ready.connect(self._forward_event)
        self._thread.infrastructure_failed.connect(self._forward_failure)
        self._thread.finished.connect(self._on_thread_finished)
        self._started = False
        self._running = False
        self._closing = False
        self._cancel_requested = False
        self._terminal_delivered = False

    @property
    def running(self) -> bool:
        """Remain busy until queued terminal events and cleanup are delivered. Units: none."""
        return self._running

    def start(self, fields: dict[str, str]) -> None:
        """Copy explicit form text and start the Qt worker without blocking. Units: suffixes."""
        if self._started:
            raise RuntimeError("A diagnostic worker is one-shot; create a new worker for each run")
        self._started = True
        self._thread.fields = dict(fields)
        self._running = True
        try:
            self._thread.start()
        except Exception:
            self._running = False
            raise

    def cancel(self) -> None:
        """Request interruption safely; discard any already-queued late result. Units: none."""
        if not self._running or self._terminal_delivered:
            return
        self._cancel_requested = True
        self._thread.requestInterruption()

    @Slot(object)
    def _forward_event(self, event: Any) -> None:
        """Reject late results after Cancel, including already-queued signals. Units: source."""
        if self._closing:
            return
        if event.kind == "error":
            self._forward_failure(event.error, event.technical_details)
        elif self._terminal_delivered:
            return
        elif event.kind == "cancelled":
            self._terminal_delivered = True
            self.cancelled.emit(event.message)
        elif not self._cancel_requested:
            if event.kind == "progress":
                self.progressed.emit(event.message)
            elif event.kind == "result":
                self._terminal_delivered = True
                self.succeeded.emit(event.run)

    @Slot(object, str)
    def _forward_failure(self, error: dict[str, Any], technical_details: str) -> None:
        """Surface startup/cleanup failures, even during cancellation. Units: source."""
        self._terminal_delivered = True
        self.failed.emit(error, technical_details)

    @Slot()
    def _on_thread_finished(self) -> None:
        """Finish after the owning thread reaps the service process. Units: none."""
        self._running = False
        if self._closing:
            return
        if not self._terminal_delivered:
            if self._cancel_requested:
                self._terminal_delivered = True
                self.cancelled.emit("Cancelled. No result was published.")
            else:
                self._forward_failure(
                    {
                        "type": "WorkerExited",
                        "message": "Qt worker ended without a terminal service event. No result.",
                        "clause": "QT WORKER LIFECYCLE (software constraint)",
                        "value": "missing terminal event",
                        "limit": "a complete verified result, cancellation or explicit error",
                    },
                    "The service supervisor finished without publishing its outcome.",
                )
        self.finished.emit()

    def close(self) -> None:
        """Bound shutdown, never terminate QThread or leave an OpenSees child alive. Units: 5 s."""
        self._closing = True
        self._cancel_requested = True
        self._thread.requestInterruption()
        # Only window shutdown waits. Ordinary Run/Cancel never waits on the GUI thread.
        if not self._thread.wait(5_000):
            self._closing = False
            raise RuntimeError("The Qt service worker did not stop; refusing to destroy it")
        self._running = False
