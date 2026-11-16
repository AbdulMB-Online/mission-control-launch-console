import asyncio
from dataclasses import replace
from datetime import UTC, datetime
from decimal import Decimal
from uuid import uuid4

import httpx
import pytest
from sqlalchemy import text

from app.application.llm import LLMResult, ModelTrace
from app.application.reports import ReportService
from app.domain.briefings import Briefing
from app.domain.reports import ReportInput
from app.infrastructure.db import Database
from app.infrastructure.llm.fake_gateway import FakeGateway
from app.infrastructure.repository import SQLAlchemyReportStore
from app.main import create_app


def active_settings(settings, **overrides):
    return type(settings)(**{**settings.model_dump(), "pipeline_autostart": True, **overrides})


def gate_classification(gateway):
    started, release = asyncio.Event(), asyncio.Event()
    response = LLMResult(provider="fake", model="scripted-lifecycle", payload={
        "subsystem": "propulsion", "severity": "low", "rationale": "Scripted classification.",
    })
    gateway.script("classification", None, response, started=started, release=release)
    return started, release


def client_for(app):
    return httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://mission.test")


async def saved_report(settings, payload, *, finish=False, fail=False, interrupted=False):
    database = Database(settings.database_url)
    gateway = FakeGateway()
    try:
        await database.migrate()
        store = SQLAlchemyReportStore(database.sessions)
        service = ReportService(store)
        report = await service.file(ReportInput(**{
            **payload, **{field: Decimal(payload[field]) for field in ("wind_knots", "temp_c", "fuel_pct")},
        }))
        if finish or fail or interrupted:
            report = await service.classify(report.id, gateway)
            report = await service.run_checks(report.id, gateway)
        if fail:
            gateway.script("draft", 1, RuntimeError("secret provider message"))
        if finish or fail:
            report = await service.generate_briefing(report.id, gateway)
        if interrupted:
            now = datetime.now(UTC)
            draft = Briefing(str(uuid4()), 1, "Saved draft before interruption.", ("Confirm the observation.",), now)
            report = replace(report, pipeline_status="processing", briefings=(draft,))
            trace = ModelTrace(
                id=str(uuid4()), report_id=report.id, step_key="evaluation_1", display_order=110,
                status="running", started_at=now, finished_at=now, provider="fake", model="fake-v1",
                prompt_version="evaluation-v1", provider_response_id=None, input_tokens=None,
                cached_input_tokens=None, output_tokens=None, usage_status="unavailable", error_code=None,
                round_number=1,
            )
            await store.update_briefings(report, trace)
        return report
    finally:
        await gateway.aclose()
        await database.close()


async def test_filing_returns_before_model_completion_and_reports_process_one_at_a_time(settings, report_payload):
    app = create_app(active_settings(settings))
    async with app.router.lifespan_context(app):
        gateway = app.state.llm_gateway
        started, release = gate_classification(gateway)
        async with client_for(app) as client:
            try:
                response = await asyncio.wait_for(client.post("/api/v1/reports", json=report_payload), timeout=1)
                assert response.status_code == 201
                first = response.json()
                assert first["pipeline_status"] == "queued"
                assert first["approval_state"] == "unavailable"
                await asyncio.wait_for(started.wait(), timeout=1)
                current = (await client.get(response.headers["location"])).json()
                assert current["pipeline_status"] == "processing"
                assert current["verdict"] == first["verdict"]
                assert (await client.get("/healthz")).status_code == 200
                second = await asyncio.wait_for(client.post("/api/v1/reports", json={**report_payload, "station": "TEL"}), timeout=1)
                assert second.status_code == 201 and second.json()["pipeline_status"] == "queued"
                assert len(gateway.requests) == 1, "Only one report executes while the first call is blocked"
            finally:
                release.set()
            await asyncio.wait_for(app.state.pipeline_runner.wait_idle(), timeout=3)
            for report_id in (first["id"], second.json()["id"]):
                saved = (await client.get(f"/api/v1/reports/{report_id}")).json()
                assert saved["pipeline_status"] == "completed" and saved["approval_state"] == "pending"
            assert len(gateway.requests) == 12


async def test_duplicate_scheduling_does_not_repeat_model_calls(settings, report_payload):
    app = create_app(active_settings(settings))
    async with app.router.lifespan_context(app):
        gateway = app.state.llm_gateway
        started, release = gate_classification(gateway)
        async with client_for(app) as client:
            try:
                report = (await client.post("/api/v1/reports", json=report_payload)).json()
                await asyncio.wait_for(started.wait(), timeout=1)
                app.state.pipeline_runner.schedule(report["id"])
                app.state.pipeline_runner.schedule(report["id"])
            finally:
                release.set()
            await asyncio.wait_for(app.state.pipeline_runner.wait_idle(), timeout=3)
            assert len(gateway.requests) == 6
            saved = (await client.get(f"/api/v1/reports/{report['id']}")).json()
            assert len(saved["briefings"]) == 1 and saved["approval_state"] == "pending"


