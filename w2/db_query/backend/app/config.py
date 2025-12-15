"""Application configuration."""
import os
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""

    app_name: str = "DB Query Tool"
    app_version: str = "0.1.0"
    debug: bool = False

    # DeepSeek API
    deepseek_api_key: str = ""
    deepseek_base_url: str = "https://api.deepseek.com"

    # SQLite Database
    sqlite_db_path: str = "~/.db_query/db_query.db"

    # Server
    app_port: int = 8000
    log_level: str = "INFO"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        env_prefix="",
    )

    def __init__(self, **kwargs):
        """Initialize settings and expand SQLite path."""
        super().__init__(**kwargs)
        # Expand ~ to home directory
        if self.sqlite_db_path.startswith("~"):
            self.sqlite_db_path = str(
                Path.home() / self.sqlite_db_path[2:].lstrip("/")
            )
        # Create directory if it doesn't exist
        db_dir = Path(self.sqlite_db_path).parent
        db_dir.mkdir(parents=True, exist_ok=True)

    @property
    def sqlite_url(self) -> str:
        """Get SQLite database URL."""
        return f"sqlite+aiosqlite:///{self.sqlite_db_path}"


settings = Settings()

