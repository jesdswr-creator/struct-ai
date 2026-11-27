import json
import math

import pytest

from struct_ai.services import engine_service
from struct_ai.services.project_io import load_project, save_project


def test_evidence_is_canonical_and_atomic(tmp_path):
    path = tmp_path / "evidence.json"
    engine_service.write_diagnostic_evidence(path, {"z": 2, "a": 1})
    assert path.read_text(encoding="utf-8") == '{"a":1,"z":2}\n'
    engine_service.write_diagnostic_evidence(path, {"replacement": True})
    assert json.loads(path.read_text(encoding="utf-8")) == {"replacement": True}
    assert list(tmp_path.iterdir()) == [path]


def test_failed_serialisation_does_not_destroy_previous_evidence(tmp_path):
    path = tmp_path / "evidence.json"
    engine_service.write_diagnostic_evidence(path, {"original": True})
    with pytest.raises(ValueError):
        engine_service.write_diagnostic_evidence(path, {"invalid": math.nan})
    assert json.loads(path.read_text(encoding="utf-8")) == {"original": True}


@pytest.mark.parametrize("operation", [save_project, load_project])
def test_unimplemented_project_io_is_explicit(operation):
    with pytest.raises(NotImplementedError, match="BuildingInput"):
        operation()
