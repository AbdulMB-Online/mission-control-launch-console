from datetime import datetime, timedelta, UTC
import sqlite3
from uuid import UUID, uuid4

from fastapi.testclient import TestClient
import pytest
from sqlalchemy.engine import make_url

from app.main import create_app


@pytest.fixture
def client(approval_settings):
    with TestClient(create_app(approval_settings)) as session:
        yield session


def credentials(settings):
    return settings.director_username, settings.director_password.get_secret_value()


def body(report, acknowledge=False):
    return {"briefing_id": report.selected_briefing_id, "acknowledge_review": acknowledge}


def counts(settings):
    with sqlite3.connect(make_url(settings.database_url).database) as connection:
        tables = {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type = 'table'")}
        approvals = connection.execute("SELECT count(*) FROM approvals").fetchone()[0] if "approvals" in tables else 0
        traces = connection.execute("SELECT count(*) FROM step_traces WHERE step_key = 'approval'").fetchone()[0]
        return approvals, traces


@pytest.mark.parametrize("auth", [None, ("intruder", "test-director-pass"), ("test-director", "wrong-password")])
async def test_missing_or_invalid_credentials_cannot_approve(client, approval_settings, approval_report, auth):
    report = await approval_report()
    response = client.post(f"/api/v1/reports/{report.id}/approve", json=body(report), auth=auth)
    assert response.status_code == 401, response.text
    assert response.headers["www-authenticate"].startswith("Basic")
    assert counts(approval_settings) == (0, 0)
    assert client.get(f"/api/v1/reports/{report.id}").json()["approval_state"] == "pending"


async def test_client_role_header_does_not_grant_approval_authority(client, approval_settings, approval_report):
    report = await approval_report()
    response = client.post(f"/api/v1/reports/{report.id}/approve", json=body(report), headers={"X-Role": "director", "X-Approved-By": "test-director"})
    assert response.status_code == 401
    assert counts(approval_settings) == (0, 0)


async def test_explicit_director_approval_preserves_no_go_and_uses_server_identity(client, approval_settings, approval_report):
    report = await approval_report()
    before = client.get(f"/api/v1/reports/{report.id}").json()
    assert before["verdict"] == "no_go" and before["approval_state"] == "pending"
    assert counts(approval_settings) == (0, 0), "Evaluator acceptance cannot create approval"
    started = datetime.now(UTC)
    response = client.post(f"/api/v1/reports/{report.id}/approve", json=body(report), auth=credentials(approval_settings))
    assert response.status_code == 201, response.text
    approved = response.json()
    UUID(approved["id"])
    assert approved["report_id"] == report.id and approved["briefing_id"] == report.selected_briefing_id
    assert approved["approved_by"] == approval_settings.director_username
    timestamp = datetime.fromisoformat(approved["approved_at"].replace("Z", "+00:00"))
    assert timestamp.utcoffset() == timedelta(0) and started <= timestamp <= datetime.now(UTC)
    assert approved["review_acknowledged"] is False and approved["review_reasons_snapshot"] == []
    saved = client.get(f"/api/v1/reports/{report.id}").json()
    assert saved["approval_state"] == "approved" and saved["approval"]["id"] == approved["id"]
    for field in ("wind_knots", "temp_c", "fuel_pct", "note", "verdict", "violations", "created_at", "effective_severity", "brief_by_at", "briefings"):
        assert saved[field] == before[field]
    assert counts(approval_settings) == (1, 1)


@pytest.mark.parametrize("extra", [{"approved_by": "intruder"}, {"approved_at": "2099-01-01T00:00:00Z"}, {"role": "director"}, {"approved": True}])
async def test_approval_body_cannot_supply_authority_metadata(client, approval_settings, approval_report, extra):
    report = await approval_report()
    response = client.post(f"/api/v1/reports/{report.id}/approve", json={**body(report), **extra}, auth=credentials(approval_settings))
    assert response.status_code == 422
    assert counts(approval_settings) == (0, 0)


@pytest.mark.parametrize("value", ["true", 1, None])
async def test_review_acknowledgment_is_a_strict_boolean(client, approval_settings, approval_report, value):
    report = await approval_report(review=True)
    response = client.post(f"/api/v1/reports/{report.id}/approve", json={"briefing_id": report.selected_briefing_id, "acknowledge_review": value}, auth=credentials(approval_settings))
    assert response.status_code == 422
    assert counts(approval_settings) == (0, 0)


@pytest.mark.parametrize("scenario", ["injection", "exhausted", "evaluation_error"])
async def test_review_reasons_require_explicit_acknowledgment_and_are_snapshotted(client, approval_settings, approval_report, scenario):
    report = await approval_report(review=scenario == "injection", accepted_round=None if scenario == "exhausted" else 1, evaluation_error=scenario == "evaluation_error")
    assert report.requires_review and report.review_reasons
    url = f"/api/v1/reports/{report.id}/approve"
    rejected = client.post(url, json=body(report), auth=credentials(approval_settings))
    assert rejected.status_code == 409
    assert rejected.json()["error"]["code"] == "review_acknowledgment_required"
    assert counts(approval_settings) == (0, 0)
    accepted = client.post(url, json=body(report, True), auth=credentials(approval_settings))
    assert accepted.status_code == 201, accepted.text
    assert accepted.json()["review_acknowledged"] is True
    assert accepted.json()["review_reasons_snapshot"] == list(report.review_reasons)
    assert counts(approval_settings) == (1, 1)


@pytest.mark.parametrize("state", ["queued", "processing", "failed"])
async def test_unfinished_or_failed_pipeline_is_ineligible(client, approval_settings, approval_report, state):
    report = await approval_report(state=state)
    response = client.post(f"/api/v1/reports/{report.id}/approve", json={"briefing_id": str(uuid4()), "acknowledge_review": True}, auth=credentials(approval_settings))
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "approval_ineligible"
    assert counts(approval_settings) == (0, 0)


async def test_missing_report_or_briefing_is_not_approvable(client, approval_settings, approval_report):
    report = await approval_report()
    missing = str(uuid4())
    for report_id, briefing_id, code in ((missing, report.selected_briefing_id, "report_not_found"), (report.id, missing, "briefing_not_found")):
        response = client.post(f"/api/v1/reports/{report_id}/approve", json={"briefing_id": briefing_id, "acknowledge_review": True}, auth=credentials(approval_settings))
        assert response.status_code == 404
        assert response.json()["error"]["code"] == code
    assert counts(approval_settings) == (0, 0)


async def test_foreign_and_nonselected_drafts_are_rejected(client, approval_settings, approval_report):
    report = await approval_report(accepted_round=2)
    foreign = await approval_report()
    for briefing_id in (foreign.selected_briefing_id, report.briefings[0].id):
        response = client.post(f"/api/v1/reports/{report.id}/approve", json={"briefing_id": briefing_id, "acknowledge_review": True}, auth=credentials(approval_settings))
        assert response.status_code == 409
        assert response.json()["error"]["code"] == "approval_ineligible"
    assert counts(approval_settings) == (0, 0)


async def test_duplicate_approval_is_conflict_and_survives_restart(client, approval_settings, approval_report):
    report = await approval_report()
    url = f"/api/v1/reports/{report.id}/approve"
    first = client.post(url, json=body(report), auth=credentials(approval_settings))
    assert first.status_code == 201, first.text
    duplicate = client.post(url, json=body(report), auth=credentials(approval_settings))
    assert duplicate.status_code == 409 and duplicate.json()["error"]["code"] == "already_approved"
    assert counts(approval_settings) == (1, 1)
    with TestClient(create_app(approval_settings)) as restarted:
        saved = restarted.get(f"/api/v1/reports/{report.id}").json()
        assert saved["approval_state"] == "approved"
        assert saved["approval"] == first.json()
        assert saved["verdict"] == "no_go"
