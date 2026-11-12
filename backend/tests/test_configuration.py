import pytest
from pydantic import ValidationError

from app.config import Settings


def test_fake_mode_needs_no_api_key(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    assert Settings().llm_provider == "fake"


@pytest.mark.parametrize(
    "values, message",
    [
        ({"llm_provider": "openai"}, "OPENAI_API_KEY"),
        (
            {"llm_provider": "openai", "openai_api_key": "test-key"},
            "director credentials",
        ),
        ({"database_url": "postgresql://localhost/mission"}, "SQLite"),
    ],
)
def test_invalid_runtime_configuration_has_clear_errors(values, message):
    with pytest.raises(ValidationError, match=message):
        Settings(**values)


def test_live_mode_accepts_explicit_credentials_and_redacts_secrets():
    settings = Settings(
        llm_provider="openai",
        openai_api_key="private-api-key",
        director_username="director",
        director_password="private-director-password",
    )
    assert settings.llm_provider == "openai"
    assert "private-api-key" not in repr(settings)
    assert "private-director-password" not in repr(settings)
