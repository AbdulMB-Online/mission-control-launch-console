from unittest.mock import AsyncMock

from fastapi.testclient import TestClient

from app.main import create_app


def test_startup_migrates_database_and_serves_health(settings):
    with TestClient(create_app(settings)) as client:
        response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "mission-control",
        "provider": "fake",
    }


def test_health_reports_unready_database_without_exposing_configuration(settings):
    app = create_app(settings)
    with TestClient(app) as client:
        app.state.database.ready = AsyncMock(return_value=False)
        response = client.get("/healthz")
    assert response.status_code == 503
    assert response.json() == {"status": "unavailable"}
    assert settings.database_url not in response.text
