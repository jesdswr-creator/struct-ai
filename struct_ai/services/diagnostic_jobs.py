"""Spawned diagnostic jobs; no Qt dependency or shared solver state. Units: payload-specific."""

from __future__ import annotations

import json
import multiprocessing as mp
import time
import traceback
from dataclasses import dataclass
from multiprocessing.connection import Connection
from typing import Any, Literal

from struct_ai.arms.diagnostic_models import DiagnosticRun
from struct_ai.exceptions import EngineeringError
from struct_ai.serialization import canonical_json


@dataclass(frozen=True)
class DiagnosticEvent:
    """Service-owned event presented verbatim by GUI/CLI clients. Units: payload-specific."""

    kind: Literal["progress", "result", "error", "cancelled"]
    message: str = ""
    run: DiagnosticRun | None = None
    error: dict[str, Any] | None = None
    technical_details: str = ""


def _child_main(payload_json: str, sender: Connection) -> None:
    """Enter the public service inside a fresh process. Units: explicit in form field names."""
    from struct_ai.services import engine_service

    def send(payload: dict[str, Any]) -> None:
        """Use JSON bytes, not unvalidated result objects, across the pipe. Units: unchanged."""
        sender.send_bytes(canonical_json(payload).encode("utf-8"))

    try:
        run = engine_service.run_diagnostic_form(
            json.loads(payload_json),
            progress=lambda stage: send({"kind": "progress", "message": stage}),
        )
        send({"kind": "result", "run": run.model_dump(mode="json")})
    except Exception as error:
        details = (
            error.as_dict()
            if isinstance(error, EngineeringError)
            else {
                "type": type(error).__name__,
                "message": str(error),
                "clause": "DIAGNOSTIC WORKER (software failure, not an IS-code clause)",
                "value": type(error).__name__,
                "limit": "successful validated diagnostic execution",
            }
        )
        send({"kind": "error", "error": details, "technical_details": traceback.format_exc()})
    finally:
        sender.close()


class DiagnosticJob:
    """One isolated child with non-blocking poll/cancel operations. Units: event-specific."""

    def __init__(self, form_fields: dict[str, str]) -> None:
        """Start a spawned process with a copied JSON request. Units: form field suffixes."""
        context = mp.get_context("spawn")
        self._receiver, sender = context.Pipe(duplex=False)
        self._process = context.Process(
            target=_child_main,
            args=(canonical_json(form_fields), sender),
            name="struct_ai diagnostic",
            daemon=True,
        )
        self._terminal = False
        self._closed = False
        self._pipe_eof = False
        self._cancelled_at: float | None = None
        try:
            self._process.start()
        except Exception:
            self._receiver.close()
            raise
        finally:
            sender.close()

    @property
    def finished(self) -> bool:
        """True after the terminal event and child cleanup. Units: none."""
        return self._closed

    def cancel(self) -> None:
        """Request termination without waiting on the GUI thread. Units: none."""
        if self._terminal or self._closed or self._cancelled_at is not None:
            return
        self._cancelled_at = time.monotonic()
        if self._process.is_alive():
            self._process.terminate()

    def _finish(self) -> None:
        """Reap an already-exited process and close descriptors. Units: none."""
        self._process.join(timeout=0)
        self._process.close()
        self._receiver.close()
        self._closed = True

    def poll(self) -> list[DiagnosticEvent]:
        """Drain ready events; reject corrupt/missing terminal messages. Units: payload-specific."""
        if self._closed:
            return []
        if self._cancelled_at is not None:
            if self._process.is_alive():
                if time.monotonic() - self._cancelled_at > 1.0:
                    self._process.kill()
                return []
            self._terminal = True
            self._finish()
            return [
                DiagnosticEvent(kind="cancelled", message="Cancelled. No result was published.")
            ]
        # Snapshot liveness BEFORE reading to avoid racing a final send+exit between
        # an empty pipe poll and the liveness check. The next timer tick reaps it.
        child_was_alive = self._process.is_alive()
        events: list[DiagnosticEvent] = []
        try:
            while not self._pipe_eof:
                try:
                    if not self._receiver.poll():
                        break
                    message = self._receiver.recv_bytes(maxlength=1_000_000)
                except EOFError:
                    self._pipe_eof = True
                    break
                except BrokenPipeError as error:
                    # CPython's Windows PeekNamedPipe can report ERROR_BROKEN_PIPE
                    # (109) on normal peer closure, whereas recv_bytes reports EOF.
                    # Only that transport EOF is normalised; other errors still fail.
                    if getattr(error, "winerror", None) != 109:
                        raise
                    self._pipe_eof = True
                    break
                payload = json.loads(message)
                kind = payload["kind"]
                if self._terminal:
                    raise ValueError("Unexpected event after terminal worker message")
                if kind == "progress":
                    events.append(DiagnosticEvent(kind="progress", message=payload["message"]))
                elif kind == "result":
                    run = DiagnosticRun.model_validate_json(canonical_json(payload["run"]))
                    self._terminal = True
                    events.append(DiagnosticEvent(kind="result", run=run))
                elif kind == "error":
                    self._terminal = True
                    events.append(
                        DiagnosticEvent(
                            kind="error",
                            error=payload["error"],
                            technical_details=payload["technical_details"],
                        )
                    )
                else:
                    raise ValueError(f"Unknown worker event: {kind}")
        except Exception as error:
            self._terminal = True
            if self._process.is_alive():
                self._process.terminate()
            events.append(
                DiagnosticEvent(
                    kind="error",
                    error={
                        "type": type(error).__name__,
                        "message": f"Worker communication failed: {error}",
                        "clause": "WORKER MESSAGE INTEGRITY (software constraint)",
                        "value": type(error).__name__,
                        "limit": "valid complete JSON event and result hash",
                    },
                    technical_details=traceback.format_exc(),
                )
            )
        if not child_was_alive:
            if not self._terminal:
                self._terminal = True
                events.append(
                    DiagnosticEvent(
                        kind="error",
                        error={
                            "type": "WorkerExited",
                            "message": "Solver process exited without a result. Nothing published.",
                            "clause": "WORKER LIFECYCLE (software constraint)",
                            "value": self._process.exitcode,
                            "limit": "a verified result or an explicit engineering error",
                        },
                    )
                )
            self._finish()
        return events

    def close(self) -> None:
        """Bounded shutdown for application exit, not the normal UI cancel path. Units: s."""
        if self._closed:
            return
        if self._process.is_alive():
            self._process.terminate()
            self._process.join(timeout=1.0)
        if self._process.is_alive():
            self._process.kill()
            self._process.join(timeout=1.0)
        if self._process.is_alive():
            raise RuntimeError("The diagnostic process could not be terminated")
        self._finish()
