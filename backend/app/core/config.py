from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    app_name: str = "AI Contact API"
    app_version: str = "1.0.0"
    debug: bool = False
    host: str = "0.0.0.0"
    port: int = 8000

    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"

    unisender_api_key: str = ""
    unisender_sender_email: str = ""

    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from_email: str = ""
    smtp_owner_email: str = ""

    rate_limit_max: int = 5
    rate_limit_window: int = 60

    database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5432/contacts"

    @property
    def storage_dir(self) -> Path:
        return Path(__file__).resolve().parent.parent.parent / "storage"

    @property
    def logs_dir(self) -> Path:
        return self.storage_dir / "logs"

    @property
    def metrics_dir(self) -> Path:
        return self.storage_dir / "metrics"

    @property
    def rate_limit_dir(self) -> Path:
        return self.storage_dir / "rate_limit"


settings = Settings()
