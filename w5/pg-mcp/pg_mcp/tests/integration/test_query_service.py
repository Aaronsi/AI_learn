"""Integration tests for query service"""

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
def mock_settings():
    """Mock settings"""
    return Settings(
        databases=[
            DatabaseConfig(
                name="test_db",
                host="localhost",
                port=5432,
                database="test",
                username="test_user",
                password=SecretStr("test_pass"),
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
def mock_db_pool():
    """Mock database pool"""
    from contextlib import asynccontextmanager
    from pg_mcp.infrastructure.db_adapter import PostgreSQLAdapter
    
    pool = MagicMock(spec=DBPoolManager)
    pool.list_databases.return_value = ["test_db"]
    pool.get_db_type.return_value = "postgresql"
    
    # Mock 连接适配器
    mock_adapter = MagicMock(spec=PostgreSQLAdapter)
    mock_adapter.fetch = AsyncMock(return_value=[])
    mock_adapter.fetchval = AsyncMock(return_value="PostgreSQL 15.0")
    mock_adapter.execute = AsyncMock(return_value=1)
    
    # Mock acquire_readonly 异步上下文管理器
    @asynccontextmanager
    async def acquire_readonly_ctx(db_name, timeout=30):
        yield mock_adapter
    
    pool.acquire_readonly = acquire_readonly_ctx
    
    return pool


@pytest.fixture
def mock_llm_client():
    """Mock LLM client"""
    client = MagicMock(spec=LLMClient)
    client.generate_sql = AsyncMock(
        return_value={
            "sql": "SELECT * FROM users WHERE active = true",
            "explanation": "查询活跃用户",
            "confidence": 0.9,
        }
    )
    client.validate_result = AsyncMock(
        return_value={"is_valid": True, "reason": "结果正确", "suggestions": []}
    )
    return client


@pytest.fixture
def mock_schema_service():
    """Mock schema service"""
    service = MagicMock(spec=SchemaService)
    service.format_for_llm.return_value = """
Schema: public

Table: users
  Columns:
    - id: integer NOT NULL [PK]
    - name: varchar NULL
    - active: boolean NULL
"""
    schema_info = SchemaInfo(name="public")
    schema_info.tables["users"] = TableInfo(
        schema_name="public",
        table_name="users",
        columns=[
            ColumnInfo(name="id", data_type="integer", nullable=False),
            ColumnInfo(name="name", data_type="varchar", nullable=True),
            ColumnInfo(name="active", data_type="boolean", nullable=True),
        ],
    )
    schema_info.tables["employees"] = TableInfo(
        schema_name="public",
        table_name="employees",
        columns=[
            ColumnInfo(name="department", data_type="varchar", nullable=True),
        ],
    )
    db_info = DatabaseInfo(name="test_db", schemas={"public": schema_info})
    service.get_cached.return_value = db_info
    return service


@pytest.mark.asyncio
async def test_simple_query(mock_settings, mock_db_pool, mock_llm_client, mock_schema_service):
    """P6-1a: 简单查询测试 - 查询所有活跃用户"""
    rate_limiter = RateLimiter(mock_settings.rate_limit)
    sanitizer = Sanitizer(mock_settings.security.sensitive_columns)
    validation_service = ValidationService(
        sanitizer,
        mock_llm_client,
        mock_settings.security.validation_sample_rows,
        mock_settings.security.validation_sample_cols,
    )
    metrics = Metrics()
    token_meter = TokenMeter(metrics)
    log_sanitizer = LogSanitizer(mock_settings.security.sensitive_columns)

    query_service = QueryService(
        mock_settings,
        mock_db_pool,
        mock_schema_service,
        mock_llm_client,
        rate_limiter,
        metrics,
        token_meter,
        log_sanitizer,
        validation_service,
    )

    request = QueryRequest(
        query="查询所有活跃用户",
        database="test_db",
        schema_name="public",
        return_type="sql",
    )

    response = await query_service.execute_query(request)

    assert response.success is True
    assert response.data is not None
    assert hasattr(response.data, "sql")
    assert "SELECT" in response.data.sql.upper()


@pytest.mark.asyncio
async def test_complex_aggregation_query(mock_settings, mock_db_pool, mock_llm_client, mock_schema_service):
    """P6-1b: 复杂聚合查询测试 - 统计每个部门的员工数量"""
    mock_llm_client.generate_sql = AsyncMock(
        return_value={
            "sql": "SELECT department, COUNT(*) as count FROM employees GROUP BY department",
            "explanation": "按部门统计员工数量",
            "confidence": 0.85,
        }
    )

    rate_limiter = RateLimiter(mock_settings.rate_limit)
    sanitizer = Sanitizer(mock_settings.security.sensitive_columns)
    validation_service = ValidationService(
        sanitizer,
        mock_llm_client,
        mock_settings.security.validation_sample_rows,
        mock_settings.security.validation_sample_cols,
    )
    metrics = Metrics()
    token_meter = TokenMeter(metrics)
    log_sanitizer = LogSanitizer(mock_settings.security.sensitive_columns)

    query_service = QueryService(
        mock_settings,
        mock_db_pool,
        mock_schema_service,
        mock_llm_client,
        rate_limiter,
        metrics,
        token_meter,
        log_sanitizer,
        validation_service,
    )

    request = QueryRequest(
        query="统计每个部门的员工数量",
        database="test_db",
        schema_name="public",
        return_type="sql",
    )

    response = await query_service.execute_query(request)

    assert response.success is True
    assert response.data is not None
    assert "GROUP BY" in response.data.sql.upper()
    assert "COUNT" in response.data.sql.upper()


@pytest.mark.asyncio
async def test_security_interception(mock_settings, mock_db_pool, mock_llm_client, mock_schema_service):
    """P6-1c: 安全拦截测试 - 删除所有过期订单"""
    # LLM 错误地生成了 DELETE 语句
    mock_llm_client.generate_sql = AsyncMock(
        return_value={
            "sql": "DELETE FROM orders WHERE expired = true",
            "explanation": "删除过期订单",
            "confidence": 0.7,
        }
    )

    rate_limiter = RateLimiter(mock_settings.rate_limit)
    sanitizer = Sanitizer(mock_settings.security.sensitive_columns)
    validation_service = ValidationService(
        sanitizer,
        mock_llm_client,
        mock_settings.security.validation_sample_rows,
        mock_settings.security.validation_sample_cols,
    )
    metrics = Metrics()
    token_meter = TokenMeter(metrics)
    log_sanitizer = LogSanitizer(mock_settings.security.sensitive_columns)

    query_service = QueryService(
        mock_settings,
        mock_db_pool,
        mock_schema_service,
        mock_llm_client,
        rate_limiter,
        metrics,
        token_meter,
        log_sanitizer,
        validation_service,
    )

    request = QueryRequest(
        query="删除所有过期订单",
        database="test_db",
        schema_name="public",
        return_type="sql",
    )

    response = await query_service.execute_query(request)

    # 应该被安全校验拦截
    assert response.success is False
    assert response.error is not None
    assert response.error.type == "SECURITY_VIOLATION" or "禁止" in response.error.message


@pytest.mark.asyncio
async def test_pagination(mock_settings, mock_db_pool, mock_llm_client, mock_schema_service):
    """P6-1d: 分页测试 - 验证page/page_size参数"""
    from pg_mcp.infrastructure.db_adapter import PostgreSQLAdapter
    
    # Mock 数据库返回结果
    mock_adapter = MagicMock(spec=PostgreSQLAdapter)
    mock_rows = [{"id": i, "name": f"user{i}"} for i in range(150)]
    mock_adapter.fetch = AsyncMock(return_value=mock_rows)
    mock_adapter.fetchval = AsyncMock(return_value="PostgreSQL 15.0")
    mock_adapter.execute = AsyncMock(return_value=1)

    from contextlib import asynccontextmanager
    
    @asynccontextmanager
    async def acquire_readonly_ctx(db_name, timeout=30):
        yield mock_adapter
    
    mock_db_pool.acquire_readonly = acquire_readonly_ctx

    rate_limiter = RateLimiter(mock_settings.rate_limit)
    sanitizer = Sanitizer(mock_settings.security.sensitive_columns)
    validation_service = ValidationService(
        sanitizer,
        mock_llm_client,
        mock_settings.security.validation_sample_rows,
        mock_settings.security.validation_sample_cols,
    )
    metrics = Metrics()
    token_meter = TokenMeter(metrics)
    log_sanitizer = LogSanitizer(mock_settings.security.sensitive_columns)

    query_service = QueryService(
        mock_settings,
        mock_db_pool,
        mock_schema_service,
        mock_llm_client,
        rate_limiter,
        metrics,
        token_meter,
        log_sanitizer,
        validation_service,
    )

    request = QueryRequest(
        query="查询所有用户",
        database="test_db",
        schema_name="public",
        return_type="result",
        page=2,
        page_size=50,
    )

    response = await query_service.execute_query(request)

    assert response.success is True
    assert response.data is not None
    assert hasattr(response.data, "page")
    assert response.data.page == 2
    assert hasattr(response.data, "page_size")
    assert response.data.page_size == 50


@pytest.mark.asyncio
async def test_multiple_databases(mock_settings, mock_db_pool, mock_llm_client, mock_schema_service):
    """P6-1e: 多数据库测试 - 指定不同数据库查询"""
    mock_db_pool.list_databases.return_value = ["db1", "db2"]

    rate_limiter = RateLimiter(mock_settings.rate_limit)
    sanitizer = Sanitizer(mock_settings.security.sensitive_columns)
    validation_service = ValidationService(
        sanitizer,
        mock_llm_client,
        mock_settings.security.validation_sample_rows,
        mock_settings.security.validation_sample_cols,
    )
    metrics = Metrics()
    token_meter = TokenMeter(metrics)
    log_sanitizer = LogSanitizer(mock_settings.security.sensitive_columns)

    query_service = QueryService(
        mock_settings,
        mock_db_pool,
        mock_schema_service,
        mock_llm_client,
        rate_limiter,
        metrics,
        token_meter,
        log_sanitizer,
        validation_service,
    )

    # 指定数据库
    request1 = QueryRequest(
        query="查询用户",
        database="db1",
        schema_name="public",
        return_type="sql",
    )
    response1 = await query_service.execute_query(request1)
    assert response1.success is True

    # 不指定数据库（使用默认第一个）
    request2 = QueryRequest(
        query="查询用户",
        database=None,
        schema_name="public",
        return_type="sql",
    )
    response2 = await query_service.execute_query(request2)
    assert response2.success is False
    assert response2.error is not None


@pytest.mark.asyncio
async def test_hard_max_rows_truncation(mock_settings, mock_db_pool, mock_llm_client, mock_schema_service):
    """P6-1f: 硬上限截断测试 - 结果超过hard_max_rows时正确截断"""
    from pg_mcp.infrastructure.db_adapter import PostgreSQLAdapter
    
    # Mock 返回超过硬上限的行数
    mock_adapter = MagicMock(spec=PostgreSQLAdapter)
    mock_rows = [{"id": i} for i in range(1500)]  # 超过 hard_max_rows=1000
    mock_adapter.fetch = AsyncMock(return_value=mock_rows)
    mock_adapter.fetchval = AsyncMock(return_value="PostgreSQL 15.0")
    mock_adapter.execute = AsyncMock(return_value=1)

    from contextlib import asynccontextmanager
    
    @asynccontextmanager
    async def acquire_readonly_ctx(db_name, timeout=30):
        yield mock_adapter
    
    mock_db_pool.acquire_readonly = acquire_readonly_ctx

    rate_limiter = RateLimiter(mock_settings.rate_limit)
    sanitizer = Sanitizer(mock_settings.security.sensitive_columns)
    validation_service = ValidationService(
        sanitizer,
        mock_llm_client,
        mock_settings.security.validation_sample_rows,
        mock_settings.security.validation_sample_cols,
    )
    metrics = Metrics()
    token_meter = TokenMeter(metrics)
    log_sanitizer = LogSanitizer(mock_settings.security.sensitive_columns)

    query_service = QueryService(
        mock_settings,
        mock_db_pool,
        mock_schema_service,
        mock_llm_client,
        rate_limiter,
        metrics,
        token_meter,
        log_sanitizer,
        validation_service,
    )

    request = QueryRequest(
        query="查询所有数据",
        database="test_db",
        schema_name="public",
        return_type="result",
        max_rows=None,  # 使用默认值
    )

    response = await query_service.execute_query(request)

    assert response.success is True
    assert response.data is not None
    # 应该被截断到 hard_max_rows
    assert response.data.row_count <= mock_settings.security.hard_max_rows
    assert response.data.truncated is True


@pytest.mark.asyncio
async def test_max_rows_parameter(mock_settings, mock_db_pool, mock_llm_client, mock_schema_service):
    """P6-1g: max_rows参数测试 - 验证max_rows与hard_max_rows协同，取较小值"""
    from contextlib import asynccontextmanager
    from pg_mcp.infrastructure.db_adapter import PostgreSQLAdapter
    
    mock_adapter = MagicMock(spec=PostgreSQLAdapter)
    mock_rows = [{"id": i} for i in range(500)]
    mock_adapter.fetch = AsyncMock(return_value=mock_rows)
    mock_adapter.fetchval = AsyncMock(return_value="PostgreSQL 15.0")
    mock_adapter.execute = AsyncMock(return_value=1)

    @asynccontextmanager
    async def acquire_readonly_ctx(db_name, timeout=30):
        yield mock_adapter
    
    mock_db_pool.acquire_readonly = acquire_readonly_ctx

    rate_limiter = RateLimiter(mock_settings.rate_limit)
    sanitizer = Sanitizer(mock_settings.security.sensitive_columns)
    validation_service = ValidationService(
        sanitizer,
        mock_llm_client,
        mock_settings.security.validation_sample_rows,
        mock_settings.security.validation_sample_cols,
    )
    metrics = Metrics()
    token_meter = TokenMeter(metrics)
    log_sanitizer = LogSanitizer(mock_settings.security.sensitive_columns)

    query_service = QueryService(
        mock_settings,
        mock_db_pool,
        mock_schema_service,
        mock_llm_client,
        rate_limiter,
        metrics,
        token_meter,
        log_sanitizer,
        validation_service,
    )

    # 测试 max_rows < hard_max_rows
    request1 = QueryRequest(
        query="查询数据",
        database="test_db",
        schema_name="public",
        return_type="result",
        max_rows=100,  # 小于 hard_max_rows=1000
    )

    response1 = await query_service.execute_query(request1)
    assert response1.success is True
    assert response1.data is not None
    assert response1.data.row_count <= 100

    # 测试 max_rows > hard_max_rows（应该取 hard_max_rows）
    request2 = QueryRequest(
        query="查询数据",
        database="test_db",
        schema_name="public",
        return_type="result",
        max_rows=2000,  # 大于 hard_max_rows=1000
    )

    response2 = await query_service.execute_query(request2)
    assert response2.success is True
    assert response2.data is not None
    assert response2.data.row_count <= mock_settings.security.hard_max_rows

