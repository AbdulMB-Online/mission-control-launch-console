from dataclasses import dataclass
from datetime import datetime
from typing import Literal


@dataclass(frozen=True)
class Briefing:
    id: str
    round_number: int
    summary: str
    recommended_actions: tuple[str, ...]
    created_at: datetime
    evaluation_status: Literal["pending", "accepted", "needs_revision", "error"] = "pending"
    feedback: tuple[str, ...] = ()
    evaluated_at: datetime | None = None
    is_selected: bool = False
