from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Literal

from app.domain.launch_rules import Verdict, Violation
from app.domain.severity import Severity
from app.domain.checks import CheckOutcome


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
    classified_severity: Severity | None
    effective_severity: Severity
    deadline_minutes: int
    brief_by_at: datetime
    severity_provisional: bool
    subsystem: str = "unknown"
    classification_status: Literal["not_run", "completed", "fallback"] = "not_run"
    classification_rationale: str = ""
    requires_review: bool = False
    review_reasons: tuple[str, ...] = ()
    checks: tuple[CheckOutcome, ...] = ()