async def test_startup_recovers_report_committed_before_task_scheduling(settings, report_payload):
    original = await saved_report(settings, report_payload)
    app = create_app(active_settings(settings))
    async with app.router.lifespan_context(app):
        await asyncio.wait_for(app.state.pipeline_runner.wait_idle(), timeout=3)
        async with client_for(app) as client:
            report = (await client.get(f"/api/v1/reports/{original.id}")).json()
            assert report["pipeline_status"] == "completed" and report["approval_state"] == "pending"
            assert report["created_at"] == original.created_at.isoformat(timespec="microseconds").replace("+00:00", "Z")
            assert report["verdict"] == original.verdict
            assert len(app.state.llm_gateway.requests) == 6


async def test_startup_marks_interrupted_work_failed_without_repeating_billable_calls(settings, report_payload):
    original = await saved_report(settings, report_payload, interrupted=True)
    app = create_app(active_settings(settings))
    async with app.router.lifespan_context(app):
        async with client_for(app) as client:
            report = (await client.get(f"/api/v1/reports/{original.id}")).json()
            assert report["pipeline_status"] == "failed"
            assert report["error_code"] == "interrupted"
            assert report["requires_review"] and "pipeline_interrupted" in report["review_reasons"]
            assert report["approval_state"] == "unavailable"
            assert len(report["checks"]) == 3 and len(report["briefings"]) == 1
            assert report["briefings"][0]["summary"] == "Saved draft before interruption."
            assert report["verdict"] == original.verdict
            assert not app.state.llm_gateway.requests
        async with app.state.database.engine.connect() as connection:
            row = (await connection.execute(text(
                "SELECT status, error_code, input_tokens, output_tokens FROM step_traces "
                "WHERE report_id = :id AND step_key = 'evaluation_1'"
            ), {"id": original.id})).one()
            assert tuple(row) == ("error", "interrupted", None, None)


@pytest.mark.parametrize("failed", [False, True])
async def test_terminal_reports_are_not_processed_again_on_restart(settings, report_payload, failed):
    original = await saved_report(settings, report_payload, finish=not failed, fail=failed)
    app = create_app(active_settings(settings))
    async with app.router.lifespan_context(app):
        async with client_for(app) as client:
            report = (await client.get(f"/api/v1/reports/{original.id}")).json()
            assert report["pipeline_status"] == ("failed" if failed else "completed")
            assert report["selected_briefing_id"] == original.selected_briefing_id
            assert report["verdict"] == original.verdict
            assert not app.state.llm_gateway.requests


async def test_shutdown_cancels_active_work_and_retains_report_without_approval(settings, report_payload):
    app = create_app(active_settings(settings))
    async with app.router.lifespan_context(app):
        started, _release = gate_classification(app.state.llm_gateway)
        async with client_for(app) as client:
            original = (await client.post("/api/v1/reports", json=report_payload)).json()
            await asyncio.wait_for(started.wait(), timeout=1)
    database = Database(settings.database_url)
    try:
        report = await ReportService(SQLAlchemyReportStore(database.sessions)).get(original["id"])
        assert report.pipeline_status == "failed" and report.error_code == "interrupted"
        assert report.approval_state == "unavailable" and report.verdict == original["verdict"]
    finally:
        await database.close()


async def test_pipeline_timeout_is_visible_and_does_not_reset_deadline(settings, report_payload):
    app = create_app(active_settings(settings, pipeline_timeout_seconds=0.2))
    async with app.router.lifespan_context(app):
        started, _release = gate_classification(app.state.llm_gateway)
        async with client_for(app) as client:
            original = (await client.post("/api/v1/reports", json=report_payload)).json()
            await asyncio.wait_for(started.wait(), timeout=1)
            await asyncio.wait_for(app.state.pipeline_runner.wait_idle(), timeout=3)
            report = (await client.get(f"/api/v1/reports/{original['id']}")).json()
            assert report["pipeline_status"] == "failed" and report["error_code"] == "pipeline_timeout"
            assert report["approval_state"] == "unavailable"
            assert report["brief_by_at"] == original["brief_by_at"]
            assert report["verdict"] == original["verdict"]
            assert len(app.state.llm_gateway.requests) == 1


async def test_unknown_scheduled_id_does_not_break_later_work(settings, report_payload):
    app = create_app(active_settings(settings))
    async with app.router.lifespan_context(app):
        app.state.pipeline_runner.schedule("00000000-0000-4000-8000-000000000000")
        async with client_for(app) as client:
            report = (await client.post("/api/v1/reports", json=report_payload)).json()
            await asyncio.wait_for(app.state.pipeline_runner.wait_idle(), timeout=3)
            saved = (await client.get(f"/api/v1/reports/{report['id']}")).json()
            assert saved["pipeline_status"] == "completed" and len(app.state.llm_gateway.requests) == 6
