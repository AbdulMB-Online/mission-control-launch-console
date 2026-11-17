"""The smoke CLI must exercise the deployed HTTP contract and fail clearly."""
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import subprocess
import sys
from threading import Thread

from test_system_workflow import system_api  # shared isolated API-process fixture


SMOKE = Path(__file__).resolve().parents[2] / "scripts" / "smoke.py"


def run_smoke(base_url, *, password="system-pass"):
    return subprocess.run([sys.executable, str(SMOKE)], env={
        **os.environ, "SMOKE_BASE_URL": str(base_url).rstrip("/"), "OPENAI_API_KEY": "",
        "DIRECTOR_USERNAME": "system-director", "DIRECTOR_PASSWORD": password,
    }, capture_output=True, text=True, timeout=20)


def test_deployment_smoke_files_processes_and_explicitly_approves_a_report(system_api):
    with system_api() as (client, _):
        result = run_smoke(client.base_url)
        assert result.returncode == 0, result.stdout + result.stderr
        listing = client.get("/api/v1/reports").json()
        assert listing["total"] == 1
        report = listing["items"][0]
        assert report["pipeline_status"] == "completed" and report["approval_state"] == "approved"
        assert report["approval"]["approved_by"] == "system-director"
        assert report["verdict"] == "no_go" and report["violations"]
        traces = client.get(f"/api/v1/reports/{report['id']}/traces").json()
        assert traces["steps"][-1]["step_key"] == "approval"
        assert traces["totals"]["simulated"] and traces["totals"]["cost_complete"]


def test_deployment_smoke_reports_invalid_director_credentials_without_false_success(system_api):
    with system_api() as (client, _):
        result = run_smoke(client.base_url, password="wrong-password")
        assert result.returncode != 0
        assert "credentials" in (result.stdout + result.stderr).lower()
        listing = client.get("/api/v1/reports").json()
        assert listing["total"] == 1
        assert listing["items"][0]["approval"] is None


@contextmanager
def live_mode_health():
    writes = []
    class HealthHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            body = json.dumps({"status": "ok", "service": "mission-control", "provider": "openai"}).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        def do_POST(self):
            writes.append(self.path)
            self.send_error(500)
        def log_message(self, *_args):
            pass
    server = ThreadingHTTPServer(("127.0.0.1", 0), HealthHandler)
    worker = Thread(target=server.serve_forever, daemon=True)
    worker.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}", writes
    finally:
        server.shutdown()
        server.server_close()
        worker.join(timeout=2)


def test_deployment_smoke_refuses_live_mode_before_filing_or_model_calls():
    with live_mode_health() as (url, writes):
        result = run_smoke(url)
        assert result.returncode != 0
        assert "fake" in (result.stdout + result.stderr).lower()
        assert writes == []
