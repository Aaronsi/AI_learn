"""Unit tests for configuration"""

import pytest
from pathlib import Path
from pydantic import ValidationError
from pg_mcp.config.settings import (
    DatabaseConfig,
    LLMConfig,
    SecurityConfig,
    RateLimitConfig,
    CacheConfig,
)


def test_database_config():
    """Test DatabaseConfig validation"""
    from pydantic import SecretStr

    config = DatabaseConfig(
        name="test_db",
        host="localhost",
        port=5432,
        database="test",
        username="user",
        password=SecretStr("pass"),
    )
    assert config.name == "test_db"
    assert config.host == "localhost"
    assert config.port == 5432
    assert config.schemas == ["public"]
    assert config.min_pool_size == 2
    assert config.max_pool_size == 10


def test_llm_config():
    """Test LLMConfig validation"""
    from pydantic import SecretStr

    config = LLMConfig(
        api_key=SecretStr("sk-test"),
        base_url="https://api.deepseek.com/v1",
        model="deepseek-chat",
        temperature=0.1,
        max_tokens=2048,
        timeout=30,
    )
    assert config.base_url == "https://api.deepseek.com/v1"
    assert config.model == "deepseek-chat"
    assert config.temperature == 0.1
    assert config.max_tokens == 2048

    # Test validation
    with pytest.raises(ValidationError):
        LLMConfig(api_key=SecretStr("test"), temperature=3.0)  # Invalid temperature

    with pytest.raises(ValidationError):
        LLMConfig(api_key=SecretStr("test"), max_tokens=0)  # Invalid max_tokens


def test_security_config_defaults():
    """Test SecurityConfig default values"""
    config = SecurityConfig()
    assert config.max_rows == 200
    assert config.hard_max_rows == 1000
    assert config.query_timeout == 30
    assert config.enable_result_validation is True
    assert config.max_retry_attempts == 3
    assert "password" in config.sensitive_columns


def test_cache_config():
    """Test CacheConfig validation"""
    config = CacheConfig()
    assert config.enable_disk_cache is True
    assert config.cache_dir == Path(".pg_mcp_cache")
    assert config.cache_ttl_hours == 24
    assert config.auto_refresh_interval_hours == 0

