"""Configuration management using Pydantic Settings"""

from pydantic import BaseModel, Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict, PydanticBaseSettingsSource
from typing import Literal
from pathlib import Path

try:
    from pydantic_settings import YamlConfigSettingsSource
    HAS_YAML_SOURCE = True
except ImportError:
    HAS_YAML_SOURCE = False


class DatabaseConfig(BaseModel):
    """单个数据库连接配置"""

    name: str = Field(..., description="数据库别名")
    db_type: Literal["postgresql", "mysql"] = Field(
        default="postgresql", description="数据库类型"
    )
    host: str = Field(default="localhost")
    port: int = Field(default=5432)
    database: str = Field(..., description="数据库名")
    username: str
    password: SecretStr
    role: str | None = Field(
        default=None, description="可选的只读角色，若提供则在会话中执行 SET ROLE"
    )
    ssl_mode: Literal[
        "disable", "prefer", "require", "verify-ca", "verify-full"
    ] = "prefer"
    schemas: list[str] = Field(default=["public"])
    exclude_tables: list[str] = Field(default_factory=list)
    min_pool_size: int = Field(default=2, ge=1)
    max_pool_size: int = Field(default=10, ge=1)


class LLMConfig(BaseModel):
    """LLM配置（DeepSeek使用OpenAI兼容API）"""

    api_key: SecretStr
    base_url: str = Field(default="https://api.deepseek.com/v1")
    model: str = Field(default="deepseek-chat")
    temperature: float = Field(default=0.1, ge=0, le=2)
    max_tokens: int = Field(default=2048, ge=1)
    timeout: int = Field(default=30, ge=1)
    cost_per_1k_tokens: float = Field(
        default=0.0, ge=0, description="可选：每千token成本估算"
    )


class SecurityConfig(BaseModel):
    """安全配置"""

    max_rows: int = Field(default=200, ge=1, description="默认最大返回行数")
    hard_max_rows: int = Field(default=1000, ge=1, description="硬上限")
    query_timeout: int = Field(default=30, ge=1, description="查询超时秒数")
    allowed_functions: list[str] = Field(
        default_factory=list, description="函数白名单"
    )
    sensitive_columns: list[str] = Field(
        default=["password", "secret", "token", "credential", "ssn", "credit_card"],
        description="敏感列名模式",
    )
    enable_result_validation: bool = Field(default=True)
    max_retry_attempts: int = Field(default=3, ge=1)
    validation_sample_rows: int = Field(default=20, ge=1)
    validation_sample_cols: int = Field(default=10, ge=1)
    enable_explain_check: bool = Field(
        default=False, description="执行前是否进行EXPLAIN安全检查"
    )
    explain_max_cost: float | None = Field(
        default=None, ge=0, description="EXPLAIN计划允许的最大成本"
    )
    explain_max_rows: int | None = Field(
        default=None, ge=1, description="EXPLAIN计划允许的最大行数"
    )


class RateLimitConfig(BaseModel):
    """限流配置"""

    llm_requests_per_minute: int = Field(default=60)
    db_queries_per_minute: int = Field(default=100)
    enable_circuit_breaker: bool = Field(default=True)
    circuit_breaker_threshold: int = Field(
        default=5, description="连续失败次数触发熔断"
    )
    circuit_breaker_timeout: int = Field(
        default=60, description="熔断恢复时间秒数"
    )


class CacheConfig(BaseModel):
    """缓存配置"""

    enable_disk_cache: bool = Field(default=True)
    cache_dir: Path = Field(default=Path(".pg_mcp_cache"))
    cache_ttl_hours: int = Field(default=24)
    auto_refresh_interval_hours: int = Field(
        default=0, description="0表示禁用自动刷新"
    )


class Settings(BaseSettings):
    """应用主配置"""

    model_config = SettingsConfigDict(
        env_prefix="PG_MCP_",
        env_nested_delimiter="__",
        yaml_file="pg-mcp.yaml",
        yaml_file_encoding="utf-8",
    )

    databases: list[DatabaseConfig]
    llm: LLMConfig
    security: SecurityConfig = Field(default_factory=SecurityConfig)
    rate_limit: RateLimitConfig = Field(default_factory=RateLimitConfig)
    cache: CacheConfig = Field(default_factory=CacheConfig)
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        """自定义配置源顺序，添加 YAML 支持"""
        sources: list[PydanticBaseSettingsSource] = [
            init_settings,
            env_settings,
        ]
        if HAS_YAML_SOURCE:
            sources.append(YamlConfigSettingsSource(settings_cls))
        sources.append(dotenv_settings)
        sources.append(file_secret_settings)
        return tuple(sources)

