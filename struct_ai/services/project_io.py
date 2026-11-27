"""Atomic diagnostic evidence I/O only; BuildingInput projects are not implemented. Units: none."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path
from typing import Any, Never

from pydantic import BaseModel

from struct_ai.serialization import canonical_json


def write_evidence(path: Path, payload: BaseModel | dict[str, Any]) -> None:
    """Write canonical JSON atomically; preserve previous files on failure. Units: none."""
    text = canonical_json(payload) + "\n"
    path = path.resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=path.parent, prefix=f".{path.name}.", delete=False
        ) as stream:
            temporary = Path(stream.name)
            stream.write(text)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def save_project(*args: object, **kwargs: object) -> Never:
    """Do not mistake diagnostic evidence for a validated BuildingInput project. Units: none."""
    raise NotImplementedError("BuildingInput project save/load is not implemented in M0/M0b.")


def load_project(*args: object, **kwargs: object) -> Never:
    """Refuse project loading until BuildingInput and its versioned format exist. Units: none."""
    raise NotImplementedError("BuildingInput project save/load is not implemented in M0/M0b.")
