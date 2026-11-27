"""Independent transcription oracles for the explicit public draft, NOT code verification."""

import pytest

from struct_ai.codes.registry import CodeRegistry

# Separate transcription of N13 Table 6.1, not read/generated from shipped JSON.
SHEAR_ROWS = (
    (0.15, (0.28, 0.29, 0.29, 0.29, 0.30)),
    (0.25, (0.36, 0.36, 0.37, 0.37, 0.38)),
    (0.50, (0.48, 0.49, 0.50, 0.50, 0.51)),
    (0.75, (0.56, 0.57, 0.59, 0.59, 0.60)),
    (1.00, (0.62, 0.64, 0.66, 0.67, 0.68)),
    (1.25, (0.67, 0.70, 0.71, 0.73, 0.74)),
    (1.50, (0.72, 0.74, 0.76, 0.78, 0.79)),
    (1.75, (0.75, 0.78, 0.80, 0.82, 0.84)),
    (2.00, (0.79, 0.82, 0.84, 0.86, 0.88)),
    (2.25, (0.81, 0.85, 0.88, 0.90, 0.92)),
    (2.50, (0.82, 0.88, 0.91, 0.93, 0.95)),
    (2.75, (0.82, 0.90, 0.94, 0.96, 0.98)),
    (3.00, (0.82, 0.92, 0.96, 0.99, 1.01)),
)


@pytest.mark.parametrize("row,expected", enumerate(SHEAR_ROWS))
def test_table19_axis_and_every_cell_match_independent_transcription(row, expected):
    registry = CodeRegistry.load()
    tracker = registry.new_tracker()
    prefix = f"is456_2000.beam_checks.shear.table19.p{row:02}"
    assert registry.require(prefix + ".percent", tracker, expected_units="%") == expected[0]
    for grade, value in zip((20, 25, 30, 35, 40), expected[1], strict=True):
        assert registry.require(prefix + f".m{grade}", tracker, expected_units="N/mm²") == value
    assert tracker.snapshot().unverified_count == 6


@pytest.mark.parametrize(
    "grade,tmax,bond",
    [(20, 2.8, 1.2), (25, 3.1, 1.4), (30, 3.5, 1.5), (35, 3.7, 1.7), (40, 4.0, 1.9)],
)
def test_maximum_shear_and_bond_stress_cells(grade, tmax, bond):
    registry = CodeRegistry.load()
    tracker = registry.new_tracker()
    prefix = "is456_2000.beam_checks."
    assert registry.require(prefix + f"shear.table20.m{grade}", tracker) == tmax
    assert registry.require(prefix + f"bond.plain_tension.m{grade}", tracker) == bond


def test_m2_inventory_is_wholly_unverified_and_missing_routes_are_explicit():
    records = [r for r in CodeRegistry.load().records if ".beam_checks." in r.identifier]
    assert len(records) == 126
    assert all(not r.data.verified and r.data.verified_by is None for r in records)
    missing = {r.identifier for r in records if r.data.value is None}
    assert missing == {
        "is456_2000.beam_checks.cover.fire_table16a",
        "is456_2000.beam_checks.spacing.maximum_table15",
        "is456_2000.beam_checks.deflection.chart_factors",
    }
