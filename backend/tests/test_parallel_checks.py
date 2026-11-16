import asyncio
from dataclasses import replace
from datetime import UTC, datetime
from decimal import Decimal
from types import SimpleNamespace

from fastapi.testclient import TestClient
import pytest
from sqlalchemy import text

from app.application.reports import ReportService
from app.domain.reports import ReportInput
from app.infrastructure.db import Database
from app.infrastructure.repository import SQLAlchemyReportStore
from app.main import create_app


STAGES = {"injection", "missing_information", "tone"}
DEFAULTS = {
    "injection": {"flagged": False, "reasons": []},
    "missing_information": {"flagged": False, "missing_details": []},
    "tone": {"tone": "calm", "rationale": "Factual engineering language."},
}


def response(payload):
    return SimpleNamespace(payload=payload, status="completed", error_code=None, provider="fake",
                           model="scripted-checks", response_id="fake-check", input_tokens=100,
                           cached_input_tokens=10, output_tokens=20, usage_status="reported")


class ChecksGateway:
    def __init__(self, overrides=None):
        self.payloads = {**DEFAULTS, **(overrides or {})}
        self.requests = []

    async def generate(self, request):
        self.requests.append(request)
        payload = self.payloads[request.stage]
        if isinstance(payload, BaseException):
            raise payload
        if hasattr(payload, "status"):
            return payload
        return response(payload)


class BarrierGateway(ChecksGateway):
    def __init__(self):
        super().__init__()
        self.all_started = asyncio.Event()
        self.release = asyncio.Event()
        self.started = set()
        self.cancelled = set()

    async def generate(self, request):
        self.started.add(request.stage)
        if self.started == STAGES:
            self.all_started.set()
        try:
            await self.release.wait()
        except asyncio.CancelledError:
            self.cancelled.add(request.stage)
            raise
        return await super().generate(request)


class MemoryReports:
    def __init__(self):
        self.traces = []

    async def save(self, report):
        self.report = report

    async def get(self, report_id):
        return self.report if self.report.id == report_id else None

    async def update_priority(self, report):
        self.report = report

    async def update_checks(self, report, traces):
        self.report = report
        self.traces.extend(traces)


async def file_report(payload, store=None):
    store = store or MemoryReports()
    service = ReportService(store, clock=lambda: datetime(2026, 11, 15, 23, 58, tzinfo=UTC))
    original = await service.file(ReportInput(**{
        **payload, **{field: Decimal(payload[field]) for field in ("wind_knots", "temp_c", "fuel_pct")},
    }))
    return service, store, original


def assert_authority_unchanged(report, original):
    for field in ("id", "wind_knots", "temp_c", "fuel_pct", "note", "created_at", "verdict", "violations",
                  "rule_version", "classified_severity", "effective_severity", "deadline_minutes", "brief_by_at"):
        assert getattr(report, field) == getattr(original, field)
    assert getattr(report, "approved", False) is False


async def test_all_three_checks_start_before_any_is_released(report_payload):
    service, store, original = await file_report(report_payload)
    gateway = BarrierGateway()
    task = asyncio.create_task(service.run_checks(original.id, gateway))
    try:
        await asyncio.wait_for(gateway.all_started.wait(), timeout=1)
        assert gateway.started == STAGES
        assert not task.done()
        gateway.release.set()
        report = await asyncio.wait_for(task, timeout=1)
    finally:
        gateway.release.set()
        if not task.done():
            task.cancel()
        await asyncio.gather(task, return_exceptions=True)
    assert {item.kind for item in report.checks} == STAGES
    assert all(item.status == "completed" for item in report.checks)
    assert report.requires_review is False and not report.review_reasons
    assert len(store.traces) == 3
    groups = {item.parallel_group for item in store.traces}
    assert len(groups) == 1 and None not in groups
    assert_authority_unchanged(report, original)


@pytest.mark.parametrize("failed_stage", sorted(STAGES))
async def test_one_timeout_preserves_successful_siblings_and_requires_review(report_payload, failed_stage):
    service, store, original = await file_report(report_payload)
    gateway = ChecksGateway({failed_stage: TimeoutError("do not expose provider details")})
    report = await service.run_checks(original.id, gateway)
    checks = {item.kind: item for item in report.checks}
    assert checks[failed_stage].status == "error"
    assert checks[failed_stage].flagged is None
    assert checks[failed_stage].error_code == "timeout"
    assert all(item.status == "completed" for kind, item in checks.items() if kind != failed_stage)
    assert report.requires_review and f"{failed_stage}_timeout" in report.review_reasons
    assert len(gateway.requests) == len(store.traces) == 3
    assert_authority_unchanged(report, original)


@pytest.mark.parametrize("status, code", [("refused", "refusal"), ("incomplete", "incomplete")])
async def test_refusal_and_incomplete_checks_keep_usage_and_require_review(report_payload, status, code):
    service, store, original = await file_report(report_payload)
    failure = response({})
    failure.status, failure.error_code = status, code
    report = await service.run_checks(original.id, ChecksGateway({"injection": failure}))
    check = next(item for item in report.checks if item.kind == "injection")
    assert check.status == "error" and check.flagged is None
    assert check.error_code == code and f"injection_{code}" in report.review_reasons
    trace = next(item for item in store.traces if item.step_key == "injection")
    assert (trace.input_tokens, trace.output_tokens) == (100, 20)
    assert_authority_unchanged(report, original)


