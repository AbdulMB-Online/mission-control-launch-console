from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, StringConstraints

from app.domain.severity import Severity


Subsystem = Literal["propulsion", "avionics", "telemetry", "structures", "environment", "ground_operations", "unknown"]


class Classification(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    subsystem: Subsystem
    severity: Severity
    rationale: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=500)]
