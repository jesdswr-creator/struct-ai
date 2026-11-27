import json
import math

import pytest
from pydantic import ValidationError

from struct_ai.codes.registry import CodeRegistry, CodeUsageSnapshot
from struct_ai.exceptions import CodeDataError, MissingCodeValue
from struct_ai.serialization import canonical_json


def test_empty_catalogues_do_not_imply_verified_usage(catalogue_root):
    registry = CodeRegistry.load(catalogue_root)
    assert registry.records == ()
    assert len(registry.data_digest) == 64
    snapshot = registry.new_tracker().snapshot()
    assert snapshot.unverified_count == 0
    assert snapshot.warning is None


def test_all_shipped_constants_are_unverified():
    records = CodeRegistry.load().records
    assert records  # M1 public-draft data now exists; do not let this be vacuously true.
    assert all(not record.data.verified and record.data.verified_by is None for record in records)


def test_actual_use_is_unique_sorted_and_snapshot_is_immutable(
    catalogue_root, write_records, synthetic_record
):
    write_records(
        [
            synthetic_record | {"key": "b"},
            synthetic_record | {"key": "a", "value": 8.0},
            synthetic_record | {"key": "unused"},
        ]
    )
    registry = CodeRegistry.load(catalogue_root)
    tracker = registry.new_tracker()
    assert registry.require("is456_2000.b", tracker) == 12.0
    first_snapshot = tracker.snapshot()
    assert registry.require("is456_2000.a", tracker) == 8.0
    assert registry.require("is456_2000.b", tracker) == 12.0
    snapshot = tracker.snapshot()
    assert [item.identifier for item in snapshot.constants] == ["is456_2000.a", "is456_2000.b"]
    assert snapshot.unverified_count == 2
    assert snapshot.warning == "UNVERIFIED CODE CONSTANTS USED: 2"
    assert first_snapshot.unverified_count == 1
    with pytest.raises(ValidationError):
        snapshot.constants[0].data.value = 999.0
    assert registry.new_tracker().snapshot().constants == ()


@pytest.mark.parametrize(
    "change",
    [
        {"value": None, "verification_note": "TODO_VERIFY — source not supplied"},
        {"clause": "TODO_VERIFY"},
        {"code_edition": "TODO_VERIFY"},
        {"units": "TODO_VERIFY"},
    ],
)
def test_missing_data_blocks_and_is_not_counted_as_used(
    catalogue_root, write_records, synthetic_record, change
):
    write_records([synthetic_record | change])
    registry = CodeRegistry.load(catalogue_root)
    tracker = registry.new_tracker()
    with pytest.raises(MissingCodeValue) as caught:
        registry.require("is456_2000.synthetic_scalar", tracker)
    assert caught.value.clause
    assert caught.value.limit
    assert tracker.snapshot().constants == ()


def test_unknown_identifier_does_not_fall_back(catalogue_root):
    registry = CodeRegistry.load(catalogue_root)
    with pytest.raises(MissingCodeValue, match="not supplied"):
        registry.require("is456_2000.invented", registry.new_tracker())


@pytest.mark.parametrize(
    "change",
    [
        {"value": "12"},
        {"value": True},
        {"value": math.nan},
        {"value": math.inf},
        {"value": None},
        {"verified": "false"},
        {"verified": True},
        {"verified_by": "Someone"},
        {"clause": "  "},
        {"units": ""},
        {"unexpected": 7},
    ],
)
def test_malformed_record_fails_loudly(catalogue_root, write_records, synthetic_record, change):
    write_records([synthetic_record | change])
    with pytest.raises(CodeDataError) as caught:
        CodeRegistry.load(catalogue_root)
    assert caught.value.clause
    assert caught.value.limit


def test_missing_file_is_not_an_empty_verified_catalogue(catalogue_root):
    (catalogue_root / "is875/data/catalogue.json").unlink()
    with pytest.raises(CodeDataError, match="missing"):
        CodeRegistry.load(catalogue_root)


def test_duplicate_json_key_fails(catalogue_root):
    (catalogue_root / "is875/data/catalogue.json").write_text(
        '{"schema_version":1,"code":"is875","code":"is456_2000","constants":[]}',
        encoding="utf-8",
    )
    with pytest.raises(CodeDataError, match="Duplicate JSON key"):
        CodeRegistry.load(catalogue_root)


def test_duplicate_identifiers_across_files_fail(catalogue_root, write_records, synthetic_record):
    write_records([synthetic_record])
    write_records([synthetic_record], filename="second.json")
    with pytest.raises(CodeDataError, match="Duplicate constant"):
        CodeRegistry.load(catalogue_root)


def test_wrong_namespace_fails(catalogue_root):
    path = catalogue_root / "is875/data/catalogue.json"
    path.write_text(
        json.dumps({"schema_version": 1, "code": "is456_2000", "constants": []}), encoding="utf-8"
    )
    with pytest.raises(CodeDataError, match="namespace"):
        CodeRegistry.load(catalogue_root)


def test_repeated_load_is_deterministic_and_whitespace_independent(
    catalogue_root, write_records, synthetic_record
):
    path = write_records([synthetic_record])
    first = CodeRegistry.load(catalogue_root)
    path.write_text(json.dumps(json.loads(path.read_text()), indent=4), encoding="utf-8")
    second = CodeRegistry.load(catalogue_root)
    assert first == second
    first_tracker, second_tracker = first.new_tracker(), second.new_tracker()
    first.require("is456_2000.synthetic_scalar", first_tracker)
    second.require("is456_2000.synthetic_scalar", second_tracker)
    assert canonical_json(first_tracker.snapshot()) == canonical_json(second_tracker.snapshot())


def test_cannot_mix_data_revisions(catalogue_root, write_records, synthetic_record):
    write_records([synthetic_record])
    original = CodeRegistry.load(catalogue_root)
    tracker = original.new_tracker()
    original.require("is456_2000.synthetic_scalar", tracker)
    write_records([synthetic_record | {"value": 13.0}])
    changed = CodeRegistry.load(catalogue_root)
    with pytest.raises(CodeDataError, match="different catalogue revisions"):
        changed.require("is456_2000.synthetic_scalar", tracker)


def test_used_snapshot_rejects_duplicate_ids(catalogue_root, write_records, synthetic_record):
    write_records([synthetic_record])
    registry = CodeRegistry.load(catalogue_root)
    with pytest.raises(ValidationError, match="unique and sorted"):
        CodeUsageSnapshot(data_digest=registry.data_digest, constants=registry.records * 2)
