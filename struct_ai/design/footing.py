"""Footing design is outside v1. Units: no values accepted."""

from typing import Never


def design_footing(*args: object, **kwargs: object) -> Never:
    """Refuse footing design without returning numerical placeholders. Units: none."""
    raise NotImplementedError("Footing design is outside v1; no footing design has been produced.")
