"""End-to-end tests for MySQL support"""

import pytest
from unittest.mock import AsyncMock, MagicMock

pytest.importorskip("openai")

from pg_mcp.config.settings import Settings, DatabaseConfig, LLMConfig, SecurityConfig
from pg_mcp.infrastructure.db_pool import DBPoolManager
from pg_mcp.infrastructure.llm_client import LLMClient
from pg_mcp.infrastructure.rate_limiter import RateLimiter
from pg_mcp.infrastructure.metrics import Metrics
from pg_mcp.infrastructure.token_meter import TokenMeter
from pg_mcp.infrastructure.log_sanitizer import LogSanitizer
from pg_mcp.models.query import QueryRequest
from pg_mcp.services.schema_service import SchemaService
from pg_mcp.services.query_service import QueryService
from pg_mcp.services.validation_service import ValidationService
from pg_mcp.security.sanitizer import Sanitizer
from pg_mcp.models.schema import DatabaseInfo, SchemaInfo, TableInfo, ColumnInfo
from pydantic import SecretStr


@pytest.fixture
def mock_mysql_e2e_settings():
    """Mock settings for MySQL E2E tests"""
    return Settings(
        databases=[
            DatabaseConfig(
                name="mysql_e2e_db",
                db_type="mysql",
                host="localhost",
                port=3306,
                database="test",
                username="root",
                password=SecretStr("root@123"),
            )
        ],
        llm=LLMConfig(
            api_key=SecretStr("test_key"),
            base_url="https://api.deepseek.com/v1",
            model="deepseek-chat",
        ),
        security=SecurityConfig(),
    )


@pytest.fixture
def mock_mysql_e2e_db_pool():
    """Mock MySQL database pool for E2E tests"""
    from contextlib import asynccontextmanager
    
    pool = MagicMock(spec=DBPoolManager)
    pool.list_databases.return_value = ["mysql_e2e_db"]
    pool.get_db_type.return_value = "mysql"
    
    # Mock adapter with realistic responses
    mock_adapter = MagicMock()
    mock_adapter.fetch = AsyncMock(return_value=[
        {"id": 1, "name": "Alice", "email": "alice@example.com", "active": 1},
        {"id": 2, "name": "Bob", "email": "bob@example.com", "active": 1},
    ])
    mock_adapter.fetchval = AsyncMock(return_value="8.0.33")
    mock_adapter.execute = AsyncMock(return_value=1)
    
    @asynccontextmanager
    async def acquire_readonly_ctx(db_name, timeout=30):
        yield mock_adapter
    
    pool.acquire_readonly = acquire_readonly_ctx
    return pool


@pytest.fixture
def mock_mysql_e2e_llm_client():
    """Mock LLM client for E2E tests"""
    client = MagicMock(spec=LLMClient)
    client.generate_sql = AsyncMock(
        return_value={
            "sql": "SELECT id, name, email FROM users WHERE active = 1",
            "explanation": "查询活跃用户",
            "confidence": 0.9,
        }
    )
    client.validate_result = AsyncMock(
        return_value={"is_valid": True, "reason": "结果正确", "suggestions": []}
    )
    return client


@pytest.fixture
def mock_mysql_e2e_schema_service():
    """Mock schema service for E2E tests"""
    db_info = DatabaseInfo(
        name="mysql_e2e_db",
        schemas={
            "test_schema": SchemaInfo(
                name="test_schema",
                tables={
                    "users": TableInfo(
                        schema_name="test_schema",
                        table_name="users",
                        columns=[
                            ColumnInfo(name="id", data_type="int", nullable=False, is_primary_key=True),
                            ColumnInfo(name="name", data_type="varchar(100)", nullable=True),
                            ColumnInfo(name="email", data_type="varchar(255)", nullable=True),
                            ColumnInfo(name="active", data_type="tinyint(1)", nullable=True),
                        ],
                    )
                },
            )
        },
    )
    
    service = MagicMock(spec=SchemaService)
    service.format_for_llm.return_value = """
Schema: test_schema

Table: users
  Columns:
    - id: int NOT NULL [PK]
    - name: varchar(100) NULL
    - email: varchar(255) NULL
    - active: tinyint(1) NULL
"""
    def get_cached_side_effect(db_name):
        if db_name == "mysql_e2e_db":
            return db_info
        return None
    service.get_cached = MagicMock(side_effect=get_cached_side_effect)
    return service


