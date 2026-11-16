from datetime import datetime
from dataclasses import asdict
from decimal import Decimal
import json

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.domain.reports import Report
from app.domain.launch_rules import Violation
from app.infrastructure.models import ReportRow, StepTraceRow
from app.application.llm import ModelTrace


class SQLAlchemyReportStore:
    def __init__(self, sessions: async_sessionmaker[AsyncSession]):
        self.sessions = sessions

    async def save(self, report: Report) -> None:
        row = ReportRow(
            id=report.id,
            engineer_name=report.engineer_name,
            station=report.station,
            wind_knots=format(report.wind_knots, "f"),
            temp_c=format(report.temp_c, "f"),
            fuel_pct=format(report.fuel_pct, "f"),
            note=report.note,
            created_at=report.created_at.isoformat(timespec="microseconds").replace("+00:00", "Z"),
            verdict=report.verdict,
            violations_json=json.dumps([
                {"field": item.field, "observed": format(item.observed, "f"), "operator": item.operator,
                 "limit": format(item.limit, "f"), "message": item.message}
                for item in report.violations
            ]),
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
            review_reasons_json=json.dumps(report.review_reasons),
        )
        async with self.sessions() as session:
            session.add(row)
            await session.commit()

    async def get(self, report_id: str) -> Report | None:
        async with self.sessions() as session:
            row = await session.get(ReportRow, report_id)
            return self._to_report(row) if row is not None else None

    async def list(self, limit: int, offset: int) -> tuple[list[Report], int]:
        async with self.sessions() as session:
            total = await session.scalar(select(func.count()).select_from(ReportRow))
            rows = await session.scalars(
                select(ReportRow)
                .order_by(ReportRow.created_at.desc(), ReportRow.id.desc())
                .limit(limit)
                .offset(offset)
            )
            return [self._to_report(row) for row in rows], total or 0

    async def update_priority(self, report: Report) -> None:
        # Classification can update only priority, never the submitted readings,
        # Python verdict, violations, identity or original timestamp.
        async with self.sessions() as session:
            await session.execute(update(ReportRow).where(ReportRow.id == report.id).values(
                classified_severity=report.classified_severity,
                effective_severity=report.effective_severity,
                deadline_minutes=report.deadline_minutes,
                brief_by_at=report.brief_by_at.isoformat(timespec="microseconds").replace("+00:00", "Z"),
                severity_provisional=report.severity_provisional,
            ))
            await session.commit()

    async def update_classification(self, report: Report, trace: ModelTrace) -> None:
        # One short transaction after the model call. It cannot update launch
        # readings, verdict, violations, timestamps, identity or human approval.
        async with self.sessions() as session:
            await session.execute(update(ReportRow).where(ReportRow.id == report.id).values(
                subsystem=report.subsystem, classification_status=report.classification_status,
                classification_rationale=report.classification_rationale,
                requires_review=report.requires_review, review_reasons_json=json.dumps(report.review_reasons),
                classified_severity=report.classified_severity, effective_severity=report.effective_severity,
                deadline_minutes=report.deadline_minutes,
                brief_by_at=report.brief_by_at.isoformat(timespec="microseconds").replace("+00:00", "Z"),
                severity_provisional=report.severity_provisional,
            ))
            values = asdict(trace)
            for field in ("started_at", "finished_at"):
                values[field] = values[field].isoformat(timespec="microseconds").replace("+00:00", "Z")
            session.add(StepTraceRow(**values))
            await session.commit()

    @staticmethod
    def _to_report(row: ReportRow) -> Report:
        return Report(
            id=row.id,
            engineer_name=row.engineer_name,
            station=row.station,
            wind_knots=Decimal(row.wind_knots),
            temp_c=Decimal(row.temp_c),
            fuel_pct=Decimal(row.fuel_pct),
            note=row.note,
            created_at=datetime.fromisoformat(row.created_at.replace("Z", "+00:00")),
            verdict=row.verdict,
            violations=tuple(
                Violation(
                    field=item["field"], observed=Decimal(item["observed"]), operator=item["operator"],
                    limit=Decimal(item["limit"]), message=item["message"],
                ) for item in json.loads(row.violations_json)
            ),
            rule_version=row.rule_version,
            classified_severity=row.classified_severity,
            effective_severity=row.effective_severity,
            deadline_minutes=row.deadline_minutes,
            brief_by_at=datetime.fromisoformat(row.brief_by_at.replace("Z", "+00:00")),
            severity_provisional=row.severity_provisional,
            subsystem=row.subsystem,
            classification_status=row.classification_status,
            classification_rationale=row.classification_rationale,
            requires_review=row.requires_review,
            review_reasons=tuple(json.loads(row.review_reasons_json)),
        )
