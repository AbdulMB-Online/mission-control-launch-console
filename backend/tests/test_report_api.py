from datetime import datetime, timedelta
from decimal import Decimal
from uuid import UUID

import pytest
from fastapi.testclient import TestClient

from app.main import create_app


@pytest.fixture
def client(settings):
    with TestClient(create_app(settings)) as session:
        yield session


def assert_field_error(response, field):
    assert response.status_code == 422, response.text
    error = response.json()["error"]
    assert error["code"] == "validation_error"
    assert error["message"]
    assert any(item["field"] == field and item["message"] for item in error["fields"])


def test_file_report_returns_saved_fields_and_server_metadata(client, report_payload):
    response = client.post("/api/v1/reports", json=report_payload)
    assert response.status_code == 201, response.text
    report = response.json()
    UUID(report["id"])
    assert response.headers["location"] == f"/api/v1/reports/{report['id']}"
    for field in ("engineer_name", "station", "note"):
        assert report[field] == report_payload[field]
    for field in ("wind_knots", "temp_c", "fuel_pct"):
        assert isinstance(report[field], str)
        assert Decimal(report[field]) == Decimal(report_payload[field])
    created = datetime.fromisoformat(report["created_at"].replace("Z", "+00:00"))
    assert created.utcoffset() == timedelta(0)
    saved = client.get(response.headers["location"])
    assert saved.status_code == 200
    assert saved.json()["id"] == report["id"]


def test_filing_trims_text_without_losing_the_note(client, report_payload):
    report_payload.update(engineer_name="  Alex Rivera  ", station="  PROP  ", note="  Valve lag; verify the final cycle.  ")
    response = client.post("/api/v1/reports", json=report_payload)
    assert response.status_code == 201, response.text
    assert response.json()["engineer_name"] == "Alex Rivera"
    assert response.json()["station"] == "PROP"
    assert response.json()["note"] == "Valve lag; verify the final cycle."


@pytest.mark.parametrize("field", ["engineer_name", "station", "wind_knots", "temp_c", "fuel_pct", "note"])
def test_every_submission_field_is_required(client, report_payload, field):
    del report_payload[field]
    assert_field_error(client.post("/api/v1/reports", json=report_payload), field)


@pytest.mark.parametrize(
    "field, value",
    [
        ("engineer_name", ""),
        ("engineer_name", "A" * 101),
        ("station", "   "),
        ("station", "S" * 51),
        ("note", " \n\t "),
        ("note", "N" * 4001),
    ],
    ids=["blank-name", "name-too-long", "blank-station", "station-too-long", "blank-note", "note-too-long"],
)
def test_blank_or_overlong_text_has_a_clear_field_error(client, report_payload, field, value):
    report_payload[field] = value
    assert_field_error(client.post("/api/v1/reports", json=report_payload), field)
    listing = client.get("/api/v1/reports")
    assert listing.status_code == 200
    assert listing.json()["total"] == 0


@pytest.mark.parametrize(
    "field, value",
    [
        ("wind_knots", 25),
        ("wind_knots", True),
        ("wind_knots", "-0.001"),
        ("wind_knots", "1e1"),
        ("temp_c", None),
        ("temp_c", "NaN"),
        ("temp_c", "4.0001"),
        ("fuel_pct", "Infinity"),
        ("fuel_pct", "-0.001"),
        ("fuel_pct", "1000000"),
    ],
)
def test_invalid_readings_are_rejected_without_rounding(client, report_payload, field, value):
    report_payload[field] = value
    assert_field_error(client.post("/api/v1/reports", json=report_payload), field)


@pytest.mark.parametrize(
    "field, value",
    [("verdict", "go"), ("approved", True), ("approved_by", "intruder"), ("severity", "low"), ("created_at", "2000-01-01T00:00:00Z")],
)
def test_submission_cannot_supply_privileged_metadata(client, report_payload, field, value):
    report_payload[field] = value
    assert_field_error(client.post("/api/v1/reports", json=report_payload), field)


@pytest.mark.parametrize(
    "field, value",
    [("wind_knots", "25.001"), ("temp_c", "3.999"), ("temp_c", "-5.000"), ("fuel_pct", "97.999"), ("fuel_pct", "100.001")],
)
def test_out_of_launch_limit_readings_are_valid_report_data(client, report_payload, field, value):
    report_payload[field] = value
    response = client.post("/api/v1/reports", json=report_payload)
    assert response.status_code == 201, response.text
    assert Decimal(response.json()[field]) == Decimal(value)


def test_reports_list_is_paginated_and_ordered_from_saved_metadata(client, report_payload):
    reports = []
    for station in ("PROP", "TEL", "ENV"):
        response = client.post("/api/v1/reports", json={**report_payload, "station": station})
        assert response.status_code == 201, response.text
        reports.append(response.json())
    response = client.get("/api/v1/reports?limit=1&offset=1")
    assert response.status_code == 200
    page = response.json()
    expected = sorted(reports, key=lambda item: (item["created_at"], item["id"]), reverse=True)
    assert page["total"] == 3
    assert page["limit"] == 1 and page["offset"] == 1
    assert [item["id"] for item in page["items"]] == [expected[1]["id"]]


def test_unknown_report_has_an_explicit_not_found_error(client):
    response = client.get("/api/v1/reports/00000000-0000-4000-8000-000000000000")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "report_not_found"


@pytest.mark.parametrize("query, field", [("limit=0", "limit"), ("offset=-1", "offset")])
def test_invalid_list_parameters_have_clear_errors(client, query, field):
    assert_field_error(client.get(f"/api/v1/reports?{query}"), field)
