import json
from pathlib import Path

import pytest

NAMESPACES = ("is456_2000", "is875", "is1893_2016", "is13920_2016")


@pytest.fixture
def synthetic_record():
    return {
        "key": "synthetic_scalar",
        "value": 12.0,
        "clause": "SYNTHETIC TEST 1 — NOT an IS-code clause",
        "code_edition": "SYNTHETIC TEST DATA — NOT an Indian Standard",
        "units": "test units",
        "verified": False,
        "verified_by": None,
        "source": "Hand-authored software test fixture, not an engineering source",
        "verification_note": "UNVERIFIED synthetic data for loader tests only",
    }


@pytest.fixture
def catalogue_root(tmp_path):
    root = tmp_path / "codes"
    for namespace in NAMESPACES:
        directory = root / namespace / "data"
        directory.mkdir(parents=True)
        (directory / "catalogue.json").write_text(
            json.dumps({"schema_version": 1, "code": namespace, "constants": []}), encoding="utf-8"
        )
    return root


@pytest.fixture
def write_records(catalogue_root):
    def write(records, *, namespace="is456_2000", filename="catalogue.json") -> Path:
        path = catalogue_root / namespace / "data" / filename
        path.write_text(
            json.dumps({"schema_version": 1, "code": namespace, "constants": records}),
            encoding="utf-8",
        )
        return path

    return write
