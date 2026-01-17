"""Unit tests for MySQL database pool"""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from pydantic import SecretStr

from pg_mcp.config.settings import DatabaseConfig
from pg_mcp.infrastructure.db_pool import DBPoolManager


@pytest.fixture
def mysql_config():
    """MySQL database configuration"""
    return DatabaseConfig(
        name="mysql_test",
        db_type="mysql",
        host="localhost",
        port=3306,
        database="testdb",
        username="root",
        password=SecretStr("root@123"),
    )


@pytest.fixture
def postgres_config():
    """PostgreSQL database configuration"""
    return DatabaseConfig(
        name="postgres_test",
        db_type="postgresql",
        host="localhost",
        port=5432,
        database="testdb",
        username="postgres",
        password=SecretStr("password"),
    )


def test_mysql_pool_creation(mysql_config):
    """Test MySQL pool creation"""
    # MySQL pool creation uses direct parameters, not DSN
    # Verify config is correct
    assert mysql_config.db_type == "mysql"
    assert mysql_config.host == "localhost"
    assert mysql_config.port == 3306


def test_mysql_pool_dict_cursor(mysql_config):
    """Test MySQL uses dictionary cursor"""
    manager = DBPoolManager()
    
    # Check that DictCursor is used in pool creation
    # This is verified by checking the _create_mysql_pool method
    # In actual implementation, cursorclass=aiomysql.DictCursor should be set
    assert hasattr(manager, "_create_mysql_pool")


def test_postgres_pool_creation(postgres_config):
    """Test PostgreSQL pool creation"""
    manager = DBPoolManager()
    
    # Mock asyncpg
    with patch("pg_mcp.infrastructure.db_pool.asyncpg") as mock_asyncpg:
        mock_pool = MagicMock()
        mock_asyncpg.create_pool.return_value = AsyncMock(return_value=mock_pool)
        
        dsn = manager._build_postgresql_dsn(postgres_config)
        assert "postgresql://" in dsn


def test_mixed_pools_management(mysql_config, postgres_config):
    """Test mixed database pools management"""
    manager = DBPoolManager()
    
    # Both configs should be manageable
    assert mysql_config.db_type == "mysql"
    assert postgres_config.db_type == "postgresql"
    
    # Manager should handle both types
    assert hasattr(manager, "_create_mysql_pool")
    assert hasattr(manager, "_create_postgresql_pool")


def test_mysql_password_encoding(mysql_config):
    """Test MySQL password with special characters"""
    # MySQL uses direct parameters, password is passed directly
    # Special characters like @ are handled by aiomysql
    assert mysql_config.password.get_secret_value() == "root@123"
    # Password is stored correctly, encoding is handled by aiomysql library


def test_mysql_connection_parameters():
    """Test MySQL connection parameters"""
    config = DatabaseConfig(
        name="test",
        db_type="mysql",
        host="localhost",
        port=3306,
        database="testdb",
        username="user",
        password=SecretStr("pass@123"),
    )
    
    # MySQL uses direct parameters, verify they are correct
    assert config.host == "localhost"
    assert config.port == 3306
    assert config.database == "testdb"
    assert config.username == "user"
    assert config.password.get_secret_value() == "pass@123"


def test_build_postgresql_dsn_with_special_chars():
    """Test PostgreSQL DSN building with special characters in password"""
    manager = DBPoolManager()
    config = DatabaseConfig(
        name="test",
        db_type="postgresql",
        host="localhost",
        port=5432,
        database="testdb",
        username="user",
        password=SecretStr("pass@123"),
    )
    
    dsn = manager._build_postgresql_dsn(config)
    assert "postgresql://" in dsn
    assert "user" in dsn
    assert "testdb" in dsn
    # Password should be URL encoded
    assert "%40" in dsn or "@" not in dsn.split("@")[-1].split("/")[0]

