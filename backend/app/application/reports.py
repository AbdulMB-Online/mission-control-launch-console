from collections.abc import Callable
from dataclasses import asdict, replace
from datetime import UTC, datetime
from uuid import uuid4

from pydantic import ValidationError

from app.application.ai_schemas import Classification
from app.application.llm import LLMRequest, guarded_generate, model_error, token_usage, running_trace, python_trace
from app.domain.costs import summarize_traces
from app.application.ports import LLMGateway, ReportStore
from app.application.prompts import CLASSIFICATION_PROMPT_VERSION, CLASSIFICATION_SYSTEM, report_data
from app.application.pipeline import analyze_checks
from app.application.briefings import briefing_loop
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
        rules_started = self.clock()
        decision = assess_launch(submission.wind_knots, submission.temp_c, submission.fuel_pct)
        rules_finished = self.clock()
        priority = calculate_priority(created_at, None, bool(decision.violations), provisional=True)
        priority_finished = self.clock()
        report = Report(
            **asdict(submission), id=str(uuid4()), created_at=created_at,
            verdict=decision.verdict, violations=decision.violations, rule_version=decision.rule_version,
            **asdict(priority),
        )
        await self.store.save(report, [
            python_trace(report.id, "filing", 10, created_at, self.clock()),
            python_trace(report.id, "launch_rules", 20, rules_started, rules_finished),
            python_trace(report.id, "priority_provisional", 25, rules_finished, priority_finished),
        ])
        return report

    async def get(self, report_id: str) -> Report:
        report = await self.store.get(report_id)
        if report is None:
            raise ReportNotFound
        return report

    async def list(self, limit: int, offset: int) -> tuple[list[Report], int]:
        return await self.store.list(limit, offset)

    async def traces(self, report_id: str):
        await self.get(report_id)
        steps = await self.store.list_traces(report_id)
        return {"report_id": report_id, "steps": steps, "totals": summarize_traces(steps)}

    async def resolve_priority(self, report_id: str, classified_severity: object) -> Report:
        report = await self.get(report_id)
        started = self.clock()
        priority = calculate_priority(report.created_at, classified_severity, bool(report.violations))
        resolved = replace(report, **asdict(priority))
        await self.store.update_priority(resolved, python_trace(report.id, "priority_resolved", 40, started, self.clock()))
        return resolved

    async def classify(self, report_id: str, gateway: LLMGateway) -> Report:
        report = await self.get(report_id)
        if report.classification_status != "not_run":
            return report
        request = LLMRequest(
            stage="classification", round_number=None, system_prompt=CLASSIFICATION_SYSTEM,
            data={"report": report_data(report)},
            schema=Classification.model_json_schema(), max_output_tokens=300,
            prompt_version=CLASSIFICATION_PROMPT_VERSION,
        )
        trace = running_trace(report.id, "classification", 30, self.clock(), gateway, request.prompt_version)
        await self.store.start_traces([trace])
        response = await guarded_generate(gateway, request)
        finished_at = self.clock()

        classified = None
        code = model_error(response)
        if code is None:
            try:
                classified = Classification.model_validate(response.payload)
            except ValidationError:
                code = "invalid_output"

        priority_started = self.clock()
        priority = calculate_priority(report.created_at, classified.severity if classified else "high", bool(report.violations))
        priority_trace = python_trace(report.id, "priority_resolved", 40, priority_started, self.clock())
        reasons = tuple(dict.fromkeys((*report.review_reasons, *((f"classification_{code}",) if code else ()))))
        resolved = replace(
            report, **asdict(priority), subsystem=classified.subsystem if classified else "unknown",
            classification_status="completed" if classified else "fallback",
            classification_rationale=classified.rationale if classified else "Classification unavailable; human review required.",
            requires_review=report.requires_review or bool(code), review_reasons=reasons,
        )
        usage = token_usage(response.input_tokens, response.cached_input_tokens, response.output_tokens)
        trace = replace(trace,
            status="error" if code else "completed", finished_at=finished_at,
            provider=response.provider, model=response.model, prompt_version=request.prompt_version,
            provider_response_id=response.response_id, error_code=code, **usage,
        )
        await self.store.update_classification(resolved, trace, priority_trace)
        return resolved

    async def run_checks(self, report_id: str, gateway: LLMGateway) -> Report:
        report = await self.get(report_id)
        if report.checks:
            return report
        resolved, traces = await analyze_checks(report, gateway, self.clock, self.store)
        await self.store.update_checks(resolved, traces)
        return resolved

    async def generate_briefing(self, report_id: str, gateway: LLMGateway) -> Report:
        return await briefing_loop(await self.get(report_id), gateway, self.store, self.clock)
