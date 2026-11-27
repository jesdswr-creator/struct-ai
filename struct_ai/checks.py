"""Immutable upper-bound checks; demand/capacity have the declared units, ratio is 1."""

from __future__ import annotations

import math
from typing import Annotated, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

NonEmptyText = Annotated[str, Field(min_length=1, pattern=r"\S")]
NonNegative = Annotated[float, Field(ge=0, allow_inf_nan=False)]
Positive = Annotated[float, Field(gt=0, allow_inf_nan=False)]


class FrozenModel(BaseModel):
    """Reject unknown fields and coercion; freeze values. Units: field-specific."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        strict=True,
        allow_inf_nan=False,
        validate_default=True,
    )


class CheckResult(FrozenModel):
    """A required amount versus an available amount. Units: declared; ratio dimensionless.

    Demand must be non-negative and capacity strictly positive. For a minimum provision
    check, demand is the required minimum and capacity is the actual provision. Signed
    actions belong in analysis results, not in this utilisation representation. A zero
    or undefined capacity must raise an engineering error, not produce NaN or infinity.
    The equality check for ratio representation does NOT relax the pass/fail decision.
    """

    name: NonEmptyText
    ok: bool
    clause: NonEmptyText
    demand: NonNegative
    capacity: Positive
    ratio: NonNegative
    units: NonEmptyText

    @model_validator(mode="after")
    def consistent_result(self) -> Self:
        """Reject contradictory payloads without changing them. Units: ratio is 1."""
        expected_ratio = self.demand / self.capacity
        if not math.isfinite(expected_ratio) or not math.isclose(
            self.ratio, expected_ratio, rel_tol=1e-12, abs_tol=0.0
        ):
            raise ValueError("ratio must equal demand / capacity (no rounded ratios in results)")
        if self.ok != (self.demand <= self.capacity):
            raise ValueError("ok must reflect demand <= capacity without a passing tolerance")
        return self
