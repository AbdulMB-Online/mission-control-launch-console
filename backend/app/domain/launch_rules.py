"""Launch limits v1: exact comparisons, independent of models and report text."""

from dataclasses import dataclass
from decimal import Decimal
from typing import Literal


Verdict = Literal["go", "no_go"]


@dataclass(frozen=True)
class Violation:
    field: str
    observed: Decimal
    operator: Literal["<=", ">="]
    limit: Decimal
    message: str


@dataclass(frozen=True)
class LaunchDecision:
    verdict: Verdict
    violations: tuple[Violation, ...]
    rule_version: str = "v1"


def assess_launch(wind_knots: Decimal, temp_c: Decimal, fuel_pct: Decimal) -> LaunchDecision:
    violations = []
    if wind_knots > Decimal("25"):
        violations.append(Violation("wind_knots", wind_knots, "<=", Decimal("25"), "Wind must be at most 25 knots."))
    if temp_c < Decimal("4"):
        violations.append(Violation("temp_c", temp_c, ">=", Decimal("4"), "Temperature must be at least 4°C."))
    if fuel_pct < Decimal("98"):
        violations.append(Violation("fuel_pct", fuel_pct, ">=", Decimal("98"), "Fuel must be at least 98%."))
    if fuel_pct > Decimal("100"):
        violations.append(Violation("fuel_pct", fuel_pct, "<=", Decimal("100"), "Fuel must be at most 100%."))
    return LaunchDecision("no_go" if violations else "go", tuple(violations))
