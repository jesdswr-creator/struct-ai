"""Public-draft constitutive primitives. Units: stress N/mm²; strain dimensionless."""

from __future__ import annotations

import math
from dataclasses import dataclass
from functools import cached_property
from itertools import pairwise

from struct_ai.codes.registry import CodeRegistry, CodeUseTracker
from struct_ai.exceptions import CodeDataError


class FlexureData:
    """Run-local access with units, provenance and no numerical fallbacks. Units: per record."""

    def __init__(self, registry: CodeRegistry, tracker: CodeUseTracker) -> None:
        """Bind all accesses to one data revision. Units: none."""
        self.registry = registry
        self.tracker = tracker

    def number(self, key: str, units: str = "1", *, positive: bool = True) -> float:
        """Require a physical coefficient in its declared units. Units: `units`."""
        value = self.registry.require(
            f"is456_2000.flexure.{key}", self.tracker, expected_units=units
        )
        if value < 0 or (positive and value == 0):
            raise CodeDataError(
                f"Invalid constitutive/provision value: {key}",
                clause=f"CODE DATA DOMAIN: is456_2000.flexure.{key}",
                value={"value": value, "units": units},
                limit="positive" if positive else "nonnegative",
            )
        return value

    @cached_property
    def cold_worked_points(self) -> tuple[tuple[float, float], ...]:
        """Load primitive stress-ratio/plastic-strain pairs, NOT SP16. Units: 1, 1."""
        points = tuple(
            (
                self.number(f"steel.curve.p{index}.stress_ratio"),
                self.number(f"steel.curve.p{index}.plastic_strain", positive=False),
            )
            for index in range(1, 7)
        )
        valid = points[0][1] == 0 and points[-1][0] == 1
        valid = valid and all(
            0 < left[0] < right[0] <= 1 and left[1] < right[1] for left, right in pairwise(points)
        )
        if not valid:
            raise CodeDataError(
                "The representative steel curve is not a strictly ordered, bounded curve.",
                clause="38.1(e), Figure 23A — public-draft constitutive data",
                value=points,
                limit="increasing stress ratios/plastic strains, elastic origin, final ratio 1",
            )
        return points


@dataclass(frozen=True)
class ConcreteLaw:
    """NPTEL rounded-peak parabolic/plateau law; tension ignored. Units: N/mm², strain."""

    peak_factor: float
    peak_stress: float
    plateau_strain: float
    ultimate_strain: float

    @classmethod
    def load(cls, data: FlexureData, fck_n_mm2: float) -> ConcreteLaw:
        """Resolve only cited data; do not replace the rounded peak convention. Units: N/mm²."""
        peak_factor = data.number("concrete.peak_stress_factor")
        law = cls(
            peak_factor=peak_factor,
            peak_stress=peak_factor * fck_n_mm2,
            plateau_strain=data.number("concrete.plateau_strain"),
            ultimate_strain=data.number("concrete.ultimate_strain"),
        )
        if law.plateau_strain >= law.ultimate_strain:
            raise CodeDataError(
                "Concrete plateau must begin before the ultimate bending strain.",
                clause="38.1(b)/(c), Figures 21/22 — public-draft constitutive data",
                value=law.plateau_strain,
                limit={"less_than": law.ultimate_strain, "units": "strain"},
            )
        return law

    def stress(self, strain: float) -> float:
        """Evaluate compression; the input must not exceed ultimate strain. Units: N/mm²."""
        if strain <= 0:
            return 0.0  # Concrete tension is deliberately excluded from this ULS model.
        if strain > self.ultimate_strain:
            raise CodeDataError(
                "Concrete law evaluated beyond its ultimate strain.",
                clause="38.1(b) — constitutive evaluation domain",
                value=strain,
                limit=self.ultimate_strain,
            )
        if strain >= self.plateau_strain:
            return self.peak_stress
        ratio = strain / self.plateau_strain
        return self.peak_stress * ratio * (2 - ratio)

    def strip_integrals(self, x: float, start: float, end: float) -> tuple[float, float]:
        """Analytically integrate stress and stress*y over a unit-width strip. Units: N/mm, N.

        y is measured from the active compression face; strain varies linearly from
        ultimate at y=0 to zero at y=x. Segment bounds lie in 0..x. No quadrature grid
        or Annex G equivalent-block factor is used by this calculation.
        """
        plateau_end = x * (1 - self.plateau_strain / self.ultimate_strain)
        area = first_moment = 0.0
        plateau_stop = min(end, plateau_end)
        if start < plateau_stop:
            area = self.peak_stress * (plateau_stop - start)
            first_moment = area * (plateau_stop + start) / 2
        parabola_start = max(start, plateau_end)
        if parabola_start < end:
            k = self.ultimate_strain / self.plateau_strain
            u, v = (x - parabola_start) / x, (x - end) / x
            delta2, delta3, delta4 = u**2 - v**2, u**3 - v**3, u**4 - v**4
            area += self.peak_stress * x * (k * delta2 - k**2 * delta3 / 3)
            first_moment += (
                self.peak_stress
                * x**2
                * (k * delta2 - (2 * k + k**2) * delta3 / 3 + k**2 * delta4 / 4)
            )
        return area, first_moment


@dataclass(frozen=True)
class SteelLaw:
    """Design steel curve using fy/gamma consistently, without 0.87 rounding. Units: N/mm²."""

    fy: float
    elastic_modulus: float
    design_yield: float
    partial_factor: float
    minimum_plastic_tension_strain: float
    data: FlexureData

    @classmethod
    def load(cls, data: FlexureData, grade: str) -> SteelLaw:
        """Load the explicit grade; no grade substitutions. Units: N/mm² and strain."""
        fy = data.number(f"steel.{grade.lower()}.yield_strength", "N/mm²")
        partial_factor = data.number("steel.partial_factor")
        return cls(
            fy=fy,
            elastic_modulus=data.number("steel.elastic_modulus", "N/mm²"),
            design_yield=fy / partial_factor,
            partial_factor=partial_factor,
            minimum_plastic_tension_strain=data.number("steel.minimum_plastic_tension_strain"),
            data=data,
        )

    @property
    def minimum_tension_strain(self) -> float:
        """Derive the strain condition, not a rounded xu/d value. Units: strain."""
        return self.design_yield / self.elastic_modulus + self.minimum_plastic_tension_strain

    def stress(self, strain: float) -> float:
        """Interpolate DESIGN total strain, symmetric in sign; plateau thereafter. Units: N/mm²."""
        points = tuple(
            (ratio * self.design_yield / self.elastic_modulus + plastic, ratio * self.design_yield)
            for ratio, plastic in self.data.cold_worked_points
        )
        if points[-1][0] > self.minimum_tension_strain:
            raise CodeDataError(
                "Steel curve yield strain exceeds the declared ductility strain condition.",
                clause="38.1(e)/(f) — inconsistent public-draft curve data",
                value=points[-1][0],
                limit=self.minimum_tension_strain,
            )
        absolute = abs(strain)
        if absolute <= points[0][0]:
            return strain * self.elastic_modulus
        for (left_e, left_s), (right_e, right_s) in pairwise(points):
            if absolute <= right_e:
                stress = left_s + (absolute - left_e) * (right_s - left_s) / (right_e - left_e)
                return math.copysign(stress, strain)
        return math.copysign(self.design_yield, strain)
