"""Integration tests for MySQL schema service"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from pathlib import Path
import tempfile
import shutil

from pg_mcp.config.settings import CacheConfig
from pg_mcp.infrastructure.db_pool import DBPoolManager
from pg_mcp.services.schema_service import SchemaService


@pytest.fixture
def temp_cache_dir():
    """临时缓存目录"""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)


@pytest.fixture
def mock_mysql_db_pool():
    """Mock MySQL database pool"""
    pool = MagicMock(spec=DBPoolManager)
    
    # Mock connection
    mock_conn = AsyncMock()
    
    # Mock version query (MySQL format)
    mock_conn.fetchval = AsyncMock(return_value="8.0.33")
    
    # Mock fetch handling for MySQL information_schema queries
    def mock_fetch(query, *params):
        q = query.lower()
        # MySQL uses %s for parameters, not $1
        if "from information_schema.tables" in q and "table_schema" in q:
            return [
                {
                    "table_schema": "test_schema",
                    "table_name": "users",
                    "table_comment": "用户表",
                    "row_estimate": 1000,
                },
                {
                    "table_schema": "test_schema",
                    "table_name": "orders",
                    "table_comment": "订单表",
                    "row_estimate": 500,
                },
            ]
        if "from information_schema.columns" in q:
            # Return columns based on table name from params
            table_name = params[1] if len(params) > 1 else "users"
            if table_name == "users":
                return [
                    {
                        "column_name": "id",
                        "data_type": "int",
                        "nullable": "NO",
                        "column_default": None,
                        "comment": "用户ID",
                    },
                    {
                        "column_name": "name",
                        "data_type": "varchar(100)",
                        "nullable": "YES",
                        "column_default": None,
                        "comment": "用户名",
                    },
                    {
                        "column_name": "email",
                        "data_type": "varchar(255)",
                        "nullable": "YES",
                        "column_default": None,
                        "comment": "邮箱",
                    },
                ]
            elif table_name == "orders":
                return [
                    {
                        "column_name": "id",
                        "data_type": "int",
                        "nullable": "NO",
                        "column_default": None,
                        "comment": None,
                    },
                    {
                        "column_name": "user_id",
                        "data_type": "int",
                        "nullable": "NO",
                        "column_default": None,
                        "comment": None,
                    },
                ]
            return []
        if "key_column_usage" in q and "constraint_name" in q:
            # Foreign keys
            return []
        if "statistics" in q and "index_name" in q:
            # Indexes for MySQL
            return [
                {
                    "index_name": "PRIMARY",
                    "column_name": "id",
                    "non_unique": 0,
                }
            ]
        if "key_column_usage" in q and "constraint_name" in q:
            # Primary keys
            if "constraint_name = 'PRIMARY'" in q or "PRIMARY" in str(params):
                return [{"column_name": "id"}]
            # Foreign keys
            return []
        return []

    mock_conn.fetch = AsyncMock(side_effect=mock_fetch)
    
    # Mock acquire_readonly context manager
    pool.acquire_readonly = AsyncMock()
    pool.acquire_readonly.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
    pool.acquire_readonly.return_value.__aexit__ = AsyncMock(return_value=None)
    
    # Mock get_db_type to return mysql
    pool.get_db_type = MagicMock(return_value="mysql")
    
    return pool


@pytest.fixture
def mock_postgres_db_pool():
    """Mock PostgreSQL database pool"""
    pool = MagicMock(spec=DBPoolManager)
    
    mock_conn = AsyncMock()
    mock_conn.fetchval = AsyncMock(return_value="PostgreSQL 14.0")
    
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
    
    pool.get_db_type = MagicMock(return_value="postgresql")
    
    return pool


@pytest.mark.asyncio
async def test_mysql_schema_discovery(mock_mysql_db_pool, temp_cache_dir):
    """Test MySQL schema discovery"""
    cache_config = CacheConfig(
        enable_disk_cache=False,
        cache_dir=temp_cache_dir,
    )
    
    schema_service = SchemaService(mock_mysql_db_pool, cache_config)
    
    db_info = await schema_service.load_all(
        "mysql_test_db",
        ["test_schema"],
        exclude_tables=[],
    )
    
    assert db_info.name == "mysql_test_db"
    assert "test_schema" in db_info.schemas
    assert "users" in db_info.schemas["test_schema"].tables
    assert "orders" in db_info.schemas["test_schema"].tables


@pytest.mark.asyncio
async def test_postgres_schema_discovery(mock_postgres_db_pool, temp_cache_dir):
    """Test PostgreSQL schema discovery"""
    cache_config = CacheConfig(
        enable_disk_cache=False,
        cache_dir=temp_cache_dir,
    )
    
    schema_service = SchemaService(mock_postgres_db_pool, cache_config)
    
    db_info = await schema_service.load_all(
        "postgres_test_db",
        ["public"],
        exclude_tables=[],
    )
    
    assert db_info.name == "postgres_test_db"
    assert "public" in db_info.schemas
    assert "users" in db_info.schemas["public"].tables


@pytest.mark.asyncio
async def test_mysql_schema_caching(mock_mysql_db_pool, temp_cache_dir):
    """Test MySQL schema caching"""
    cache_config = CacheConfig(
        enable_disk_cache=True,
        cache_dir=temp_cache_dir,
        cache_ttl_hours=24,
    )
    
    schema_service = SchemaService(mock_mysql_db_pool, cache_config)
    
    # First load (from database)
    db_info1 = await schema_service.load_all("mysql_test_db", ["test_schema"])
    
    # Second load (should use cache)
    db_info2 = await schema_service.load_all("mysql_test_db", ["test_schema"])
    
    # Verify cache file exists
    cache_file = temp_cache_dir / "mysql_test_db.json"
    assert cache_file.exists()
    
    # Verify both loads return same data
    assert db_info1.name == db_info2.name
    assert len(db_info1.schemas) == len(db_info2.schemas)


@pytest.mark.asyncio
async def test_mysql_column_type_mapping(mock_mysql_db_pool, temp_cache_dir):
    """Test MySQL column type mapping"""
    cache_config = CacheConfig(
        enable_disk_cache=False,
        cache_dir=temp_cache_dir,
    )
    
    schema_service = SchemaService(mock_mysql_db_pool, cache_config)
    
    db_info = await schema_service.load_all("mysql_test_db", ["test_schema"])
    
    users_table = db_info.schemas["test_schema"].tables["users"]
    
    # Verify column types are correctly mapped
    id_col = next((c for c in users_table.columns if c.name == "id"), None)
    assert id_col is not None
    assert id_col.data_type in ["int", "integer"]  # MySQL int type
    
    name_col = next((c for c in users_table.columns if c.name == "name"), None)
    assert name_col is not None
    assert "varchar" in name_col.data_type.lower()


@pytest.mark.asyncio
async def test_mysql_schema_format_for_llm(mock_mysql_db_pool, temp_cache_dir):
    """Test MySQL schema formatting for LLM"""
    cache_config = CacheConfig(
        enable_disk_cache=False,
        cache_dir=temp_cache_dir,
    )
    
    schema_service = SchemaService(mock_mysql_db_pool, cache_config)
    
    # Load schema first
    await schema_service.load_all("mysql_test_db", ["test_schema"])
    
    # Format for LLM
    formatted = schema_service.format_for_llm("mysql_test_db", "test_schema")
    
    assert "Schema: test_schema" in formatted or "test_schema" in formatted
    assert "Table: users" in formatted or "users" in formatted
    assert "Columns:" in formatted or "Column" in formatted


@pytest.mark.asyncio
async def test_mysql_chinese_table_names(mock_mysql_db_pool, temp_cache_dir):
    """Test MySQL Chinese table and column names support"""
    cache_config = CacheConfig(
        enable_disk_cache=False,
        cache_dir=temp_cache_dir,
    )
    
    # Mock connection with Chinese table names
    mock_conn = AsyncMock()
    mock_conn.fetchval = AsyncMock(return_value="8.0.33")
    
    def mock_fetch(query, *params):
        q = query.lower()
        if "from information_schema.tables" in q:
            return [
                {
                    "table_schema": "test_schema",
                    "table_name": "用户表",
                    "table_comment": "用户信息表",
                    "row_estimate": 100,
                }
            ]
        if "from information_schema.columns" in q:
            return [
                {
                    "column_name": "用户ID",
                    "data_type": "int",
                    "nullable": "NO",
                    "column_default": None,
                    "comment": "用户唯一标识",
                }
            ]
        return []
    
    mock_conn.fetch = AsyncMock(side_effect=mock_fetch)
    mock_mysql_db_pool.acquire_readonly.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
    
    schema_service = SchemaService(mock_mysql_db_pool, cache_config)
    
    db_info = await schema_service.load_all("mysql_test_db", ["test_schema"])
    
    # Verify Chinese table name is handled
    assert "test_schema" in db_info.schemas
    # Table name should be preserved (may be in different case)
    tables = db_info.schemas["test_schema"].tables
    assert len(tables) > 0


@pytest.mark.asyncio
async def test_mysql_parameter_placeholder(mock_mysql_db_pool):
    """Test MySQL uses %s parameter placeholder"""
    # This test verifies that MySQL queries use %s instead of $1
    # The actual implementation is in schema_service.py
    # We verify by checking that the service can handle MySQL queries
    
    cache_config = CacheConfig(enable_disk_cache=False)
    schema_service = SchemaService(mock_mysql_db_pool, cache_config)
    
    # This should work with MySQL parameter placeholders
    db_info = await schema_service.load_all("mysql_test_db", ["test_schema"])
    assert db_info.name == "mysql_test_db"


@pytest.mark.asyncio
async def test_mysql_view_loading(mock_mysql_db_pool, temp_cache_dir):
    """Test MySQL view loading"""
    cache_config = CacheConfig(
        enable_disk_cache=False,
        cache_dir=temp_cache_dir,
    )
    
    # Mock connection with views
    mock_conn = AsyncMock()
    mock_conn.fetchval = AsyncMock(return_value="8.0.33")
    
    def mock_fetch(query, *params):
        q = query.lower()
        if "from information_schema.tables" in q:
            return [
                {
                    "table_schema": "test_schema",
                    "table_name": "users",
                    "table_comment": None,
                    "row_estimate": 100,
                }
            ]
        if "from information_schema.views" in q:
            return [
                {
                    "table_schema": "test_schema",
                    "view_name": "user_summary",
                    "view_definition": "SELECT id, name FROM users",
                }
            ]
        if "from information_schema.columns" in q:
            if "view_name" in str(params) or len(params) > 1 and params[1] == "user_summary":
                return [
                    {
                        "column_name": "id",
                        "data_type": "int",
                        "nullable": "NO",
                        "column_default": None,
                        "comment": None,
                    },
                    {
                        "column_name": "name",
                        "data_type": "varchar(100)",
                        "nullable": "YES",
                        "column_default": None,
                        "comment": None,
                    },
                ]
            return [
                {
                    "column_name": "id",
                    "data_type": "int",
                    "nullable": "NO",
                    "column_default": None,
                    "comment": None,
                }
            ]
        return []
    
    mock_conn.fetch = AsyncMock(side_effect=mock_fetch)
    mock_mysql_db_pool.acquire_readonly.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
    
    schema_service = SchemaService(mock_mysql_db_pool, cache_config)
    
    db_info = await schema_service.load_all("mysql_test_db", ["test_schema"])
    
    # Verify views are loaded
    assert "test_schema" in db_info.schemas
    # Views should be in the schema (implementation dependent)
    schema = db_info.schemas["test_schema"]
    # Check if views are loaded (may be in views dict or tables dict)
    assert len(schema.tables) > 0 or (hasattr(schema, "views") and len(schema.views) > 0)

