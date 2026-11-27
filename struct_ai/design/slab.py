"""Slab DESIGN is outside v1; load distribution is separate. Units: no values accepted."""

from typing import Never


def design_slab(*args: object, **kwargs: object) -> Never:
    """Refuse slab design without returning numerical placeholders. Units: none."""
    raise NotImplementedError("Slab design is outside v1; no slab design has been produced.")
