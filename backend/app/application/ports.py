from typing import Protocol

from app.domain.reports import Report


class ReportStore(Protocol):
    async def save(self, report: Report) -> None: ...

    async def get(self, report_id: str) -> Report | None: ...

    async def list(self, limit: int, offset: int) -> tuple[list[Report], int]: ...
