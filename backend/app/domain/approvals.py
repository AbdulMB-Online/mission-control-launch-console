from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class Approval:
    id: str
    report_id: str
    briefing_id: str
    approved_by: str
    approved_at: datetime
    review_acknowledged: bool
    review_reasons_snapshot: tuple[str, ...]


class ApprovalRejected(Exception):
    def __init__(self, code: str, message: str, status_code: int = 409):
        super().__init__(message)
        self.code, self.message, self.status_code = code, message, status_code


def ensure_approvable(report, briefing_id: str, briefing_exists: bool, acknowledge_review: bool):
    if report is None:
        raise ApprovalRejected("report_not_found", "Report not found.", 404)
    if report.approval is not None:
        raise ApprovalRejected("already_approved", "This briefing has already been approved.")
    if report.pipeline_status != "completed" or report.selected_briefing_id is None:
        raise ApprovalRejected("approval_ineligible", "A completed pipeline with a selected valid briefing is required.")
    if not briefing_exists:
        raise ApprovalRejected("briefing_not_found", "Briefing not found.", 404)
    if briefing_id != report.selected_briefing_id:
        raise ApprovalRejected("approval_ineligible", "Only this report's selected briefing can be approved.")
    if (report.requires_review or report.review_reasons) and not acknowledge_review:
        raise ApprovalRejected("review_acknowledgment_required", "Acknowledge the flagged findings before approving this briefing.")
