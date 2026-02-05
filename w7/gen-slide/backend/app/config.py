"""Configuration management for GenSlides application.

This module provides centralized configuration using Pydantic settings,
loading values from environment variables and .env files.
"""

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables.

    Attributes:
        ARK_API_KEY: Volcano Ark API authentication key
        ARK_API_ENDPOINT: Base URL for Ark API
        ARK_MODEL_ID: Model identifier for image generation
        HOST: Server host address
        PORT: Server port number
        SLIDES_BASE_PATH: Base directory for storing slide projects
    """

    ARK_API_KEY: str
    ARK_API_ENDPOINT: str = "https://ark.cn-beijing.volces.com/api/v3"
    ARK_MODEL_ID: str = "doubao-seedream-4-5-251128"
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    SLIDES_BASE_PATH: str = "../slides"

    class Config:
        """Pydantic configuration."""
        env_file = ".env"
        env_file_encoding = "utf-8"


# Global settings instance
settings = Settings()
