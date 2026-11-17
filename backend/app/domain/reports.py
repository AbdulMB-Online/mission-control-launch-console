from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Literal

from app.domain.launch_rules import Verdict, Violation
from app.domain.severity import Severity
from app.domain.checks import CheckOutcome
from app.domain.briefings import Briefing
from app.domain.approvals import Approval


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
    pipeline_status: Literal["queued", "processing", "completed", "failed"] = "queued"
    error_code: str | None = None
    briefings: tuple[Briefing, ...] = ()
    approval: Approval | None = None

    @property
    def selected_briefing_id(self) -> str | None:
        return next((item.id for item in self.briefings if item.is_selected), None)

    @property
    def approval_state(self) -> Literal["unavailable", "pending", "approved"]:
        if self.approval is not None:
            return "approved"
        # Evaluator acceptance can select a draft, never create this record.
        return "pending" if self.pipeline_status == "completed" and self.selected_briefing_id else "unavailable"
