import pytest

from struct_ai.codes.registry import CodeRegistry
from struct_ai.design.beam_materials import ConcreteLaw, FlexureData, SteelLaw


@pytest.mark.parametrize("fy", [415, 500])
@pytest.mark.parametrize(
    "ratio,plastic",
    [
        (0.8, 0.0),
        (0.85, 0.0001),
        (0.9, 0.0003),
        (0.95, 0.0007),
        (0.975, 0.001),
        (1.0, 0.002),
    ],
)
def test_steel_points_use_design_total_strain(fy, ratio, plastic):
    registry = CodeRegistry.load()
    data = FlexureData(registry, registry.new_tracker())
    law = SteelLaw.load(data, f"Fe{fy}")
    # Independent N02 design stress/elastic strain + primitive inelastic strain.
    stress = ratio * fy / 1.15
    strain = stress / 200000 + plastic
    assert law.stress(strain) == pytest.approx(stress, rel=1e-13)
    assert law.stress(-strain) == pytest.approx(-stress, rel=1e-13)
    assert all(not r.data.verified for r in data.tracker.snapshot().constants)


@pytest.mark.parametrize("fy", [415, 500])
def test_steel_elastic_interpolated_and_post_yield_segments(fy):
    registry = CodeRegistry.load()
    law = SteelLaw.load(FlexureData(registry, registry.new_tracker()), f"Fe{fy}")
    assert law.stress(0.0005) == 100.0
    fd = fy / 1.15
    left = 0.9 * fd / 200000 + 0.0003
    right = 0.95 * fd / 200000 + 0.0007
    assert law.stress((left + right) / 2) == pytest.approx(0.925 * fd, rel=1e-13)
    assert law.stress(0.01) == fd
    assert law.stress(-0.01) == -fd
    assert law.stress(0.0) == 0.0


def test_concrete_parabola_plateau_and_ignored_tension_are_distinct():
    registry = CodeRegistry.load()
    law = ConcreteLaw.load(FlexureData(registry, registry.new_tracker()), 25.0)
    # At half the plateau strain the parabola is 3/4 of its peak, NOT full peak.
    assert law.stress(0.001) == pytest.approx((3 / 4) * 0.446 * 25, rel=1e-13)
    assert law.stress(0.002) == 0.446 * 25
    assert law.stress(0.0035) == 0.446 * 25
    assert law.stress(0.0) == 0.0
    assert law.stress(-0.001) == 0.0
