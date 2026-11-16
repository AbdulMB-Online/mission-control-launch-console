import asyncio
from collections.abc import Callable
from dataclasses import asdict, replace
from datetime import UTC, datetime
from uuid import uuid4

from pydantic import ValidationError

from app.application.ai_schemas import Classification
from app.application.llm import LLMRequest, LLMResult, ModelTrace, token_usage
from app.application.ports import LLMGateway, ReportStore
from app.application.prompts import CLASSIFICATION_PROMPT_VERSION, CLASSIFICATION_SYSTEM
from app.domain.launch_rules import assess_launch
from app.domain.reports import Report, ReportInput
from app.domain.severity import calculate_priority


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
        priority = calculate_priority(created_at, None, bool(decision.violations), provisional=True)
        report = Report(
            **asdict(submission), id=str(uuid4()), created_at=created_at,
            verdict=decision.verdict, violations=decision.violations, rule_version=decision.rule_version,
            **asdict(priority),
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

    async def resolve_priority(self, report_id: str, classified_severity: object) -> Report:
        report = await self.get(report_id)
        priority = calculate_priority(report.created_at, classified_severity, bool(report.violations))
        resolved = replace(report, **asdict(priority))
        await self.store.update_priority(resolved)
        return resolved

    async def classify(self, report_id: str, gateway: LLMGateway) -> Report:
        report = await self.get(report_id)
        if report.classification_status != "not_run":
            return report
        request = LLMRequest(
            stage="classification", round_number=None, system_prompt=CLASSIFICATION_SYSTEM,
            data={"report": {
                "engineer_name": report.engineer_name, "station": report.station, "note": report.note,
                "wind_knots": format(report.wind_knots, "f"), "temp_c": format(report.temp_c, "f"),
                "fuel_pct": format(report.fuel_pct, "f"),
            }},
            schema=Classification.model_json_schema(), max_output_tokens=300,
            prompt_version=CLASSIFICATION_PROMPT_VERSION,
        )
        started_at = self.clock()
        try:
            async with asyncio.timeout(30):
                response = await gateway.generate(request)
        except TimeoutError:
            response = LLMResult(provider=getattr(gateway, "provider", "unknown"), status="error", error_code="timeout")
        except Exception:
            response = LLMResult(provider=getattr(gateway, "provider", "unknown"), status="error", error_code="provider_error")

        classified = None
        code = None
        if response.status == "completed":
            try:
                classified = Classification.model_validate(response.payload)
            except ValidationError:
                code = "invalid_output"
        else:
            allowed = {"refusal", "incomplete", "invalid_output", "timeout", "provider_error",
                       "authentication_error", "rate_limited", "transport_error"}
            code = response.error_code if response.error_code in allowed else "provider_error"

        priority = calculate_priority(report.created_at, classified.severity if classified else "high", bool(report.violations))
        reasons = tuple(dict.fromkeys((*report.review_reasons, *((f"classification_{code}",) if code else ()))))
        resolved = replace(
            report, **asdict(priority), subsystem=classified.subsystem if classified else "unknown",
            classification_status="completed" if classified else "fallback",
            classification_rationale=classified.rationale if classified else "Classification unavailable; human review required.",
            requires_review=report.requires_review or bool(code), review_reasons=reasons,
        )
        usage = token_usage(response.input_tokens, response.cached_input_tokens, response.output_tokens)
        trace = ModelTrace(
            id=str(uuid4()), report_id=report.id, step_key="classification", display_order=30,
            status="error" if code else "completed", started_at=started_at, finished_at=self.clock(),
            provider=response.provider, model=response.model, prompt_version=request.prompt_version,
            provider_response_id=response.response_id, error_code=code, **usage,
        )
        await self.store.update_classification(resolved, trace)
        return resolved
