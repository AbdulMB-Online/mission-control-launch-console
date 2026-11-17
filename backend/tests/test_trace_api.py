import asyncio
from dataclasses import replace
from datetime import datetime
from decimal import Decimal
from importlib import import_module
import json
import sqlite3
from uuid import uuid4

from fastapi.testclient import TestClient
import pytest
from sqlalchemy.engine import make_url

from app.application.llm import LLMResult
from app.application.reports import ReportService
from app.domain.reports import ReportInput
from app.infrastructure.db import Database
from app.infrastructure.llm.fake_gateway import FakeGateway
from app.infrastructure.repository import SQLAlchemyReportStore
from app.main import create_app


MODEL = "gpt-5.4-mini-2026-03-17"


class UsageGateway(FakeGateway):
    """Scripted metadata exercises real accounting without an OpenAI adapter or network."""
    provider = "openai"

    async def generate(self, request):
        result = await super().generate(request)
        return replace(result, provider="openai", model=MODEL, input_tokens=1000,
                       cached_input_tokens=200, output_tokens=100, usage_status="reported")


@pytest.fixture
async def trace_run(settings, report_payload):
    database = Database(settings.database_url)
    await database.migrate()
    service = ReportService(SQLAlchemyReportStore(database.sessions))
    async def create(*, gateway=None, accept_at=1, complete=True):
        gateway = gateway or UsageGateway()
        report = await service.file(ReportInput(**{
            **report_payload, **{key: Decimal(report_payload[key]) for key in ("wind_knots", "temp_c", "fuel_pct")},
        }))
        for number in range(1, 4):
            gateway.script("evaluation", number, LLMResult(provider="fake", payload={
                "acceptable": number == accept_at, "feedback": [] if number == accept_at else ["Clarify the valve timing."],
            }))
        if complete:
            await service.classify(report.id, gateway)
            await service.run_checks(report.id, gateway)
            report = await service.generate_briefing(report.id, gateway)
        return service, gateway, report
    try:
        yield create
    finally:
        await database.close()


def read_trace(client, report_id):
    response = client.get(f"/api/v1/reports/{report_id}/traces")
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["report_id"] == report_id
    return data


async def test_trace_records_every_executed_step_and_all_three_rounds_once(approval_settings, trace_run):
    _, gateway, report = await trace_run(accept_at=3)
    with TestClient(create_app(approval_settings)) as client:
        approved = client.post(f"/api/v1/reports/{report.id}/approve", auth=("test-director", "test-director-pass"), json={"briefing_id": report.selected_briefing_id, "acknowledge_review": True})
        assert approved.status_code == 201
        data = read_trace(client, report.id)
    keys = [item["step_key"] for item in data["steps"]]
    assert keys == ["filing", "launch_rules", "priority_provisional", "classification", "priority_resolved", "injection", "missing_information", "tone", "draft_1", "evaluation_1", "draft_2", "evaluation_2", "draft_3", "evaluation_3", "approval"]
    assert len({item["id"] for item in data["steps"]}) == 15
    assert len(gateway.requests) == 10, "Reading traces must not repeat model calls"
    for item in data["steps"]:
        assert item["status"] == "completed"
        assert datetime.fromisoformat(item["started_at"].replace("Z", "+00:00")) <= datetime.fromisoformat(item["finished_at"].replace("Z", "+00:00"))
        if item["provider"] in ("python", "human"):
            assert (item["input_tokens"], item["cached_input_tokens"], item["output_tokens"]) == (0, 0, 0)
            assert Decimal(item["cost_usd"]) == 0
        else:
            assert Decimal(item["cost_usd"]) == Decimal("0.001065")
            assert item["rate_snapshot"]["model"] == MODEL
            assert item["rate_snapshot"]["version"]
    parallel = [item for item in data["steps"] if item["step_key"] in ("injection", "missing_information", "tone")]
    assert parallel[0]["parallel_group"] and len({item["parallel_group"] for item in parallel}) == 1
    totals = data["totals"]
    assert (totals["input_tokens"], totals["cached_input_tokens"], totals["output_tokens"]) == (10000, 2000, 1000)
    assert Decimal(totals["known_cost_usd"]) == Decimal("0.010650")
    assert totals["cost_complete"] and totals["usage_complete"] and not totals["simulated"]


async def test_queued_report_has_only_steps_that_actually_executed(settings, trace_run):
    _, _, report = await trace_run(complete=False)
    with TestClient(create_app(settings)) as client:
        data = read_trace(client, report.id)
    assert [item["step_key"] for item in data["steps"]] == ["filing", "launch_rules", "priority_provisional"]
    assert all(item["provider"] == "python" for item in data["steps"])


