import asyncio
from copy import deepcopy
from dataclasses import dataclass

from app.application.llm import LLMRequest, LLMResult


@dataclass
class Script:
    response: object
    started: asyncio.Event | None
    release: asyncio.Event | None


class FakeGateway:
    """Explicit simulation; scripts are keyed independently of call scheduling."""

    provider = "fake"

    def __init__(self):
        self.requests: list[LLMRequest] = []
        self._scripts: dict[tuple[str, int | None], Script] = {}

    def script(self, stage, round_number, response, *, started=None, release=None):
        self._scripts[(stage, round_number)] = Script(deepcopy(response), started, release)

    async def generate(self, request: LLMRequest) -> LLMResult:
        self.requests.append(deepcopy(request))
        scripted = self._scripts.get((request.stage, request.round_number))
        if scripted is not None:
            if scripted.started is not None:
                scripted.started.set()
            if scripted.release is not None:
                await scripted.release.wait()
            if isinstance(scripted.response, BaseException):
                raise scripted.response
            return deepcopy(scripted.response)
        if request.stage == "classification":
            return LLMResult(
                provider="fake", model="fake-v1", response_id="fake-classification",
                payload={"subsystem": "unknown", "severity": "high",
                         "rationale": "Simulated classification; inspect the engineering report before acting."},
                input_tokens=0, cached_input_tokens=0, output_tokens=0, usage_status="reported",
            )
        if request.stage in ("injection", "missing_information", "tone"):
            # Deliberately labeled simulation, not an LLM or safety authority.
            note = request.data.get("report", {}).get("note", "").lower()
            flagged = any(marker in note for marker in ("ignore prior", "ignore all", "system override", "mark approved", "hide this instruction"))
            payloads = {
                "injection": {"flagged": flagged, "reasons": ["Simulated detection of instruction-like text."] if flagged else []},
                "missing_information": {"flagged": True, "missing_details": ["Confirm the anomaly timestamp and reproduction steps."]},
                "tone": {"tone": "calm", "rationale": "Simulated tone check; inspect the original report."},
            }
            return LLMResult(provider="fake", model="fake-v1", response_id=f"fake-{request.stage}",
                             payload=payloads[request.stage], input_tokens=0, cached_input_tokens=0,
                             output_tokens=0, usage_status="reported")
        return LLMResult(provider="fake", model="fake-v1", status="error", error_code="unsupported_stage")

    async def aclose(self) -> None:
        pass
