from contextlib import contextmanager
import os
from pathlib import Path
import subprocess
import sys
import time

from fastapi.testclient import TestClient
import httpx

from app.main import create_app


def assert_original_data(saved, created):
    for field in ("id", "engineer_name", "station", "wind_knots", "temp_c", "fuel_pct", "note", "created_at"):
        assert saved[field] == created[field]


def test_report_survives_disposing_and_recreating_the_application(settings, report_payload):
    with TestClient(create_app(settings)) as first:
        response = first.post("/api/v1/reports", json=report_payload)
        assert response.status_code == 201, response.text
        created = response.json()

    with TestClient(create_app(settings)) as restarted:
        response = restarted.get(f"/api/v1/reports/{created['id']}")
        assert response.status_code == 200
        assert_original_data(response.json(), created)
        listing = restarted.get("/api/v1/reports").json()
        assert listing["total"] == 1
        assert listing["items"][0]["id"] == created["id"]


@contextmanager
def running_api(settings, log_path):
    environment = {
        **os.environ,
        "DATABASE_URL": settings.database_url,
        "LLM_PROVIDER": "fake",
        "OPENAI_API_KEY": "",
        "PYTHONUNBUFFERED": "1",
        "PIPELINE_AUTOSTART": "false",
    }
    with log_path.open("a") as log:
        process = subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "app.main:create_app", "--factory", "--host", "127.0.0.1", "--port", "18081"],
            cwd=Path(__file__).resolve().parents[1],
            env=environment,
            stdout=log,
            stderr=subprocess.STDOUT,
        )
        try:
            with httpx.Client(base_url="http://127.0.0.1:18081", trust_env=False, timeout=1) as client:
                deadline = time.monotonic() + 10
                while time.monotonic() < deadline:
                    if process.poll() is not None:
                        raise AssertionError(f"Local API failed to start: {log_path.read_text()[-2000:]}")
                    try:
                        if client.get("/healthz").status_code == 200:
                            break
                    except httpx.TransportError:
                        pass
                    time.sleep(0.05)
                else:
                    raise AssertionError("Local API readiness timed out")
                yield client
        finally:
            process.terminate()
            try:
                process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=3)


def test_report_survives_a_real_api_process_restart(settings, report_payload, tmp_path):
    log_path = tmp_path / "api-process.log"
    with running_api(settings, log_path) as first:
        response = first.post("/api/v1/reports", json=report_payload)
        assert response.status_code == 201, response.text
        created = response.json()

    with running_api(settings, log_path) as restarted:
        response = restarted.get(f"/api/v1/reports/{created['id']}")
        assert response.status_code == 200
        assert_original_data(response.json(), created)
