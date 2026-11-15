import pytest

from app.config import Settings


@pytest.fixture
def settings(tmp_path):
    return Settings(database_url=f"sqlite+aiosqlite:///{tmp_path}/mission.sqlite")


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
