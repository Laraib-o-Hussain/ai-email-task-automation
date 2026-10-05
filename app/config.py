from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "AI Email Task Automation"
    database_url: str = "sqlite:///./data/tasks.db"
    ai_mode: str = "mock"  # mock | openai
    openai_api_key: str | None = None
    openai_model: str = "gpt-4o-mini"
    openai_base_url: str = "https://api.openai.com/v1"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()

if settings.database_url.startswith("sqlite:///./"):
    Path("data").mkdir(exist_ok=True)
