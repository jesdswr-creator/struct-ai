"""Explicit engine errors with machine-readable context. Units: carried in context."""

from __future__ import annotations

import math
from collections.abc import Mapping
from typing import Any


def _json_safe(value: Any) -> Any:
    """Make error context JSON-safe without hiding non-finite values. Units: unchanged."""
    if isinstance(value, float) and not math.isfinite(value):
        return repr(value)
    if value is None or isinstance(value, str | int | float | bool):
        return value
    if isinstance(value, Mapping):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, list | tuple):
        return [_json_safe(item) for item in value]
    return repr(value)


class EngineeringError(Exception):
    """Base for an actionable failure, never a substitute result. Units: explicit context."""

    def __init__(
        self,
        message: str,
        *,
        clause: str,
        value: Any,
        limit: Any,
    ) -> None:
        """Keep message, citation, offending value and requirement. Units: caller-specified."""
        super().__init__(message)
        self.clause = clause
        self.value = value
        self.limit = limit

    def as_dict(self) -> dict[str, Any]:
        """Return serialisable diagnostic context, not a result. Units: unchanged."""
        return {
            "type": type(self).__name__,
            "message": str(self),
            "clause": self.clause,
            "value": _json_safe(self.value),
            "limit": _json_safe(self.limit),
        }


class InputOutOfRange(EngineeringError):
    """An input violates an explicit bound. Units: value and limit must identify units."""


class ScopeRefusal(EngineeringError):
    """A requested structure is outside the supported scope. Units: context-specific."""


class MissingCodeValue(EngineeringError):
    """A required code value is absent; calculation is blocked. Units: record-specific."""


class CodeDataError(EngineeringError):
    """A code catalogue is absent, ambiguous or malformed. Units: record-specific."""


class UnitConversionError(EngineeringError):
    """A conversion received an invalid or overflowing value. Units: named in clause."""


class SolverFailure(EngineeringError):
    """A solver import, analysis or verification failed. Units: analysis uses kN, m."""


class OperationCancelled(EngineeringError):
    """A run was cancelled; no partial result may be published. Units: none."""