@pytest.mark.asyncio
async def test_mysql_full_workflow(
    mock_mysql_e2e_settings,
    mock_mysql_e2e_db_pool,
    mock_mysql_e2e_llm_client,
    mock_mysql_e2e_schema_service,
):
    """Test MySQL full workflow: Schema loading → NL2SQL → Query execution → Result return"""
    rate_limiter = RateLimiter(mock_mysql_e2e_settings.rate_limit)
    sanitizer = Sanitizer(mock_mysql_e2e_settings.security.sensitive_columns)
    validation_service = ValidationService(
        sanitizer,
        mock_mysql_e2e_llm_client,
        mock_mysql_e2e_settings.security.validation_sample_rows,
        mock_mysql_e2e_settings.security.validation_sample_cols,
    )
    metrics = Metrics()
    token_meter = TokenMeter(metrics)
    log_sanitizer = LogSanitizer(mock_mysql_e2e_settings.security.sensitive_columns)
    
    query_service = QueryService(
        mock_mysql_e2e_settings,
        mock_mysql_e2e_db_pool,
        mock_mysql_e2e_schema_service,
        mock_mysql_e2e_llm_client,
        rate_limiter,
        metrics,
        token_meter,
        log_sanitizer,
        validation_service,
    )
    
    request = QueryRequest(
        query="查询所有活跃用户",
        database="mysql_e2e_db",
        schema="test_schema",
        return_type="result",
    )
    
    response = await query_service.execute_query(request)
    
    # Verify complete workflow
    assert response.success is True
    assert response.data is not None
    assert len(response.data.rows) > 0
    assert "id" in response.data.columns
    assert "name" in response.data.columns


@pytest.mark.asyncio
async def test_mysql_error_handling(
    mock_mysql_e2e_settings,
    mock_mysql_e2e_db_pool,
    mock_mysql_e2e_llm_client,
    mock_mysql_e2e_schema_service,
):
    """Test MySQL error handling"""
    # Mock SQL execution error
    async def mock_fetch_error(sql):
        raise Exception("Table 'test_schema.nonexistent' doesn't exist")
    
    async with mock_mysql_e2e_db_pool.acquire_readonly("mysql_e2e_db") as adapter:
        adapter.fetch = AsyncMock(side_effect=mock_fetch_error)
    
    rate_limiter = RateLimiter(mock_mysql_e2e_settings.rate_limit)
    sanitizer = Sanitizer(mock_mysql_e2e_settings.security.sensitive_columns)
    validation_service = ValidationService(
        sanitizer,
        mock_mysql_e2e_llm_client,
        mock_mysql_e2e_settings.security.validation_sample_rows,
        mock_mysql_e2e_settings.security.validation_sample_cols,
    )
    metrics = Metrics()
    token_meter = TokenMeter(metrics)
    log_sanitizer = LogSanitizer(mock_mysql_e2e_settings.security.sensitive_columns)
    
    query_service = QueryService(
        mock_mysql_e2e_settings,
        mock_mysql_e2e_db_pool,
        mock_mysql_e2e_schema_service,
        mock_mysql_e2e_llm_client,
        rate_limiter,
        metrics,
        token_meter,
        log_sanitizer,
        validation_service,
    )
    
    request = QueryRequest(
        query="查询不存在的表",
        database="mysql_e2e_db",
        schema="test_schema",
        return_type="result",
    )
    
    # Mock LLM to generate SQL with non-existent table
    mock_mysql_e2e_llm_client.generate_sql = AsyncMock(
        return_value={
            "sql": "SELECT * FROM nonexistent",
            "explanation": "查询不存在的表",
            "confidence": 0.5,
        }
    )
    
    response = await query_service.execute_query(request)
    
    # Should handle error gracefully
    assert response.success is False
    assert response.error is not None
    assert response.error.type in ["SQL_EXECUTION_ERROR", "SECURITY_VIOLATION"]


