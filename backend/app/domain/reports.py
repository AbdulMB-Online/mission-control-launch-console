from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from app.domain.launch_rules import Verdict, Violation


@dataclass(frozen=True)
class ReportInput:
    engineer_name: str
    station: str
    wind_knots: Decimal
    temp_c: Decimal
    fuel_pct: Decimal
    note: str


@dataclass(frozen=True)
class Report(ReportInput):
    id: str
    created_at: datetime
    verdict: Verdict
    violations: tuple[Violation, ...]
    rule_version: str
