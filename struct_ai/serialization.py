"""Canonical result serialisation, separate from clocks and logs. Units: preserved."""

from __future__ import annotations

import hashlib
import json
from typing import Any

from pydantic import BaseModel


def canonical_json(value: BaseModel | dict[str, Any] | list[Any]) -> str:
    """Serialise deterministically; reject NaN/Infinity. Units: no conversion performed."""
    data = value.model_dump(mode="json") if isinstance(value, BaseModel) else value
    return json.dumps(
        data, ensure_ascii=False, allow_nan=False, sort_keys=True, separators=(",", ":")
    )


def content_hash(value: BaseModel | dict[str, Any] | list[Any]) -> str:
    """Hash canonical UTF-8 content, excluding no fields implicitly. Units: none."""
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()
