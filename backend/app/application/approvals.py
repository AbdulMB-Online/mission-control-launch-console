from collections.abc import Callable
from datetime import UTC, datetime

from app.application.ports import HumanApprovalStore
from app.domain.approvals import Approval


class ApprovalService:
    def __init__(self, store: HumanApprovalStore, clock: Callable[[], datetime] | None = None):
        self.store = store
        self.clock = clock or (lambda: datetime.now(UTC))

    async def approve(self, report_id: str, briefing_id: str, director: str, acknowledge_review: bool) -> Approval:
        return await self.store.approve_briefing(report_id, briefing_id, director, acknowledge_review, self.clock())
