import asyncio
import sqlite3

import httpx
from sqlalchemy.engine import make_url

from app.main import create_app


async def test_simultaneous_approval_requests_create_one_record_and_one_trace(approval_settings, approval_report):
    report = await approval_report()
    app = create_app(approval_settings)
    async with app.router.lifespan_context(app):
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://mission.test") as client:
            async def approve():
                return await client.post(f"/api/v1/reports/{report.id}/approve", json={"briefing_id": report.selected_briefing_id, "acknowledge_review": False}, auth=(approval_settings.director_username, approval_settings.director_password.get_secret_value()))
            responses = await asyncio.gather(approve(), approve())
            assert sorted(response.status_code for response in responses) == [201, 409]
            saved = (await client.get(f"/api/v1/reports/{report.id}")).json()
            assert saved["approval_state"] == "approved" and saved["verdict"] == "no_go"
    with sqlite3.connect(make_url(approval_settings.database_url).database) as connection:
        assert connection.execute("SELECT count(*) FROM approvals WHERE report_id = ?", (report.id,)).fetchone()[0] == 1
        assert connection.execute("SELECT count(*) FROM step_traces WHERE report_id = ? AND step_key = 'approval'", (report.id,)).fetchone()[0] == 1
