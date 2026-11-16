from dataclasses import dataclass
from typing import Literal


CheckKind = Literal["injection", "missing_information", "tone"]


@dataclass(frozen=True)
class CheckOutcome:
    kind: CheckKind
    status: Literal["completed", "error"]
    flagged: bool | None
    details: dict[str, object]
    error_code: str | None = None
