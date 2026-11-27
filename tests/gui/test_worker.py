import multiprocessing

import pytest
from PySide6.QtCore import Qt, QThread

from struct_ai.gui.workers.diagnostic_worker import DiagnosticWorker
from struct_ai.services import engine_service


def form_fields():
    return {
        name: str(value)
        for name, value in engine_service.diagnostic_example_input().model_dump().items()
    }


def test_real_qthread_runs_service_off_ui_and_delivers_back_on_ui(window, qtbot, qapp):
    worker = DiagnosticWorker(window)
    execution_threads = []
    delivery_threads = []
    results = []
    failures = []
    # Qt emits started from the actual worker thread. No service or solver is replaced.
    worker._thread.started.connect(
        lambda: execution_threads.append(QThread.currentThread()),
        Qt.ConnectionType.DirectConnection,
    )
    worker.succeeded.connect(lambda run: results.append(run))
    worker.succeeded.connect(lambda _: delivery_threads.append(QThread.currentThread()))
    worker.failed.connect(lambda error, _: failures.append(error))
    try:
        worker.start(form_fields())
        assert worker.running
        qtbot.waitUntil(lambda: not worker.running, timeout=20_000)
        assert execution_threads == [worker._thread]
        assert execution_threads[0] != qapp.thread()
        assert delivery_threads == [qapp.thread()]
        assert len(results) == 1
        assert all(check.ok for check in results[0].result.checks)
        assert failures == []
        assert not worker._thread.isRunning()
    finally:
        worker.close()


def test_cancel_discards_a_real_result_already_queued_to_ui(window, qtbot):
    worker = DiagnosticWorker(window)
    results = []
    queued_events = []
    cancellations = []
    failures = []
    worker._thread.event_ready.connect(queued_events.append, Qt.ConnectionType.DirectConnection)
    worker.succeeded.connect(results.append)
    worker.cancelled.connect(cancellations.append)
    worker.failed.connect(lambda error, _: failures.append(error))
    try:
        worker.start(form_fields())
        # Deliberately withhold UI event processing until the *real* solver and thread
        # finish. Cancel then precedes delivery of their already-queued result signal.
        assert worker._thread.wait(20_000)
        assert [event.kind for event in queued_events].count("result") == 1
        assert worker.running
        worker.cancel()
        qtbot.waitUntil(lambda: not worker.running, timeout=5_000)
        assert results == []
        assert len(cancellations) == 1
        assert "No result" in cancellations[0]
        assert failures == []
    finally:
        worker.close()


def test_closing_worker_reaps_service_thread_and_child(window, qtbot):
    original_children = {child.pid for child in multiprocessing.active_children()}
    worker = DiagnosticWorker(window)
    worker.start(form_fields())
    # Let the supervisor spawn its child; Qt run/cancel is still nonblocking.
    qtbot.waitUntil(
        lambda: any(
            child.pid not in original_children for child in multiprocessing.active_children()
        ),
        timeout=10_000,
    )
    worker.close()
    assert not worker.running
    assert not worker._thread.isRunning()
    assert {child.pid for child in multiprocessing.active_children()} <= original_children


def test_worker_is_one_shot_and_refuses_overlapping_start(window):
    worker = DiagnosticWorker(window)
    try:
        worker.start(form_fields())
        with pytest.raises(RuntimeError, match="one-shot"):
            worker.start(form_fields())
    finally:
        worker.close()


def test_repeated_run_action_keeps_one_active_qthread(window, qtbot):
    window.start_diagnostic()
    first_worker = window.worker
    window.start_diagnostic()
    assert window.worker is first_worker
    qtbot.waitUntil(lambda: not first_worker.running, timeout=20_000)
    assert window.current_run is not None
    window.start_diagnostic()
    assert window.worker is not first_worker
    qtbot.waitUntil(lambda: not window.worker.running, timeout=20_000)
    assert window.current_run is not None
