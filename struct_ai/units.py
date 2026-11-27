"""The only unit-conversion module: analysis kN/m; section design N/mm/N/mm²."""

from __future__ import annotations

import math
from numbers import Real

from struct_ai.exceptions import UnitConversionError

N_PER_KN = 1_000.0
MM_PER_M = 1_000.0


def _scale(value: float, factor: float, source: str, target: str) -> float:
    """Scale a finite real number without rounding or clamping. Units: source -> target."""
    context = f"UNIT CONVERSION: {source} -> {target} (not an IS-code clause)"
    if isinstance(value, bool) or not isinstance(value, Real):
        raise UnitConversionError(
            "Unit conversions require a finite real number, not text or a boolean.",
            clause=context,
            value=value,
            limit=f"finite real value in {source}",
        )
    try:
        result = float(value) * factor
    except OverflowError as error:
        raise UnitConversionError(
            "Unit conversion overflowed; no value was returned.",
            clause=context,
            value=value,
            limit=f"finite representable value in {target}",
        ) from error
    if not math.isfinite(result):
        raise UnitConversionError(
            "Unit conversion is non-finite; no value was returned.",
            clause=context,
            value=value,
            limit=f"finite representable value in {target}",
        )
    return result


def kn_to_n(value: float) -> float:
    """Convert force from kN to N; signs are preserved."""
    return _scale(value, N_PER_KN, "kN", "N")


def n_to_kn(value: float) -> float:
    """Convert force from N to kN; signs are preserved."""
    return _scale(value, 1 / N_PER_KN, "N", "kN")


def m_to_mm(value: float) -> float:
    """Convert length from m to mm; signs are preserved."""
    return _scale(value, MM_PER_M, "m", "mm")


def mm_to_m(value: float) -> float:
    """Convert length from mm to m; signs are preserved."""
    return _scale(value, 1 / MM_PER_M, "mm", "m")


def kn_m_to_n_mm(value: float) -> float:
    """Convert moment from kN·m to N·mm, not to N·m."""
    return _scale(value, N_PER_KN * MM_PER_M, "kN m", "N mm")


def n_mm_to_kn_m(value: float) -> float:
    """Convert moment from N·mm to kN·m."""
    return _scale(value, 1 / (N_PER_KN * MM_PER_M), "N mm", "kN m")


def m2_to_mm2(value: float) -> float:
    """Convert area from m² to mm²."""
    return _scale(value, MM_PER_M**2, "m²", "mm²")


def mm2_to_m2(value: float) -> float:
    """Convert area from mm² to m²."""
    return _scale(value, 1 / MM_PER_M**2, "mm²", "m²")


def m4_to_mm4(value: float) -> float:
    """Convert second moment of area from m⁴ to mm⁴."""
    return _scale(value, MM_PER_M**4, "m⁴", "mm⁴")


def mm4_to_m4(value: float) -> float:
    """Convert second moment of area from mm⁴ to m⁴."""
    return _scale(value, 1 / MM_PER_M**4, "mm⁴", "m⁴")


def mpa_to_kn_m2(value: float) -> float:
    """Convert stress/modulus from MPa (N/mm²) to kN/m²."""
    return _scale(value, MM_PER_M**2 / N_PER_KN, "N/mm²", "kN/m²")


def kn_m2_to_mpa(value: float) -> float:
    """Convert stress/modulus from kN/m² to MPa (N/mm²)."""
    return _scale(value, N_PER_KN / MM_PER_M**2, "kN/m²", "N/mm²")
