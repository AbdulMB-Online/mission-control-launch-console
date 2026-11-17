from decimal import Decimal
import re
from typing import Annotated, Literal

from pydantic import BaseModel, BeforeValidator, ConfigDict, Field, StringConstraints

from app.domain.reports import Report, ReportInput
from app.domain.launch_rules import Verdict
from app.domain.severity import Severity
from app.application.ai_schemas import Subsystem
from app.domain.checks import CheckKind


def parse_reading(value: object) -> Decimal:
    if not isinstance(value, str) or re.fullmatch(r"-?[0-9]{1,6}(?:\.[0-9]{1,3})?", value) is None:
        raise ValueError("Use decimal text with up to six integer digits and three decimal places.")
    return Decimal(value)


Reading = Annotated[Decimal, BeforeValidator(parse_reading)]


class ReportCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    engineer_name: Annotated[str, StringConstraints(strict=True, strip_whitespace=True, min_length=1, max_length=100)]
    station: Annotated[str, StringConstraints(strict=True, strip_whitespace=True, min_length=1, max_length=50)]
    wind_knots: Annotated[Reading, Field(ge=0)]
    temp_c: Reading
    fuel_pct: Annotated[Reading, Field(ge=0)]
    note: Annotated[str, StringConstraints(strict=True, strip_whitespace=True, min_length=1, max_length=4000)]

    def to_submission(self) -> ReportInput:
        return ReportInput(**self.model_dump())


class ViolationRead(BaseModel):
    field: str
    observed: str
    operator: str
    limit: str
    message: str


class CheckRead(BaseModel):
    kind: CheckKind
    status: Literal["completed", "error"]
    flagged: bool | None
    details: dict[str, object]
    error_code: str | None


class BriefingRead(BaseModel):
    id: str
    round_number: int
    summary: str
    recommended_actions: list[str]
    created_at: str
    evaluation_status: Literal["pending", "accepted", "needs_revision", "error"]
    feedback: list[str]
    evaluated_at: str | None
    is_selected: bool


class ReportRead(BaseModel):
    id: str
    engineer_name: str
    station: str
    wind_knots: str
    temp_c: str
    fuel_pct: str
    note: str
    created_at: str
    verdict: Verdict
    violations: list[ViolationRead]
    rule_version: str
    classified_severity: Severity | None
    effective_severity: Severity
    deadline_minutes: int
    brief_by_at: str
    severity_provisional: bool
    subsystem: Subsystem
    classification_status: Literal["not_run", "completed", "fallback"]
    classification_rationale: str
    requires_review: bool
    review_reasons: list[str]
    checks: list[CheckRead]
    pipeline_status: Literal["queued", "processing", "completed", "failed"]
    error_code: str | None
    briefings: list[BriefingRead]
    selected_briefing_id: str | None
    approval_state: Literal["unavailable", "pending"]

    @classmethod
    def from_report(cls, report: Report) -> "ReportRead":
        return cls(
            id=report.id,
            engineer_name=report.engineer_name,
            station=report.station,
            wind_knots=format(report.wind_knots, "f"),
            temp_c=format(report.temp_c, "f"),
            fuel_pct=format(report.fuel_pct, "f"),
            note=report.note,
            created_at=report.created_at.isoformat(timespec="microseconds").replace("+00:00", "Z"),
            verdict=report.verdict,
            violations=[ViolationRead(
                field=item.field, observed=format(item.observed, "f"), operator=item.operator,
                limit=format(item.limit, "f"), message=item.message,
            ) for item in report.violations],
            rule_version=report.rule_version,
            classified_severity=report.classified_severity,
            effective_severity=report.effective_severity,
            deadline_minutes=report.deadline_minutes,
            brief_by_at=report.brief_by_at.isoformat(timespec="microseconds").replace("+00:00", "Z"),
            severity_provisional=report.severity_provisional,
            subsystem=report.subsystem,
            classification_status=report.classification_status,
            classification_rationale=report.classification_rationale,
            requires_review=report.requires_review,
            review_reasons=list(report.review_reasons),
            checks=[CheckRead(kind=item.kind, status=item.status, flagged=item.flagged,
                              details=item.details, error_code=item.error_code) for item in report.checks],
            pipeline_status=report.pipeline_status,
            error_code=report.error_code,
            briefings=[BriefingRead(
                id=item.id, round_number=item.round_number, summary=item.summary,
                recommended_actions=list(item.recommended_actions),
                created_at=item.created_at.isoformat(timespec="microseconds").replace("+00:00", "Z"),
                evaluation_status=item.evaluation_status, feedback=list(item.feedback),
                evaluated_at=item.evaluated_at.isoformat(timespec="microseconds").replace("+00:00", "Z") if item.evaluated_at else None,
                is_selected=item.is_selected,
            ) for item in report.briefings],
            selected_briefing_id=report.selected_briefing_id,
            approval_state=report.approval_state,
        )


class ReportPage(BaseModel):
    items: list[ReportRead]
    total: int
    limit: int
    offset: int
