"""Python-owned urgency and deadlines, always anchored to submission time."""

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Literal


Severity = Literal["high", "medium", "low"]


@dataclass(frozen=True)
class Priority:
    classified_severity: Severity | None
    effective_severity: Severity
    deadline_minutes: int
    brief_by_at: datetime
    severity_provisional: bool


def calculate_priority(
    created_at: datetime,
    classified_severity: object,
    has_violations: bool,
    *,
    provisional: bool = False,
) -> Priority:
    if created_at.tzinfo is None or created_at.utcoffset() is None:
        raise ValueError("Submission time must include a timezone.")
    severity = classified_severity if isinstance(classified_severity, str) and classified_severity in ("high", "medium", "low") else "high"
    effective = "high" if provisional or has_violations else severity
    minutes = {"high": 5, "medium": 15, "low": 30}[effective]
    return Priority(
        classified_severity=None if provisional else severity,
        effective_severity=effective,
        deadline_minutes=minutes,
        brief_by_at=created_at.astimezone(UTC) + timedelta(minutes=minutes),
        severity_provisional=provisional,
    )
