import pytest

from app.config import Settings


@pytest.fixture
def settings(tmp_path):
    return Settings(database_url=f"sqlite+aiosqlite:///{tmp_path}/mission.sqlite", pipeline_autostart=False)


@pytest.fixture
def report_payload():
    return {
        "engineer_name": "Alex Rivera",
        "station": "PROP",
        "wind_knots": "25.000",
        "temp_c": "4.000",
        "fuel_pct": "98.000",
        "note": "Valve response lagged during the final check at 13:42 UTC.",
    }


@pytest.fixture(params=[
    pytest.param(("wind_knots", "24.999", None, None), id="wind-below-limit"),
    pytest.param(("wind_knots", "25", None, None), id="wind-at-limit"),
    pytest.param(("wind_knots", "25.000", None, None), id="wind-at-limit-with-scale"),
    pytest.param(("wind_knots", "25.001", "<=", "25"), id="wind-above-limit"),
    pytest.param(("temp_c", "3.999", ">=", "4"), id="temperature-below-limit"),
    pytest.param(("temp_c", "4", None, None), id="temperature-at-limit"),
    pytest.param(("temp_c", "4.001", None, None), id="temperature-above-limit"),
    pytest.param(("fuel_pct", "97.999", ">=", "98"), id="fuel-below-minimum"),
    pytest.param(("fuel_pct", "98", None, None), id="fuel-at-minimum"),
    pytest.param(("fuel_pct", "98.001", None, None), id="fuel-above-minimum"),
    pytest.param(("fuel_pct", "99.999", None, None), id="fuel-below-maximum"),
    pytest.param(("fuel_pct", "100", None, None), id="fuel-at-maximum"),
    pytest.param(("fuel_pct", "100.001", "<=", "100"), id="fuel-above-maximum"),
])
def launch_case(request, report_payload):
    field, value, operator, limit = request.param
    return {
        "payload": {**report_payload, field: value},
        "verdict": "no_go" if operator else "go",
        "violations": [{"field": field, "observed": value, "operator": operator, "limit": limit}] if operator else [],
    }


@pytest.fixture
def approval_settings(settings):
    return Settings(**{**settings.model_dump(), "director_username": "test-director", "director_password": "test-director-pass"})


@pytest.fixture
def approval_report(approval_settings, report_payload):
    """Build real saved analysis/drafts without adding an approval backdoor."""
    async def create(*, wind="25.001", review=False, accepted_round=1, evaluation_error=False, state=None):
        from decimal import Decimal
        from sqlalchemy import text
        from app.application.llm import LLMResult
        from app.application.reports import ReportService
        from app.domain.reports import ReportInput
        from app.infrastructure.db import Database
        from app.infrastructure.llm.fake_gateway import FakeGateway
        from app.infrastructure.repository import SQLAlchemyReportStore

        database = Database(approval_settings.database_url)
        gateway = FakeGateway()
        try:
            await database.migrate()
            service = ReportService(SQLAlchemyReportStore(database.sessions))
            payload = {**report_payload, "wind_knots": wind}
            report = await service.file(ReportInput(**{
                **payload, **{key: Decimal(payload[key]) for key in ("wind_knots", "temp_c", "fuel_pct")},
            }))
            if state is not None:
                async with database.engine.begin() as connection:
                    await connection.execute(text("UPDATE reports SET pipeline_status = :state WHERE id = :id"), {"state": state, "id": report.id})
                return await service.get(report.id)
            gateway.script("injection", None, LLMResult(provider="fake", payload={"flagged": review, "reasons": ["Instruction-like text."] if review else []}))
            gateway.script("missing_information", None, LLMResult(provider="fake", payload={"flagged": False, "missing_details": []}))
            for number in range(1, 4):
                gateway.script("evaluation", number, LLMResult(provider="fake", payload={
                    "acceptable": number == accepted_round, "feedback": [] if number == accepted_round else [f"Revise round {number}."],
                }))
            if evaluation_error:
                gateway.script("evaluation", 1, LLMResult(provider="fake", status="refused", error_code="refusal"))
            await service.classify(report.id, gateway)
            await service.run_checks(report.id, gateway)
            return await service.generate_briefing(report.id, gateway)
        finally:
            await gateway.aclose()
            await database.close()
    return create
