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
