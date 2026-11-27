import math

import pytest
from pydantic import ValidationError

from struct_ai.checks import CheckResult
from struct_ai.serialization import canonical_json, content_hash


def payload(**overrides):
    data = {
        "name": "SYNTHETIC upper-bound check",
        "ok": True,
        "clause": "SYNTHETIC TEST, not an IS-code clause",
        "demand": 3.0,
        "capacity": 4.0,
        "ratio": 0.75,
        "units": "kN",
    }
    return data | overrides


def test_check_is_immutable_and_canonical():
    result = CheckResult(**payload())
    with pytest.raises(ValidationError):
        result.ok = False
    assert CheckResult.model_validate_json(result.model_dump_json()) == result
    assert content_hash(result) == content_hash(payload())
    assert canonical_json(payload()) == canonical_json(dict(reversed(list(payload().items()))))


@pytest.mark.parametrize(
    "overrides",
    [
        {"ratio": 0.74},
        {"ok": False},
        {"demand": -3.0},
        {"capacity": 0.0},
        {"capacity": -4.0},
        {"demand": math.nan},
        {"capacity": math.inf},
        {"ratio": math.inf},
        {"ok": "true"},
        {"demand": "3"},
        {"demand": True},
        {"name": "   "},
        {"units": ""},
        {"surprise": 1},
    ],
)
def test_inconsistent_or_ambiguous_check_is_rejected(overrides):
    with pytest.raises(ValidationError):
        CheckResult(**payload(**overrides))


def test_near_limit_does_not_clamp_a_failure_to_pass():
    demand = 4.000000000000001
    result = CheckResult(**payload(demand=demand, ratio=demand / 4, ok=False))
    assert not result.ok
    with pytest.raises(ValidationError, match="without a passing tolerance"):
        CheckResult(**payload(demand=demand, ratio=demand / 4, ok=True))


def test_zero_demand_and_exact_limit():
    assert CheckResult(**payload(demand=0.0, ratio=0.0)).ok
    assert CheckResult(**payload(demand=4.0, ratio=1.0)).ok


def test_canonical_serialisation_rejects_nan():
    with pytest.raises(ValueError):
        canonical_json({"value": math.nan})
