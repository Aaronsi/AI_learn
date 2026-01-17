"""Integration tests for database pool (requires PostgreSQL)"""

import pytest
from pg_mcp.infrastructure.db_pool import DBPoolManager
from pg_mcp.config.settings import DatabaseConfig
from pydantic import SecretStr


@pytest.mark.asyncio
@pytest.mark.integration
async def test_db_pool_connection():
    """Test database pool connection (requires real PostgreSQL)"""
    # This test requires a real PostgreSQL instance
    # Skip if not available
    pytest.skip("Requires real PostgreSQL instance")


@pytest.mark.asyncio
async def test_db_pool_manager_initialization():
    """Test DBPoolManager initialization"""
    manager = DBPoolManager()
    assert manager._pools == {}
    assert manager._configs == {}
    assert manager.list_databases() == []


@pytest.mark.asyncio
async def test_build_dsn():
    """Test DSN building"""
    manager = DBPoolManager()
    config = DatabaseConfig(
        name="test",
        db_type="postgresql",
        host="localhost",
        port=5432,
        database="testdb",
        username="user",
        password=SecretStr("pass"),
        ssl_mode="prefer",
    )
    dsn = manager._build_postgresql_dsn(config)
    assert "postgresql://user:pass@localhost:5432/testdb" in dsn
    assert "sslmode=prefer" in dsn

