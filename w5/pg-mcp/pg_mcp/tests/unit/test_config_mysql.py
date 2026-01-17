"""Unit tests for MySQL configuration"""

import pytest
from pydantic import ValidationError, SecretStr
from pg_mcp.config.settings import DatabaseConfig


def test_mysql_database_config():
    """Test MySQL database configuration validation"""
    config = DatabaseConfig(
        name="mysql_test",
        db_type="mysql",
        host="localhost",
        port=3306,
        database="testdb",
        username="root",
        password=SecretStr("password123"),
    )
    assert config.name == "mysql_test"
    assert config.db_type == "mysql"
    assert config.host == "localhost"
    assert config.port == 3306
    assert config.database == "testdb"


def test_mysql_password_with_special_chars():
    """Test MySQL password with special characters like @"""
    config = DatabaseConfig(
        name="mysql_test",
        db_type="mysql",
        host="localhost",
        port=3306,
        database="testdb",
        username="root",
        password=SecretStr("root@123"),
    )
    # Password should be stored correctly
    assert config.password.get_secret_value() == "root@123"


def test_mixed_postgres_mysql_config():
    """Test mixed PostgreSQL and MySQL configuration"""
    pg_config = DatabaseConfig(
        name="postgres_test",
        db_type="postgresql",
        host="localhost",
        port=5432,
        database="testdb",
        username="postgres",
        password=SecretStr("password"),
    )
    
    mysql_config = DatabaseConfig(
        name="mysql_test",
        db_type="mysql",
        host="localhost",
        port=3306,
        database="testdb",
        username="root",
        password=SecretStr("password"),
    )
    
    assert pg_config.db_type == "postgresql"
    assert mysql_config.db_type == "mysql"
    assert pg_config.port == 5432
    assert mysql_config.port == 3306


def test_mysql_connection_string_parsing():
    """Test MySQL connection string parsing"""
    # MySQL uses direct parameters, not DSN
    config = DatabaseConfig(
        name="mysql_test",
        db_type="mysql",
        host="localhost",
        port=3306,
        database="testdb",
        username="root",
        password=SecretStr("root@123"),
    )
    
    # Verify config values are correct
    assert config.host == "localhost"
    assert config.port == 3306
    assert config.database == "testdb"
    assert config.username == "root"
    assert config.password.get_secret_value() == "root@123"


def test_db_type_validation():
    """Test db_type field validation"""
    # Valid values
    config1 = DatabaseConfig(
        name="test",
        db_type="postgresql",
        host="localhost",
        port=5432,
        database="test",
        username="user",
        password=SecretStr("pass"),
    )
    assert config1.db_type == "postgresql"
    
    config2 = DatabaseConfig(
        name="test",
        db_type="mysql",
        host="localhost",
        port=3306,
        database="test",
        username="user",
        password=SecretStr("pass"),
    )
    assert config2.db_type == "mysql"
    
    # Invalid value should raise ValidationError
    with pytest.raises(ValidationError):
        DatabaseConfig(
            name="test",
            db_type="invalid",
            host="localhost",
            port=5432,
            database="test",
            username="user",
            password=SecretStr("pass"),
        )


def test_default_db_type():
    """Test default db_type is postgresql"""
    config = DatabaseConfig(
        name="test",
        host="localhost",
        port=5432,
        database="test",
        username="user",
        password=SecretStr("pass"),
    )
    # Default should be postgresql
    assert config.db_type == "postgresql"

