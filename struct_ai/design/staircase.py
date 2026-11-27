"""Staircase design is outside v1. Units: no values accepted."""

from typing import Never


def design_staircase(*args: object, **kwargs: object) -> Never:
    """Refuse staircase design without returning numerical placeholders. Units: none."""
    raise NotImplementedError(
        "Staircase design is outside v1; no staircase design has been produced."
    )
