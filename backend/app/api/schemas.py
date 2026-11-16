from decimal import Decimal
import re
from typing import Annotated

from pydantic import BaseModel, BeforeValidator, ConfigDict, Field, StringConstraints

from app.domain.reports import Report, ReportInput
from app.domain.launch_rules import Verdict
from app.domain.severity import Severity


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
        )


class ReportPage(BaseModel):
    items: list[ReportRead]
    total: int
    limit: int
    offset: int
