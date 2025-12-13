import os
from typing import List

from pydantic import BaseModel, Field


class Settings(BaseModel):
    database_url: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/postgres"
    )
    app_port: int = 8000
    allowed_origins: List[str] = Field(default_factory=list)
    log_level: str = "INFO"
    max_request_size: int = 1_048_576  # 1 MB

    @classmethod
    def from_env(cls) -> "Settings":
        raw_origins = os.getenv("ALLOWED_ORIGINS", "")
        origins = [o.strip() for o in raw_origins.split(",") if o.strip()]
        return cls(
            database_url=os.getenv(
                "DATABASE_URL",
                cls.model_fields["database_url"].default,  # type: ignore[index]
            ),
            app_port=int(os.getenv("APP_PORT", cls.model_fields["app_port"].default)),  # type: ignore[index]
            allowed_origins=origins
            or cls.model_fields["allowed_origins"].default_factory(),  # type: ignore[operator]
            log_level=os.getenv("LOG_LEVEL", cls.model_fields["log_level"].default),  # type: ignore[index]
            max_request_size=int(
                os.getenv(
                    "MAX_REQUEST_SIZE", cls.model_fields["max_request_size"].default
                )  # type: ignore[index]
            ),
        )


settings = Settings.from_env()
