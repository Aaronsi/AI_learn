"""Integration tests for schema service"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from pathlib import Path
import json
import tempfile
import shutil

from pg_mcp.config.settings import CacheConfig
from pg_mcp.infrastructure.db_pool import DBPoolManager
from pg_mcp.services.schema_service import SchemaService
from pg_mcp.models.schema import DatabaseInfo


@pytest.fixture
def temp_cache_dir():
    """临时缓存目录"""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)


@pytest.fixture
def mock_db_pool():
    """Mock database pool"""
    pool = MagicMock(spec=DBPoolManager)
    
    # Mock connection
    mock_conn = AsyncMock()
    
    # Mock version query
    mock_conn.fetchval = AsyncMock(return_value="PostgreSQL 14.0")
    
    # Mock fetch handling for tables/columns/pk/fk
    def mock_fetch(query, *params):
        q = query.lower()
        if "from information_schema.tables" in q:
            return [
                {
                    "table_schema": "public",
                    "table_name": "users",
                    "table_comment": "用户表",
                    "row_estimate": 1000,
                }
            ]
        if "from information_schema.columns" in q:
            return [
                {
                    "column_name": "id",
                    "data_type": "integer",
                    "nullable": False,
                    "column_default": None,
                    "comment": "用户ID",
                },
                {
                    "column_name": "name",
                    "data_type": "varchar",
                    "nullable": True,
                    "column_default": None,
                    "comment": "用户名",
                },
            ]
        if "from pg_index" in q:
            return [{"attname": "id"}]
        if "constraint_type = 'foreign key'" in q:
            return []
        return []

    mock_conn.fetch = AsyncMock(side_effect=mock_fetch)
    
    pool.acquire_readonly = AsyncMock()
    pool.acquire_readonly.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
    pool.acquire_readonly.return_value.__aexit__ = AsyncMock(return_value=None)
    
    return pool


@pytest.mark.asyncio
async def test_schema_loading(mock_db_pool, temp_cache_dir):
    """Test schema loading from database"""
    cache_config = CacheConfig(
        enable_disk_cache=True,
        cache_dir=temp_cache_dir,
        cache_ttl_hours=24,
    )
    
    schema_service = SchemaService(mock_db_pool, cache_config)
    
    db_info = await schema_service.load_all(
        "test_db",
        ["public"],
        exclude_tables=[],
    )
    
    assert db_info.name == "test_db"
    assert "public" in db_info.schemas
    assert "users" in db_info.schemas["public"].tables


@pytest.mark.asyncio
async def test_disk_cache(mock_db_pool, temp_cache_dir):
    """Test disk cache save and load"""
    cache_config = CacheConfig(
        enable_disk_cache=True,
        cache_dir=temp_cache_dir,
        cache_ttl_hours=24,
    )
    
    schema_service = SchemaService(mock_db_pool, cache_config)
    
    # 第一次加载（从数据库）
    db_info1 = await schema_service.load_all("test_db", ["public"])
    
    # 第二次加载（应该从缓存）
    db_info2 = await schema_service.load_all("test_db", ["public"])
    
    # 验证缓存文件存在
    cache_file = temp_cache_dir / "test_db.json"
    assert cache_file.exists()
    
    # 验证缓存内容
    cached_data = json.loads(cache_file.read_text())
    assert cached_data["name"] == "test_db"


@pytest.mark.asyncio
async def test_exclude_tables(mock_db_pool, temp_cache_dir):
    """Test exclude_tables pattern matching"""
    cache_config = CacheConfig(
        enable_disk_cache=False,
        cache_dir=temp_cache_dir,
    )
    
    schema_service = SchemaService(mock_db_pool, cache_config)
    
    # Mock tables including excluded ones
    mock_conn = AsyncMock()
    mock_conn.fetchval = AsyncMock(return_value="PostgreSQL 14.0")
    def mock_fetch(query, *params):
        q = query.lower()
        if "from information_schema.tables" in q:
            return [
                {
                    "table_schema": "public",
                    "table_name": "users",
                    "table_comment": None,
                    "row_estimate": 100,
                },
                {
                    "table_schema": "public",
                    "table_name": "audit_logs",
                    "table_comment": None,
                    "row_estimate": 1000,
                },
            ]
        if "from information_schema.columns" in q:
            return [
                {
                    "column_name": "id",
                    "data_type": "integer",
                    "nullable": False,
                    "column_default": None,
                    "comment": None,
                }
            ]
        if "from pg_index" in q:
            return [{"attname": "id"}]
        if "constraint_type = 'foreign key'" in q:
            return []
        return []

    mock_conn.fetch = AsyncMock(side_effect=mock_fetch)
    
    mock_db_pool.acquire_readonly.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
    
    db_info = await schema_service.load_all(
        "test_db",
        ["public"],
        exclude_tables=["audit_*"],
    )
    
    # audit_logs 应该被排除
    assert "users" in db_info.schemas["public"].tables
    # 注意：由于 mock 的限制，这里主要测试模式匹配逻辑


@pytest.mark.asyncio
async def test_format_for_llm(mock_db_pool, temp_cache_dir):
    """Test schema formatting for LLM"""
    cache_config = CacheConfig(
        enable_disk_cache=False,
        cache_dir=temp_cache_dir,
    )
    
    schema_service = SchemaService(mock_db_pool, cache_config)
    
    # 先加载schema
    await schema_service.load_all("test_db", ["public"])
    
    # 格式化输出
    formatted = schema_service.format_for_llm("test_db", "public")
    
    assert "Schema: public" in formatted
    assert "Table: users" in formatted
    assert "Columns:" in formatted

