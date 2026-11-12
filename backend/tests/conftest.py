import pytest

from app.config import Settings


@pytest.fixture
def settings(tmp_path):
    return Settings(database_url=f"sqlite+aiosqlite:///{tmp_path}/mission.sqlite")
