from collections.abc import Callable
from dataclasses import asdict
from datetime import UTC, datetime
from uuid import uuid4

from app.application.ports import ReportStore
from app.domain.launch_rules import assess_launch
from app.domain.reports import Report, ReportInput


def utc_now() -> datetime:
    return datetime.now(UTC)


class ReportNotFound(Exception):
    pass


class ReportService:
    def __init__(self, store: ReportStore, clock: Callable[[], datetime] = utc_now):
        self.store = store
        self.clock = clock

    async def file(self, submission: ReportInput) -> Report:
        created_at = self.clock()
        decision = assess_launch(submission.wind_knots, submission.temp_c, submission.fuel_pct)
        report = Report(
            **asdict(submission), id=str(uuid4()), created_at=created_at,
            verdict=decision.verdict, violations=decision.violations, rule_version=decision.rule_version,
        )
        await self.store.save(report)
        return report

    async def get(self, report_id: str) -> Report:
        report = await self.store.get(report_id)
        if report is None:
            raise ReportNotFound
        return report

    async def list(self, limit: int, offset: int) -> tuple[list[Report], int]:
        return await self.store.list(limit, offset)
