from datetime import UTC, datetime, timedelta
from decimal import Decimal
import sqlite3

from alembic import command
from fastapi import Request
from fastapi.testclient import TestClient
import pytest
from sqlalchemy import text
from sqlalchemy.engine import make_url

from app.api.routes import get_reports
from app.application.reports import ReportService
from app.domain.reports import ReportInput
from app.infrastructure.db import Database
from app.infrastructure.repository import SQLAlchemyReportStore
from app.main import create_app


CREATED_AT = datetime(2026, 11, 15, 23, 58, tzinfo=UTC)
DEADLINE = "2026-11-16T00:03:00.000000Z"


@pytest.fixture
def client(settings):
    app = create_app(settings)

    async def fixed_reports(request: Request):
        return ReportService(SQLAlchemyReportStore(request.app.state.database.sessions), clock=lambda: CREATED_AT)

    app.dependency_overrides[get_reports] = fixed_reports
    with TestClient(app) as session:
        yield session


@pytest.mark.parametrize("wind, verdict", [("25", "go"), ("25.001", "no_go")])
def test_filing_read_and_list_return_server_owned_provisional_deadline(client, report_payload, wind, verdict):
    response = client.post("/api/v1/reports", json={**report_payload, "wind_knots": wind})
    assert response.status_code == 201, response.text
    filed = response.json()
    for report in (filed, client.get(response.headers["location"]).json(), client.get("/api/v1/reports").json()["items"][0]):
        assert report.get("effective_severity") == "high", "Unclassified reports need conservative Python priority"
        assert report["classified_severity"] is None
        assert report["severity_provisional"] is True
        assert report["deadline_minutes"] == 5
        assert report["brief_by_at"] == DEADLINE
        assert report["verdict"] == verdict


@pytest.mark.parametrize("field, value", [
    ("classified_severity", "low"), ("effective_severity", "low"), ("deadline_minutes", 999),
    ("brief_by_at", "2099-01-01T00:00:00Z"), ("severity_provisional", False),
])
def test_engineers_cannot_set_severity_or_deadline_metadata(client, report_payload, field, value):
    response = client.post("/api/v1/reports", json={**report_payload, field: value})
    assert response.status_code == 422
    assert any(item["field"] == field for item in response.json()["error"]["fields"])
    assert client.get("/api/v1/reports").json()["total"] == 0


def test_provisional_deadline_is_stored_and_not_extended_on_restart(client, settings, report_payload):
    response = client.post("/api/v1/reports", json=report_payload)
    assert response.status_code == 201
    report = response.json()
    assert report.get("brief_by_at") == DEADLINE
    with sqlite3.connect(make_url(settings.database_url).database) as connection:
        values = connection.execute(
            "SELECT effective_severity, deadline_minutes, brief_by_at, severity_provisional FROM reports WHERE id = ?",
            (report["id"],),
        ).fetchone()
    assert values == ("high", 5, DEADLINE, 1)
    with TestClient(create_app(settings)) as restarted:
        saved = restarted.get(response.headers["location"]).json()
        for field in ("created_at", "brief_by_at", "deadline_minutes", "severity_provisional", "effective_severity"):
            assert saved[field] == report[field]


async def test_upgrade_anchors_existing_report_deadline_to_original_timestamp(settings, report_payload):
    historical = Database(settings.database_url)
    old_id = "00000000-0000-4000-8000-000000000002"
    try:
        def setup_old_schema(connection):
            config = historical.migration_config()
            config.attributes["connection"] = connection
            command.upgrade(config, "0003")

        async with historical.engine.begin() as connection:
            await connection.run_sync(setup_old_schema)
            await connection.execute(text(
                "INSERT INTO reports (id, engineer_name, station, wind_knots, temp_c, fuel_pct, note, created_at, "
                "verdict, violations_json, rule_version) VALUES (:id, :engineer_name, :station, :wind_knots, :temp_c, "
                ":fuel_pct, :note, :created_at, 'go', '[]', 'v1')"
            ), {**report_payload, "id": old_id, "created_at": CREATED_AT.isoformat(timespec="microseconds").replace("+00:00", "Z")})
    finally:
        await historical.close()

    with TestClient(create_app(settings)) as upgraded:
        response = upgraded.get(f"/api/v1/reports/{old_id}")
        assert response.status_code == 200, response.text
        report = response.json()
        assert report.get("brief_by_at") == DEADLINE, "Migration must not start a new five-minute clock"
        assert report["effective_severity"] == "high"
        assert report["classified_severity"] is None
        assert report["severity_provisional"] is True
        assert report["verdict"] == "go"


@pytest.mark.parametrize("severity, minutes", [("high", 5), ("medium", 15), ("low", 30)])
async def test_resolved_priority_is_persisted_and_reload_does_not_reset_it(settings, report_payload, severity, minutes):
    database = Database(settings.database_url)
    try:
        await database.migrate()
        service = ReportService(SQLAlchemyReportStore(database.sessions), clock=lambda: CREATED_AT)
        original = await service.file(ReportInput(**{
            **report_payload,
            **{field: Decimal(report_payload[field]) for field in ("wind_knots", "temp_c", "fuel_pct")},
        }))
        service.clock = lambda: CREATED_AT + timedelta(days=2)
        resolved = await service.resolve_priority(original.id, severity)
        assert resolved.effective_severity == severity
    finally:
        await database.close()

    with TestClient(create_app(settings)) as restarted:
        saved = restarted.get(f"/api/v1/reports/{original.id}").json()
        assert saved["effective_severity"] == severity
        assert saved["classified_severity"] == severity
        assert saved["deadline_minutes"] == minutes
        assert saved["severity_provisional"] is False
        assert saved["brief_by_at"] == (CREATED_AT + timedelta(minutes=minutes)).isoformat(timespec="microseconds").replace("+00:00", "Z")
        assert saved["created_at"] == CREATED_AT.isoformat(timespec="microseconds").replace("+00:00", "Z")
        assert saved["verdict"] == original.verdict
