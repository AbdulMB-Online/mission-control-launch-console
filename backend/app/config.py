from typing import Literal

from pydantic import SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(extra="ignore")

    database_url: str = "sqlite+aiosqlite:///./data/mission.sqlite"
    llm_provider: Literal["fake", "openai"] = "fake"
    openai_api_key: SecretStr | None = None
    openai_model: str = "gpt-5.4-mini-2026-03-17"
    director_username: str = "flight-director"
    director_password: SecretStr = SecretStr("demo-director")

    @model_validator(mode="after")
    def validate_runtime(self):
        if not self.database_url.startswith("sqlite+aiosqlite:///") or self.database_url.endswith(":memory:"):
            raise ValueError("Use a file-backed SQLite URL (sqlite+aiosqlite:///...).")
        if self.llm_provider == "openai":
            if not self.openai_api_key or not self.openai_api_key.get_secret_value().strip():
                raise ValueError("OPENAI_API_KEY is required in OpenAI mode.")
            if (
                not self.director_username.strip()
                or self.director_username == "flight-director"
                or not self.director_password.get_secret_value().strip()
                or self.director_password.get_secret_value() == "demo-director"
            ):
                raise ValueError("Set explicit non-demo director credentials in OpenAI mode.")
        return self