async def test_in_flight_model_call_is_visible_then_completed_in_place(settings, trace_run):
    gateway = UsageGateway()
    started, release = asyncio.Event(), asyncio.Event()
    gateway.script("classification", None, LLMResult(provider="fake", payload={"subsystem": "unknown", "severity": "high", "rationale": "Inspect report."}), started=started, release=release)
    service, _, report = await trace_run(gateway=gateway, complete=False)
    task = asyncio.create_task(service.classify(report.id, gateway))
    try:
        await asyncio.wait_for(started.wait(), 2)
        with TestClient(create_app(settings)) as client:
            running = read_trace(client, report.id)
            step = next(item for item in running["steps"] if item["step_key"] == "classification")
            assert step["status"] == "running" and step["finished_at"] is None
            assert step["cost_usd"] is None and not running["totals"]["cost_complete"]
            release.set()
            await task
            complete = read_trace(client, report.id)
        finished = [item for item in complete["steps"] if item["step_key"] == "classification"]
        assert len(finished) == 1 and finished[0]["id"] == step["id"]
        assert finished[0]["started_at"] == step["started_at"] and finished[0]["status"] == "completed"
    finally:
        release.set()
        await task


@pytest.mark.parametrize("status,payload,code", [
    ("completed", {"severity": "unsafe-value"}, "invalid_output"),
    ("refused", None, "refusal"), ("incomplete", None, "incomplete"),
])
async def test_failed_model_responses_keep_reported_usage_and_cost(settings, trace_run, status, payload, code):
    service, gateway, report = await trace_run(complete=False)
    gateway.script("classification", None, LLMResult(provider="openai", payload=payload, status=status, error_code=code))
    await service.classify(report.id, gateway)
    with TestClient(create_app(settings)) as client:
        data = read_trace(client, report.id)
    trace = next(item for item in data["steps"] if item["step_key"] == "classification")
    assert trace["status"] == "error" and trace["error_code"] == code
    assert trace["input_tokens"] == 1000 and trace["cached_input_tokens"] == 200 and trace["output_tokens"] == 100
    assert Decimal(trace["cost_usd"]) == Decimal("0.001065")
    assert Decimal(data["totals"]["known_cost_usd"]) == Decimal("0.001065")


@pytest.mark.parametrize("kind", ["missing_usage", "unknown_model"])
async def test_unknown_usage_or_rate_marks_total_incomplete_without_false_zero(settings, trace_run, kind):
    service, gateway, report = await trace_run(gateway=FakeGateway(), complete=False)
    gateway.script("classification", None, LLMResult(provider="openai", model="unpriced-model" if kind == "unknown_model" else MODEL,
        payload={"subsystem": "unknown", "severity": "high", "rationale": "Inspect report."},
        input_tokens=1000 if kind == "unknown_model" else None, cached_input_tokens=200 if kind == "unknown_model" else None,
        output_tokens=100 if kind == "unknown_model" else None))
    await service.classify(report.id, gateway)
    with TestClient(create_app(settings)) as client:
        data = read_trace(client, report.id)
    trace = next(item for item in data["steps"] if item["step_key"] == "classification")
    assert trace["cost_usd"] is None
    assert data["totals"]["cost_complete"] is False
    assert data["totals"]["usage_complete"] is (kind == "unknown_model")
    assert Decimal(data["totals"]["known_cost_usd"]) == 0


async def test_fake_trace_is_explicit_simulation_with_zero_real_charge(settings, trace_run):
    _, _, report = await trace_run(gateway=FakeGateway())
    with TestClient(create_app(settings)) as client:
        data = read_trace(client, report.id)
    assert data["totals"]["simulated"] is True
    assert Decimal(data["totals"]["known_cost_usd"]) == 0
    assert data["totals"]["cost_complete"] is True
    assert all(item["rate_snapshot"] is None for item in data["steps"])


async def test_cost_snapshot_is_persisted_and_never_repriced_on_read_or_restart(settings, trace_run, monkeypatch):
    _, _, report = await trace_run()
    with TestClient(create_app(settings)) as client:
        original = read_trace(client, report.id)
    with sqlite3.connect(make_url(settings.database_url).database) as connection:
        rows = connection.execute("SELECT cost_usd, rate_snapshot_json FROM step_traces WHERE report_id = ? AND provider = 'openai'", (report.id,)).fetchall()
    assert len(rows) == 6
    for amount, snapshot_json in rows:
        assert Decimal(amount) == Decimal("0.001065")
        saved_rate = json.loads(snapshot_json)
        assert Decimal(saved_rate["input_per_million"]) == Decimal("0.75")
        assert Decimal(saved_rate["cached_input_per_million"]) == Decimal("0.075")
        assert Decimal(saved_rate["output_per_million"]) == Decimal("4.50")
    module = import_module("app.domain.costs")
    monkeypatch.setattr(module, "get_rate", lambda *_: module.RateSnapshot(version="future-rate", model=MODEL,
        input_per_million=Decimal("99"), cached_input_per_million=Decimal("9"), output_per_million=Decimal("999")))
    with TestClient(create_app(settings)) as restarted:
        assert read_trace(restarted, report.id) == original


def test_trace_endpoint_rejects_missing_and_malformed_report_ids(settings):
    with TestClient(create_app(settings)) as client:
        missing = client.get(f"/api/v1/reports/{uuid4()}/traces")
        assert missing.status_code == 404 and missing.json()["error"]["code"] == "report_not_found"
        assert client.get("/api/v1/reports/not-a-uuid/traces").status_code == 422
