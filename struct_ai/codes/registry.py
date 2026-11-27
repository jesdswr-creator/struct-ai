"""Fail-closed catalogue loading and actual-use provenance. Units: stored per record."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated, Any, Literal, Self

from pydantic import Field, ValidationError, field_validator, model_validator

from struct_ai.checks import FrozenModel, NonEmptyText
from struct_ai.exceptions import CodeDataError, MissingCodeValue
from struct_ai.serialization import canonical_json, content_hash

CODE_NAMES = ("is456_2000", "is875", "is1893_2016", "is13920_2016")
CodeName = Literal["is456_2000", "is875", "is1893_2016", "is13920_2016"]
Digest = Annotated[str, Field(pattern=r"^[a-f0-9]{64}$")]


class CodeConstant(FrozenModel):
    """One scalar/cell, never an implicit default. Units: required in `units`."""

    key: Annotated[str, Field(pattern=r"^[a-z][a-z0-9_.]*$")]
    value: float | None
    clause: NonEmptyText
    code_edition: NonEmptyText
    units: NonEmptyText
    verified: bool
    verified_by: NonEmptyText | None
    source: NonEmptyText
    verification_note: NonEmptyText

    @model_validator(mode="after")
    def explicit_verification_state(self) -> Self:
        """Reject contradictory verification metadata. Units: unchanged."""
        if self.verified and (self.verified_by is None or self.value is None):
            raise ValueError("Verified records require a value and an identified verifier")
        if not self.verified and self.verified_by is not None:
            raise ValueError("Unverified records must have verified_by=null")
        if self.value is None and "TODO_VERIFY" not in self.verification_note:
            raise ValueError("A missing value must explicitly carry TODO_VERIFY")
        return self


class CodeCatalogue(FrozenModel):
    """An edition namespace with explicit records. Units: stored per constant."""

    schema_version: Literal[1]
    code: CodeName
    constants: tuple[CodeConstant, ...]

    @field_validator("schema_version", mode="before")
    @classmethod
    def strict_schema_version(cls, value: Any) -> int:
        """Reject bool/float aliases for the JSON format version. Units: integer version."""
        if type(value) is not int:
            raise ValueError("schema_version must be the integer 1, not a boolean or float")
        return value


class CataloguedConstant(FrozenModel):
    """A record identified across catalogues. Units: data.units."""

    identifier: NonEmptyText
    data: CodeConstant


class CodeUsageSnapshot(FrozenModel):
    """Immutable actual-use evidence for one run. Units: per used record."""

    data_digest: Digest
    constants: tuple[CataloguedConstant, ...]

    @model_validator(mode="after")
    def unique_sorted_records(self) -> Self:
        """Require a canonical, duplicate-free use list. Units: none."""
        identifiers = [record.identifier for record in self.constants]
        if identifiers != sorted(set(identifiers)):
            raise ValueError("Used constants must be unique and sorted by identifier")
        if any(record.data.value is None for record in self.constants):
            raise ValueError("Missing values cannot appear as consumed constants")
        return self

    @property
    def unverified_count(self) -> int:
        """Count distinct unverified records actually used. Units: count."""
        return sum(not record.data.verified for record in self.constants)

    @property
    def warning(self) -> str | None:
        """Return the mandatory warning when applicable. Units: count in warning."""
        if self.unverified_count:
            return f"UNVERIFIED CODE CONSTANTS USED: {self.unverified_count}"
        return None


class CodeUseTracker:
    """Private mutable run-local accumulator; never shared between runs. Units: per record."""

    def __init__(self, data_digest: str) -> None:
        """Bind a run to exactly one catalogue revision. Units: none."""
        self._data_digest = data_digest
        self._used: dict[str, CataloguedConstant] = {}

    def capture(self, data_digest: str, record: CataloguedConstant) -> None:
        """Record a consumed constant, rejecting mixed revisions. Units: record.data.units."""
        if data_digest != self._data_digest:
            raise CodeDataError(
                "A run cannot combine code data from different catalogue revisions.",
                clause=record.data.clause,
                value=data_digest,
                limit=self._data_digest,
            )
        self._used[record.identifier] = record

    def snapshot(self) -> CodeUsageSnapshot:
        """Freeze the sorted use list; subsequent captures cannot mutate it. Units: per record."""
        return CodeUsageSnapshot(
            data_digest=self._data_digest,
            constants=tuple(self._used[key] for key in sorted(self._used)),
        )


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    """Reject duplicate JSON keys instead of accepting the last value. Units: none."""
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"Duplicate JSON key: {key}")
        result[key] = value
    return result


def _reject_nonfinite(token: str) -> None:
    """Reject non-standard NaN/Infinity tokens. Units: none."""
    raise ValueError(f"Non-finite JSON number: {token}")


@dataclass(frozen=True, slots=True)
class CodeRegistry:
    """Immutable catalogue, loaded explicitly and validated completely. Units: per record."""

    records: tuple[CataloguedConstant, ...]
    data_digest: str

    @classmethod
    def load(cls, root: Path | None = None) -> CodeRegistry:
        """Read all four required catalogue directories. Units: no conversion performed."""
        root = Path(__file__).resolve().parent if root is None else root
        records: dict[str, CataloguedConstant] = {}
        catalogues: list[dict[str, Any]] = []
        for namespace in CODE_NAMES:
            paths = sorted((root / namespace / "data").glob("*.json"))
            if not paths:
                raise CodeDataError(
                    "A required code catalogue is missing; an empty scan is not verification.",
                    clause="SOURCE-OF-TRUTH POLICY (application requirement)",
                    value=namespace,
                    limit="at least one validated data/*.json file per code namespace",
                )
            for path in paths:
                try:
                    document = json.loads(
                        path.read_text(encoding="utf-8"),
                        object_pairs_hook=_unique_object,
                        parse_constant=_reject_nonfinite,
                    )
                    catalogue = CodeCatalogue.model_validate_json(canonical_json(document))
                except (OSError, ValueError, TypeError, ValidationError) as error:
                    raise CodeDataError(
                        f"Cannot load {namespace}/data/{path.name}: {error}",
                        clause="SOURCE-OF-TRUTH POLICY (application requirement)",
                        value=f"{namespace}/data/{path.name}",
                        limit="valid, finite, unambiguous code-record JSON",
                    ) from error
                if catalogue.code != namespace:
                    raise CodeDataError(
                        "Catalogue namespace does not match its directory.",
                        clause="SOURCE-OF-TRUTH POLICY (application requirement)",
                        value=catalogue.code,
                        limit=namespace,
                    )
                catalogues.append(catalogue.model_dump(mode="json"))
                for constant in catalogue.constants:
                    identifier = f"{namespace}.{constant.key}"
                    if identifier in records:
                        raise CodeDataError(
                            "Duplicate constant identifier; no value was selected.",
                            clause=constant.clause,
                            value=identifier,
                            limit="one definition across all catalogue files",
                        )
                    records[identifier] = CataloguedConstant(identifier=identifier, data=constant)
        return cls(
            records=tuple(records[key] for key in sorted(records)),
            data_digest=content_hash(catalogues),
        )

    def new_tracker(self) -> CodeUseTracker:
        """Start isolated actual-use tracking. Units: none."""
        return CodeUseTracker(self.data_digest)

    def require(
        self, identifier: str, tracker: CodeUseTracker, *, expected_units: str | None = None
    ) -> float:
        """Resolve/log a value; optionally enforce its unit contract. Units: declared in record."""
        record = next((item for item in self.records if item.identifier == identifier), None)
        if record is None:
            raise MissingCodeValue(
                f"Required code constant is not supplied: {identifier}",
                clause="TODO_VERIFY — required source not supplied",
                value=None,
                limit=f"authorised numeric value and citation for {identifier}",
            )
        if record.data.value is None or any(
            "TODO_VERIFY" in text
            for text in (record.data.clause, record.data.code_edition, record.data.units)
        ):
            raise MissingCodeValue(
                f"Required code constant is incomplete: {identifier}",
                clause=record.data.clause,
                value=record.data.value,
                limit=f"supplied value, edition, clause and units for {identifier}",
            )
        if expected_units is not None and record.data.units != expected_units:
            raise CodeDataError(
                f"Code constant has incompatible units: {identifier}",
                clause=record.data.clause,
                value=record.data.units,
                limit=expected_units,
            )
        tracker.capture(self.data_digest, record)
        return record.data.value
