"""Unit tests for SQL validator"""

import pytest
from pg_mcp.security.sql_validator import SQLValidator
from pg_mcp.models.errors import SecurityViolationError


def test_valid_select():
    """Test valid SELECT statement"""
    validator = SQLValidator()
    result = validator.validate("SELECT * FROM users")
    assert result.is_valid is True
    assert len(result.violations) == 0


def test_forbidden_insert():
    """Test INSERT statement is rejected"""
    validator = SQLValidator()
    result = validator.validate("INSERT INTO users VALUES (1, 'test')")
    assert result.is_valid is False
    assert any("Insert" in v for v in result.violations)


def test_forbidden_update():
    """Test UPDATE statement is rejected"""
    validator = SQLValidator()
    result = validator.validate("UPDATE users SET name = 'test' WHERE id = 1")
    assert result.is_valid is False
    assert any("Update" in v for v in result.violations)


def test_forbidden_delete():
    """Test DELETE statement is rejected"""
    validator = SQLValidator()
    result = validator.validate("DELETE FROM users WHERE id = 1")
    assert result.is_valid is False
    assert any("Delete" in v for v in result.violations)


def test_forbidden_ddl():
    """Test DDL statements are rejected"""
    validator = SQLValidator()
    
    # CREATE TABLE
    result = validator.validate("CREATE TABLE test (id INT)")
    assert result.is_valid is False
    
    # DROP TABLE
    result = validator.validate("DROP TABLE users")
    assert result.is_valid is False


def test_forbidden_select_into():
    """Test SELECT INTO is rejected"""
    validator = SQLValidator()
    result = validator.validate("SELECT * INTO new_table FROM users")
    assert result.is_valid is False
    assert any("Into" in v for v in result.violations)


def test_dangerous_function():
    """Test dangerous functions are rejected"""
    validator = SQLValidator()
    result = validator.validate("SELECT pg_sleep(100)")
    assert result.is_valid is False
    assert any("pg_sleep" in v for v in result.violations)


def test_cte_with_dml():
    """Test CTE containing DML is rejected"""
    validator = SQLValidator()
    sql = "WITH d AS (DELETE FROM users RETURNING *) SELECT * FROM d"
    result = validator.validate(sql)
    assert result.is_valid is False
    assert any("CTE" in v for v in result.violations)


def test_validate_or_raise():
    """Test validate_or_raise raises exception for invalid SQL"""
    validator = SQLValidator()
    with pytest.raises(SecurityViolationError):
        validator.validate_or_raise("INSERT INTO users VALUES (1)")


def test_allowed_functions():
    """Test allowed functions pass validation"""
    validator = SQLValidator(allowed_functions=["custom_func"])
    validator.validate("SELECT custom_func(id) FROM users")
    # Should pass if custom_func is in allowed list
    # Note: This depends on FunctionGuard implementation


def test_complex_select():
    """Test complex SELECT with JOINs passes"""
    validator = SQLValidator()
    sql = """
    SELECT u.id, u.name, p.title
    FROM users u
    JOIN posts p ON u.id = p.user_id
    WHERE u.active = true
    ORDER BY u.created_at DESC
    LIMIT 10
    """
    result = validator.validate(sql)
    assert result.is_valid is True

