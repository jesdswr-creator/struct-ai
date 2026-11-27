import json

import pytest

from struct_ai.codes.registry import CodeRegistry
from struct_ai.exceptions import CodeDataError, InputOutOfRange
from struct_ai.services import engine_service


@pytest.mark.parametrize("data", [None, [], "3", 3.0, True])
def test_wrong_top_level_type_has_typed_context(data):
    with pytest.raises(InputOutOfRange) as caught:
        engine_service.validate_diagnostic_input(data)
    assert caught.value.clause
    assert caught.value.value == data
    assert caught.value.limit


@pytest.mark.parametrize("force", [5e-324, -5e-324, 1e-7])
def test_subnormal_response_domain_is_refused_not_clamped(force):
    data = engine_service.diagnostic_example_input().model_dump() | {"force_kn": force}
    with pytest.raises(InputOutOfRange) as caught:
        engine_service.validate_diagnostic_input(data)
    assert caught.value.value["force_kn"] == force
    assert "software" in str(caught.value)


@pytest.mark.parametrize("version", [True, 1.0, "1", None, 2])
def test_catalogue_version_is_an_explicit_supported_integer(catalogue_root, version):
    path = catalogue_root / "is875/data/catalogue.json"
    path.write_text(
        json.dumps({"schema_version": version, "code": "is875", "constants": []}),
        encoding="utf-8",
    )
    with pytest.raises(CodeDataError):
        CodeRegistry.load(catalogue_root)
