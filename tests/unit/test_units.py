import math

import pytest

from struct_ai import units
from struct_ai.exceptions import UnitConversionError


@pytest.mark.parametrize(
    ("convert", "value", "expected"),
    [
        (units.kn_to_n, 2.5, 2500.0),
        (units.n_to_kn, -2500.0, -2.5),
        (units.m_to_mm, 3.2, 3200.0),
        (units.mm_to_m, 3200.0, 3.2),
        # kN*m -> (1000 N)*(1000 mm), not just one factor of 1000.
        (units.kn_m_to_n_mm, 12.5, 12_500_000.0),
        (units.n_mm_to_kn_m, 12_500_000.0, 12.5),
        # The length multiplier must be raised to the dimension's power.
        (units.m2_to_mm2, 0.12, 120_000.0),
        (units.mm2_to_m2, 120_000.0, 0.12),
        (units.m4_to_mm4, 0.0008, 800_000_000.0),
        (units.mm4_to_m4, 800_000_000.0, 0.0008),
        # 1 N/mm² = (0.001 kN)/(0.000001 m²) = 1000 kN/m².
        (units.mpa_to_kn_m2, 25_000.0, 25_000_000.0),
        (units.kn_m2_to_mpa, 25_000_000.0, 25_000.0),
    ],
)
def test_independent_conversions(convert, value, expected):
    assert convert(value) == pytest.approx(expected, rel=1e-14)


@pytest.mark.parametrize(
    ("forward", "backward"),
    [
        (units.kn_to_n, units.n_to_kn),
        (units.m_to_mm, units.mm_to_m),
        (units.kn_m_to_n_mm, units.n_mm_to_kn_m),
        (units.m2_to_mm2, units.mm2_to_m2),
        (units.m4_to_mm4, units.mm4_to_m4),
        (units.mpa_to_kn_m2, units.kn_m2_to_mpa),
    ],
)
@pytest.mark.parametrize("value", [-1e6, -0.3, 0.0, 1e-9, 12.345])
def test_round_trip(forward, backward, value):
    assert backward(forward(value)) == pytest.approx(value, rel=1e-14)


@pytest.mark.parametrize("value", [math.nan, math.inf, -math.inf, "2", None, True, 1e308])
def test_invalid_values_raise_with_context(value):
    with pytest.raises(UnitConversionError) as caught:
        units.kn_m_to_n_mm(value)
    assert "kN m" in caught.value.clause
    assert caught.value.limit


def test_elastic_deflection_is_equal_in_both_unit_systems():
    # Independent SI calculation: 12*3³/(3*25,000,000*0.0008) = 0.0054 m.
    force_kn, length_m, modulus_kn_m2, inertia_m4 = 12.0, 3.0, 25_000_000.0, 0.0008
    deflection_m = force_kn * length_m**3 / (3 * modulus_kn_m2 * inertia_m4)
    deflection_mm = (
        units.kn_to_n(force_kn)
        * units.m_to_mm(length_m) ** 3
        / (3 * units.kn_m2_to_mpa(modulus_kn_m2) * units.m4_to_mm4(inertia_m4))
    )
    assert deflection_m == pytest.approx(0.0054, rel=1e-14)
    assert deflection_mm == pytest.approx(5.4, rel=1e-14)
    assert units.mm_to_m(deflection_mm) == pytest.approx(deflection_m, rel=1e-14)
