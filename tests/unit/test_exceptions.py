import json
import math

import pytest

from struct_ai.exceptions import (
    CodeDataError,
    InputOutOfRange,
    MissingCodeValue,
    OperationCancelled,
    ScopeRefusal,
    SolverFailure,
    UnitConversionError,
)


@pytest.mark.parametrize(
    "error_type",
    [
        CodeDataError,
        InputOutOfRange,
        MissingCodeValue,
        OperationCancelled,
        ScopeRefusal,
        SolverFailure,
        UnitConversionError,
    ],
)
def test_typed_error_preserves_context(error_type):
    error = error_type("Explicit failure", clause="SYNTHETIC", value=7, limit=6)
    assert str(error) == "Explicit failure"
    assert error.as_dict() == {
        "type": error_type.__name__,
        "message": "Explicit failure",
        "clause": "SYNTHETIC",
        "value": 7,
        "limit": 6,
    }


def test_nonfinite_error_context_is_still_valid_json():
    error = InputOutOfRange("Invalid", clause="TEST", value={"x": math.nan}, limit=1)
    assert json.loads(json.dumps(error.as_dict(), allow_nan=False))["value"] == {"x": "nan"}