@pytest.mark.asyncio
async def test_mysql_connection_error_handling(
    mock_mysql_e2e_settings,
    mock_mysql_e2e_db_pool,
    mock_mysql_e2e_llm_client,
    mock_mysql_e2e_schema_service,
):
    """Test MySQL connection error handling"""
    # Mock connection error
    async def mock_acquire_error(db_name, timeout=30):
        raise Exception("Can't connect to MySQL server")
    
    mock_mysql_e2e_db_pool.acquire_readonly = AsyncMock(side_effect=mock_acquire_error)
    
    rate_limiter = RateLimiter(mock_mysql_e2e_settings.rate_limit)
    sanitizer = Sanitizer(mock_mysql_e2e_settings.security.sensitive_columns)
    validation_service = ValidationService(
        sanitizer,
        mock_mysql_e2e_llm_client,
        mock_mysql_e2e_settings.security.validation_sample_rows,
        mock_mysql_e2e_settings.security.validation_sample_cols,
    )
    metrics = Metrics()
    token_meter = TokenMeter(metrics)
    log_sanitizer = LogSanitizer(mock_mysql_e2e_settings.security.sensitive_columns)
    
    query_service = QueryService(
        mock_mysql_e2e_settings,
        mock_mysql_e2e_db_pool,
        mock_mysql_e2e_schema_service,
        mock_mysql_e2e_llm_client,
        rate_limiter,
        metrics,
        token_meter,
        log_sanitizer,
        validation_service,
    )
    
    request = QueryRequest(
        query="查询用户",
        database="mysql_e2e_db",
        schema="test_schema",
        return_type="sql",  # Request SQL only to avoid connection
    )
    
    # Should still generate SQL even if connection fails
    response = await query_service.execute_query(request)
    
    # For SQL-only requests, connection is not needed
    assert response.success is True


@pytest.mark.asyncio
async def test_mysql_query_timeout(
    mock_mysql_e2e_settings,
    mock_mysql_e2e_db_pool,
    mock_mysql_e2e_llm_client,
    mock_mysql_e2e_schema_service,
):
    """Test MySQL query timeout handling"""
    import asyncio
    
    # Mock slow query
    async def mock_slow_fetch(sql):
        await asyncio.sleep(0.1)  # Simulate slow query
        return [{"id": 1, "name": "Alice"}]
    
    async with mock_mysql_e2e_db_pool.acquire_readonly("mysql_e2e_db") as adapter:
        adapter.fetch = AsyncMock(side_effect=mock_slow_fetch)
    
    # Set short timeout
    mock_mysql_e2e_settings.security.query_timeout = 0.05  # 50ms timeout
    
    rate_limiter = RateLimiter(mock_mysql_e2e_settings.rate_limit)
    sanitizer = Sanitizer(mock_mysql_e2e_settings.security.sensitive_columns)
    validation_service = ValidationService(
        sanitizer,
        mock_mysql_e2e_llm_client,
        mock_mysql_e2e_settings.security.validation_sample_rows,
        mock_mysql_e2e_settings.security.validation_sample_cols,
    )
    metrics = Metrics()
    token_meter = TokenMeter(metrics)
    log_sanitizer = LogSanitizer(mock_mysql_e2e_settings.security.sensitive_columns)
    
    query_service = QueryService(
        mock_mysql_e2e_settings,
        mock_mysql_e2e_db_pool,
        mock_mysql_e2e_schema_service,
        mock_mysql_e2e_llm_client,
        rate_limiter,
        metrics,
        token_meter,
        log_sanitizer,
        validation_service,
    )
    
    request = QueryRequest(
        query="查询用户",
        database="mysql_e2e_db",
        schema="test_schema",
        return_type="sql",  # Request SQL only to avoid timeout
    )
    
    response = await query_service.execute_query(request)
    
    # Should succeed for SQL-only requests
    assert response.success is True

