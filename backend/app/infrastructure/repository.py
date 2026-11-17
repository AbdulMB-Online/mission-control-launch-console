from __future__ import annotations

from datetime import UTC, datetime
from dataclasses import asdict
from decimal import Decimal
import json
from uuid import uuid4

from sqlalchemy import func, select, text, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.domain.reports import Report
from app.domain.launch_rules import Violation
from app.domain.checks import CheckOutcome
from app.domain.briefings import Briefing
from app.domain.approvals import Approval, ApprovalRejected, ensure_approvable
from app.infrastructure.models import ApprovalRow, BriefingRow, PipelineCheckRow, ReportRow, StepTraceRow
from app.application.llm import ModelTrace
from app.domain import costs


class SQLAlchemyReportStore:
    def __init__(self, sessions: async_sessionmaker[AsyncSession]):
        self.sessions = sessions

    async def start_traces(self, traces):
        async with self.sessions() as session:
            for trace in traces:
                await self._write_trace(session, trace)
            await session.commit()

    async def finish_trace(self, trace):
        async with self.sessions() as session:
            await self._write_trace(session, trace)
            await session.commit()

    @staticmethod
    async def _write_trace(session, trace):
        row = await session.get(StepTraceRow, trace.id)
        if row is not None and row.status != "running":
            return  # A second persistence pass cannot reprice or double-count.
        values = asdict(trace)
        for field in ("started_at", "finished_at"):
            value = values[field]
            values[field] = value.isoformat(timespec="microseconds").replace("+00:00", "Z") if value else None
        rate = None
        if row is not None and row.rate_snapshot_json:
            saved = json.loads(row.rate_snapshot_json)
            rate = costs.RateSnapshot(**{**saved, **{key: Decimal(saved[key]) for key in (
                "input_per_million", "cached_input_per_million", "output_per_million")}})
        if rate is None or rate.model != trace.model:
            rate = costs.get_rate(trace.provider, trace.model)
        amount = None if trace.status == "running" else costs.calculate_cost(
            trace.provider, trace.model, trace.input_tokens, trace.cached_input_tokens, trace.output_tokens, rate)
        values.update(cost_usd=format(amount, "f") if amount is not None else None,
                      rate_snapshot_json=json.dumps(rate.to_dict()) if rate else None)
        if row is None:
            session.add(StepTraceRow(**values))
        else:
            for key, value in values.items():
                setattr(row, key, value)

    async def list_traces(self, report_id):
        async with self.sessions() as session:
            rows = await session.scalars(select(StepTraceRow).where(
                StepTraceRow.report_id == report_id).order_by(StepTraceRow.display_order, StepTraceRow.id))
            return [{
                **{column.name: getattr(row, column.name) for column in StepTraceRow.__table__.columns
                   if column.name != "rate_snapshot_json"},
                "rate_snapshot": json.loads(row.rate_snapshot_json) if row.rate_snapshot_json else None,
            } for row in rows]

    async def save(self, report: Report, traces=()) -> None:
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
            await session.flush()
            for trace in traces:
                await self._write_trace(session, trace)
            await session.commit()

    async def get(self, report_id: str) -> Report | None:
        async with self.sessions() as session:
            row = await session.get(ReportRow, report_id)
            if row is None:
                return None
            checks = await self._load_checks(session, [report_id])
            briefings = await self._load_briefings(session, [report_id])
            approvals = await self._load_approvals(session, [report_id])
            return self._to_report(row, checks.get(report_id, ()), briefings.get(report_id, ()), approvals.get(report_id))

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
            approvals = await self._load_approvals(session, [row.id for row in rows])
            return [self._to_report(row, checks.get(row.id, ()), briefings.get(row.id, ()), approvals.get(row.id)) for row in rows], total or 0

    async def update_priority(self, report: Report, trace=None) -> None:
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
            if trace is not None:
                await self._write_trace(session, trace)
            await session.commit()

    async def update_classification(self, report: Report, trace: ModelTrace, priority_trace: ModelTrace) -> None:
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
            await self._write_trace(session, trace)
            await self._write_trace(session, priority_trace)
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
                await self._write_trace(session, trace)
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
                await self._write_trace(session, trace)
            await session.commit()

    async def recover_pipeline(self) -> list[str]:
        async with self.sessions() as session:
            interrupted = (await session.scalars(select(ReportRow.id).where(
                ReportRow.pipeline_status == "processing",
            ))).all()
            for report_id in interrupted:
                await self._mark_failed(session, report_id, "interrupted")
            queued = (await session.scalars(select(ReportRow.id).where(
                ReportRow.pipeline_status == "queued",
            ).order_by(ReportRow.created_at, ReportRow.id))).all()
            await session.commit()
            return list(queued)

    async def approve_briefing(self, report_id, briefing_id, director, acknowledge_review, approved_at) -> Approval:
        async with self.sessions() as session:
            # Reserve the SQLite writer before reading eligibility. Concurrent
            # requests see the committed approval instead of upgrading stale
            # read snapshots. Unique constraints remain a final duplicate guard.
            await session.execute(text("BEGIN IMMEDIATE"))
            row = await session.get(ReportRow, report_id)
            report = None
            if row is not None:
                briefings = await self._load_briefings(session, [report_id])
                approvals = await self._load_approvals(session, [report_id])
                report = self._to_report(row, briefings=briefings.get(report_id, ()), approval=approvals.get(report_id))
            exists = await session.scalar(select(BriefingRow.id).where(BriefingRow.id == briefing_id))
            ensure_approvable(report, briefing_id, exists is not None, acknowledge_review)
            approval = Approval(str(uuid4()), report_id, briefing_id, director, approved_at,
                                acknowledge_review, tuple(report.review_reasons))
            timestamp = approved_at.isoformat(timespec="microseconds").replace("+00:00", "Z")
            session.add(ApprovalRow(
                id=approval.id, report_id=report_id, briefing_id=briefing_id, approved_by=director,
                approved_at=timestamp, review_acknowledged=acknowledge_review,
                review_reasons_snapshot_json=json.dumps(approval.review_reasons_snapshot),
            ))
            session.add(StepTraceRow(
                id=str(uuid4()), report_id=report_id, step_key="approval", display_order=300,
                status="completed", started_at=timestamp, finished_at=timestamp, provider="human",
                model=None, prompt_version="human-approval-v1", provider_response_id=None,
                input_tokens=0, cached_input_tokens=0, output_tokens=0, usage_status="reported",
                error_code=None, parallel_group=None, round_number=None, cost_usd="0", rate_snapshot_json=None,
            ))
            try:
                await session.commit()
            except IntegrityError:
                await session.rollback()
                raise ApprovalRejected("already_approved", "This briefing has already been approved.") from None
            return approval

    @staticmethod
    async def _load_approvals(session, report_ids):
        if not report_ids:
            return {}
        rows = await session.scalars(select(ApprovalRow).where(ApprovalRow.report_id.in_(report_ids)))
        return {row.report_id: Approval(
            id=row.id, report_id=row.report_id, briefing_id=row.briefing_id,
            approved_by=row.approved_by, approved_at=datetime.fromisoformat(row.approved_at.replace("Z", "+00:00")),
            review_acknowledged=row.review_acknowledged,
            review_reasons_snapshot=tuple(json.loads(row.review_reasons_snapshot_json)),
        ) for row in rows}

    async def claim_pipeline(self, report_id: str) -> bool:
        async with self.sessions() as session:
            result = await session.execute(update(ReportRow).where(
                ReportRow.id == report_id, ReportRow.pipeline_status == "queued",
            ).values(pipeline_status="processing", error_code=None))
            await session.commit()
            return result.rowcount == 1

    async def fail_pipeline(self, report_id: str, code: str) -> None:
        async with self.sessions() as session:
            await self._mark_failed(session, report_id, code)
            await session.commit()

    @staticmethod
    async def _mark_failed(session, report_id, code):
        row = await session.get(ReportRow, report_id)
        if row is None or row.pipeline_status != "processing":
            return
        row.pipeline_status = "failed"
        row.error_code = code
        row.requires_review = True
        reason = "pipeline_interrupted" if code == "interrupted" else code
        row.review_reasons_json = json.dumps(list(dict.fromkeys((*json.loads(row.review_reasons_json), reason))))
        await session.execute(update(BriefingRow).where(BriefingRow.report_id == report_id).values(is_selected=False))
        await session.execute(update(StepTraceRow).where(
            StepTraceRow.report_id == report_id, StepTraceRow.status == "running",
        ).values(status="error", error_code=code,
                 finished_at=datetime.now(UTC).isoformat(timespec="microseconds").replace("+00:00", "Z"),
                 input_tokens=None, cached_input_tokens=None, output_tokens=None, usage_status="unavailable", cost_usd=None))

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
    def _to_report(row: ReportRow, checks=(), briefings=(), approval=None) -> Report:
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
            approval=approval,
        )
