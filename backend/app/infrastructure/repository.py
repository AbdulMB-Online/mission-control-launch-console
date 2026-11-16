from __future__ import annotations

from datetime import datetime
from dataclasses import asdict
from decimal import Decimal
import json
from uuid import uuid4

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.domain.reports import Report
from app.domain.launch_rules import Violation
from app.domain.checks import CheckOutcome
from app.domain.briefings import Briefing
from app.infrastructure.models import BriefingRow, PipelineCheckRow, ReportRow, StepTraceRow
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
            pipeline_status=report.pipeline_status,
            error_code=report.error_code,
        )
        async with self.sessions() as session:
            session.add(row)
            await session.commit()

    async def get(self, report_id: str) -> Report | None:
        async with self.sessions() as session:
            row = await session.get(ReportRow, report_id)
            if row is None:
                return None
            checks = await self._load_checks(session, [report_id])
            briefings = await self._load_briefings(session, [report_id])
            return self._to_report(row, checks.get(report_id, ()), briefings.get(report_id, ()))

    async def list(self, limit: int, offset: int) -> tuple[list[Report], int]:
        async with self.sessions() as session:
            total = await session.scalar(select(func.count()).select_from(ReportRow))
            result = await session.scalars(
                select(ReportRow)
                .order_by(ReportRow.created_at.desc(), ReportRow.id.desc())
                .limit(limit)
                .offset(offset)
            )
            rows = result.all()
            checks = await self._load_checks(session, [row.id for row in rows])
            briefings = await self._load_briefings(session, [row.id for row in rows])
            return [self._to_report(row, checks.get(row.id, ()), briefings.get(row.id, ())) for row in rows], total or 0

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

    async def update_checks(self, report: Report, traces: list[ModelTrace]) -> None:
        # Persist each outcome as its own row, including failures. No model call
        # is awaited inside this transaction and no safety/approval column is writable.
        async with self.sessions() as session:
            await session.execute(update(ReportRow).where(ReportRow.id == report.id).values(
                requires_review=report.requires_review, review_reasons_json=json.dumps(report.review_reasons),
            ))
            for check in report.checks:
                session.add(PipelineCheckRow(
                    id=str(uuid4()), report_id=report.id, kind=check.kind, status=check.status,
                    flagged=check.flagged, details_json=json.dumps(check.details), error_code=check.error_code,
                ))
            for trace in traces:
                values = asdict(trace)
                for field in ("started_at", "finished_at"):
                    values[field] = values[field].isoformat(timespec="microseconds").replace("+00:00", "Z")
                session.add(StepTraceRow(**values))
            await session.commit()

    async def update_briefings(self, report: Report, trace: ModelTrace | None = None) -> None:
        async with self.sessions() as session:
            await session.execute(update(ReportRow).where(ReportRow.id == report.id).values(
                pipeline_status=report.pipeline_status, error_code=report.error_code,
                requires_review=report.requires_review, review_reasons_json=json.dumps(report.review_reasons),
            ))
            for item in report.briefings:
                row = await session.get(BriefingRow, item.id)
                if row is None:
                    row = BriefingRow(
                        id=item.id, report_id=report.id, round_number=item.round_number,
                        summary=item.summary, actions_json=json.dumps(item.recommended_actions),
                        created_at=item.created_at.isoformat(timespec="microseconds").replace("+00:00", "Z"),
                    )
                    session.add(row)
                elif row.report_id != report.id or row.round_number != item.round_number:
                    raise ValueError("Briefing does not belong to this report/round.")
                # Stored draft text and creation metadata remain immutable.
                row.evaluation_status = item.evaluation_status
                row.feedback_json = json.dumps(item.feedback)
                row.evaluated_at = item.evaluated_at.isoformat(timespec="microseconds").replace("+00:00", "Z") if item.evaluated_at else None
                row.is_selected = item.is_selected
            if trace is not None:
                values = asdict(trace)
                for field in ("started_at", "finished_at"):
                    values[field] = values[field].isoformat(timespec="microseconds").replace("+00:00", "Z")
                session.add(StepTraceRow(**values))
            await session.commit()

    @staticmethod
    async def _load_briefings(session, report_ids):
        if not report_ids:
            return {}
        rows = await session.scalars(select(BriefingRow).where(
            BriefingRow.report_id.in_(report_ids),
        ).order_by(BriefingRow.round_number))
        by_report = {}
        for row in rows:
            by_report.setdefault(row.report_id, []).append(Briefing(
                id=row.id, round_number=row.round_number, summary=row.summary,
                recommended_actions=tuple(json.loads(row.actions_json)),
                created_at=datetime.fromisoformat(row.created_at.replace("Z", "+00:00")),
                evaluation_status=row.evaluation_status, feedback=tuple(json.loads(row.feedback_json)),
                evaluated_at=datetime.fromisoformat(row.evaluated_at.replace("Z", "+00:00")) if row.evaluated_at else None,
                is_selected=row.is_selected,
            ))
        return {key: tuple(value) for key, value in by_report.items()}

    @staticmethod
    async def _load_checks(session, report_ids):
        if not report_ids:
            return {}
        rows = await session.scalars(select(PipelineCheckRow).where(
            PipelineCheckRow.report_id.in_(report_ids),
        ).order_by(PipelineCheckRow.kind))
        by_report = {}
        for row in rows:
            by_report.setdefault(row.report_id, []).append(CheckOutcome(
                kind=row.kind, status=row.status, flagged=row.flagged,
                details=json.loads(row.details_json), error_code=row.error_code,
            ))
        return {key: tuple(value) for key, value in by_report.items()}

    @staticmethod
    def _to_report(row: ReportRow, checks=(), briefings=()) -> Report:
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
            checks=checks,
            pipeline_status=row.pipeline_status,
            error_code=row.error_code,
            briefings=briefings,
        )
