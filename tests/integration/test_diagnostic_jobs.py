import time

import pytest

from struct_ai.serialization import canonical_json
from struct_ai.services import engine_service


def fields():
    return {
        key: str(value)
        for key, value in engine_service.diagnostic_example_input().model_dump().items()
    }


def collect(job):
    deadline = time.monotonic() + 20
    events = []
    try:
        while not job.finished and time.monotonic() < deadline:
            events.extend(job.poll())
            time.sleep(0.005)
        assert job.finished, "The actual spawned diagnostic failed to finish within 20 seconds"
        return events
    finally:
        job.close()


def test_spawned_service_result_matches_direct_service():
    events = collect(engine_service.start_diagnostic_job(fields()))
    results = [event.run for event in events if event.kind == "result"]
    assert len(results) == 1
    assert not [event for event in events if event.kind == "error"]
    direct = engine_service.run_diagnostic(engine_service.diagnostic_example_input())
    assert canonical_json(results[0]) == canonical_json(direct)


def test_actual_validation_error_crosses_the_process_boundary():
    events = collect(engine_service.start_diagnostic_job(fields() | {"length_m": ""}))
    errors = [event for event in events if event.kind == "error"]
    assert len(errors) == 1
    assert errors[0].error["type"] == "InputOutOfRange"
    assert errors[0].error["clause"]
    assert errors[0].error["limit"]
    assert "Traceback" in errors[0].technical_details
    assert not [event for event in events if event.kind == "result"]


def test_cancel_terminates_without_publishing_partial_results_and_next_run_works():
    job = engine_service.start_diagnostic_job(fields())
    job.cancel()
    events = collect(job)
    assert [event.kind for event in events] == ["cancelled"]
    next_events = collect(engine_service.start_diagnostic_job(fields()))
    assert len([event for event in next_events if event.kind == "result"]) == 1


def test_two_jobs_have_isolated_solver_domains():
    first = engine_service.start_diagnostic_job(fields())
    second = engine_service.start_diagnostic_job(fields() | {"force_kn": "-12"})
    first_events, second_events = collect(first), collect(second)
    first_result = next(event.run for event in first_events if event.kind == "result")
    second_result = next(event.run for event in second_events if event.kind == "result")
    # Same independently derived +/-12 kN expectation and 1e-12 relative tolerance
    # as the analytical solver tests; preserve the solver's floating-point roundoff.
    assert first_result.result.observations.support_fx_kn == pytest.approx(-12.0, rel=1e-12)
    assert second_result.result.observations.support_fx_kn == pytest.approx(12.0, rel=1e-12)


def test_repeated_real_child_eof_never_becomes_a_second_terminal_event():
    # Real Windows named pipes report WinError 109 from poll() after peer closure.
    # Real POSIX pipes report EOF through recv_bytes(). Both must yield one result.
    for _ in range(3):
        job = engine_service.start_diagnostic_job(fields())
        events = collect(job)
        terminal = [event for event in events if event.kind != "progress"]
        assert [event.kind for event in terminal] == ["result"]
        assert all(check.ok for check in terminal[0].run.result.checks)
        assert job.poll() == []


def test_actual_process_death_without_terminal_message_remains_an_error():
    job = engine_service.start_diagnostic_job(fields())
    # Kill the actual child before any solver work, without using the cancel API.
    # Transport EOF must not be misinterpreted as successful execution/cancellation.
    job._process.terminate()
    events = collect(job)
    terminal = [event for event in events if event.kind != "progress"]
    assert len(terminal) == 1
    assert terminal[0].kind == "error"
    assert terminal[0].error["type"] == "WorkerExited"
    assert terminal[0].error["value"] != 0
    assert not [event for event in events if event.kind == "result"]
