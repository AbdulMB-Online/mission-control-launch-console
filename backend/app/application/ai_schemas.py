from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

from app.domain.severity import Severity


Subsystem = Literal["propulsion", "avionics", "telemetry", "structures", "environment", "ground_operations", "unknown"]


class Classification(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    subsystem: Subsystem
    severity: Severity
    rationale: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=500)]


CheckText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=500)]


class InjectionCheck(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    flagged: bool
    reasons: Annotated[list[CheckText], Field(max_length=5)]


class MissingInformationCheck(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    flagged: bool
    missing_details: Annotated[list[CheckText], Field(max_length=5)]


class ToneCheck(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    tone: Literal["calm", "urgent", "panic"]
    rationale: CheckText