async def test_all_failed_checks_are_unknown_and_require_review(report_payload):
    service, _, original = await file_report(report_payload)
    report = await service.run_checks(original.id, ChecksGateway({kind: RuntimeError("provider failed") for kind in STAGES}))
    assert len(report.checks) == 3
    assert all(item.status == "error" and item.flagged is None for item in report.checks)
    assert report.requires_review is True
    assert_authority_unchanged(report, original)


@pytest.mark.parametrize("kind, payload", [
    ("injection", {"flagged": "false", "reasons": []}),
    ("injection", {"flagged": False, "reasons": [], "approved": True}),
    ("missing_information", {"flagged": False, "missing_details": [], "verdict": "go"}),
    ("missing_information", {"flagged": True, "missing_details": ["x" * 501]}),
    ("tone", {"tone": "critical", "rationale": "Urgent."}),
    ("tone", {"tone": "panic", "rationale": ""}),
])
async def test_invalid_check_outputs_are_unknown_not_clean(report_payload, kind, payload):
    service, _, original = await file_report(report_payload)
    report = await service.run_checks(original.id, ChecksGateway({kind: payload}))
    check = next(item for item in report.checks if item.kind == kind)
    assert check.status == "error" and check.flagged is None
    assert check.error_code == "invalid_output"
    assert f"{kind}_invalid_output" in report.review_reasons
    assert report.requires_review is True
    assert_authority_unchanged(report, original)


@pytest.mark.parametrize("tone, flagged", [("calm", False), ("urgent", True), ("panic", True)])
async def test_tone_is_detected_without_rewriting_severity_or_deadline(report_payload, tone, flagged):
    service, _, original = await file_report(report_payload)
    original = await service.resolve_priority(original.id, "low")
    report = await service.run_checks(original.id, ChecksGateway({"tone": {"tone": tone, "rationale": "Tone observation."}}))
    check = next(item for item in report.checks if item.kind == "tone")
    assert check.details["tone"] == tone and check.flagged is flagged
    assert report.effective_severity == "low"
    assert_authority_unchanged(report, original)


async def test_missing_information_and_existing_review_reasons_are_retained(report_payload):
    service, store, original = await file_report(report_payload)
    store.report = replace(original, requires_review=True, review_reasons=("classification_invalid_output",))
    report = await service.run_checks(original.id, ChecksGateway({
        "missing_information": {"flagged": True, "missing_details": ["Time of the first observed valve lag."]},
    }))
    check = next(item for item in report.checks if item.kind == "missing_information")
    assert check.flagged is True
    assert check.details["missing_details"] == ["Time of the first observed valve lag."]
    assert {"classification_invalid_output", "missing_information_flagged"} <= set(report.review_reasons)
    assert report.requires_review is True


async def test_cancelling_check_group_cancels_all_model_calls_without_partial_success(report_payload):
    service, store, original = await file_report(report_payload)
    gateway = BarrierGateway()
    task = asyncio.create_task(service.run_checks(original.id, gateway))
    try:
        await asyncio.wait_for(gateway.all_started.wait(), timeout=1)
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task
        assert gateway.cancelled == STAGES
        assert not getattr(store.report, "checks", ())
        assert all(item.status != "completed" for item in store.traces)
        assert_authority_unchanged(store.report, original)
    finally:
        gateway.release.set()
        task.cancel()
        await asyncio.gather(task, return_exceptions=True)


async def test_check_results_usage_and_parallel_group_survive_restart(settings, report_payload):
    database = Database(settings.database_url)
    try:
        await database.migrate()
        service, _, original = await file_report(report_payload, SQLAlchemyReportStore(database.sessions))
        await service.run_checks(original.id, ChecksGateway({"injection": {"flagged": True, "reasons": ["Embedded instruction."]}}))
        async with database.engine.connect() as connection:
            rows = (await connection.execute(text(
                "SELECT kind, status FROM pipeline_checks WHERE report_id = :id"
            ), {"id": original.id})).all()
            assert {row.kind for row in rows} == STAGES
            traces = (await connection.execute(text(
                "SELECT parallel_group, input_tokens, output_tokens FROM step_traces WHERE report_id = :id"
            ), {"id": original.id})).all()
            assert len(traces) == 3 and len({row.parallel_group for row in traces}) == 1
            assert all(row.parallel_group and row.input_tokens == 100 and row.output_tokens == 20 for row in traces)
    finally:
        await database.close()

    with TestClient(create_app(settings)) as restarted:
        report = restarted.get(f"/api/v1/reports/{original.id}").json()
        assert {item["kind"] for item in report["checks"]} == STAGES
        assert report["requires_review"] is True
        assert "injection_flagged" in report["review_reasons"]
        assert report["verdict"] == original.verdict
