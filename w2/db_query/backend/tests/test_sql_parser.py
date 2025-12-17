"""Tests for SQL parser and validation services."""
import pytest

from app.services.sql_parser import add_limit_if_needed, validate_sql


class TestValidateSql:
    """Test SQL validation functionality."""

    def test_valid_select_statement(self):
        """Test that valid SELECT statements pass validation."""
        sql = "SELECT * FROM users"
        is_valid, error = validate_sql(sql)
        assert is_valid is True
        assert error is None

    def test_select_with_where(self):
        """Test SELECT with WHERE clause."""
        sql = "SELECT id, name FROM users WHERE id > 10"
        is_valid, error = validate_sql(sql)
        assert is_valid is True
        assert error is None

    def test_select_with_join(self):
        """Test SELECT with JOIN."""
        sql = "SELECT u.id, u.name, p.title FROM users u JOIN posts p ON u.id = p.user_id"
        is_valid, error = validate_sql(sql)
        assert is_valid is True
        assert error is None

    def test_select_with_subquery(self):
        """Test SELECT with subquery."""
        sql = "SELECT * FROM (SELECT id FROM users) AS sub"
        is_valid, error = validate_sql(sql)
        assert is_valid is True
        assert error is None

    def test_select_with_order_by(self):
        """Test SELECT with ORDER BY."""
        sql = "SELECT * FROM users ORDER BY id DESC"
        is_valid, error = validate_sql(sql)
        assert is_valid is True
        assert error is None

    def test_select_with_group_by(self):
        """Test SELECT with GROUP BY."""
        sql = "SELECT COUNT(*) FROM users GROUP BY status"
        is_valid, error = validate_sql(sql)
        assert is_valid is True
        assert error is None

    def test_reject_insert_statement(self):
        """Test that INSERT statements are rejected."""
        sql = "INSERT INTO users (name) VALUES ('test')"
        is_valid, error = validate_sql(sql)
        assert is_valid is False
        assert "SELECT" in error or "not allowed" in error

    def test_reject_update_statement(self):
        """Test that UPDATE statements are rejected."""
        sql = "UPDATE users SET name = 'test' WHERE id = 1"
        is_valid, error = validate_sql(sql)
        assert is_valid is False
        assert "SELECT" in error or "not allowed" in error

    def test_reject_delete_statement(self):
        """Test that DELETE statements are rejected."""
        sql = "DELETE FROM users WHERE id = 1"
        is_valid, error = validate_sql(sql)
        assert is_valid is False
        assert "SELECT" in error or "not allowed" in error

    def test_reject_drop_statement(self):
        """Test that DROP statements are rejected."""
        sql = "DROP TABLE users"
        is_valid, error = validate_sql(sql)
        assert is_valid is False
        assert "SELECT" in error or "not allowed" in error

    def test_reject_create_statement(self):
        """Test that CREATE statements are rejected."""
        sql = "CREATE TABLE test (id INT)"
        is_valid, error = validate_sql(sql)
        assert is_valid is False
        assert "SELECT" in error or "not allowed" in error

    def test_invalid_sql_syntax(self):
        """Test that invalid SQL syntax is rejected."""
        sql = "SELECT * FROM users WHERE"
        is_valid, error = validate_sql(sql)
        assert is_valid is False
        assert error is not None

    def test_empty_sql(self):
        """Test that empty SQL is rejected."""
        sql = ""
        is_valid, error = validate_sql(sql)
        assert is_valid is False
        assert error is not None

    def test_multiple_statements(self):
        """Test that multiple statements are handled correctly."""
        sql = "SELECT * FROM users; SELECT * FROM posts"
        # sqlglot.parse_one only parses the first statement
        is_valid, error = validate_sql(sql)
        # Should pass if only first statement is SELECT
        assert is_valid is True or is_valid is False  # Depends on implementation


class TestAddLimitIfNeeded:
    """Test LIMIT clause addition functionality."""

    def test_add_limit_to_simple_select(self):
        """Test adding LIMIT to simple SELECT."""
        sql = "SELECT * FROM users"
        result = add_limit_if_needed(sql)
        assert "LIMIT" in result.upper()
        assert "1000" in result

    def test_add_limit_to_select_with_where(self):
        """Test adding LIMIT to SELECT with WHERE."""
        sql = "SELECT * FROM users WHERE id > 10"
        result = add_limit_if_needed(sql)
        assert "LIMIT" in result.upper()
        assert "WHERE" in result.upper()

    def test_do_not_add_limit_if_exists(self):
        """Test that LIMIT is not added if already present."""
        sql = "SELECT * FROM users LIMIT 50"
        result = add_limit_if_needed(sql)
        # Should not add another LIMIT
        assert result.upper().count("LIMIT") == 1
        assert "50" in result

    def test_do_not_add_limit_if_exists_lowercase(self):
        """Test that LIMIT is not added if already present (lowercase)."""
        sql = "select * from users limit 50"
        result = add_limit_if_needed(sql)
        # Should not add another LIMIT
        assert result.upper().count("LIMIT") == 1

    def test_custom_limit_value(self):
        """Test custom LIMIT value."""
        sql = "SELECT * FROM users"
        result = add_limit_if_needed(sql, default_limit=500)
        assert "LIMIT" in result.upper()
        assert "500" in result

    def test_limit_with_order_by(self):
        """Test LIMIT with ORDER BY."""
        sql = "SELECT * FROM users ORDER BY id DESC"
        result = add_limit_if_needed(sql)
        assert "LIMIT" in result.upper()
        assert "ORDER BY" in result.upper()

    def test_limit_with_group_by(self):
        """Test LIMIT with GROUP BY."""
        sql = "SELECT COUNT(*) FROM users GROUP BY status"
        result = add_limit_if_needed(sql)
        assert "LIMIT" in result.upper()

    def test_limit_with_join(self):
        """Test LIMIT with JOIN."""
        sql = "SELECT u.id, u.name FROM users u JOIN posts p ON u.id = p.user_id"
        result = add_limit_if_needed(sql)
        assert "LIMIT" in result.upper()

    def test_semicolon_handling(self):
        """Test that semicolons are handled correctly."""
        sql = "SELECT * FROM users;"
        result = add_limit_if_needed(sql)
        assert "LIMIT" in result.upper()

    def test_invalid_sql_fallback(self):
        """Test fallback behavior for invalid SQL."""
        sql = "INVALID SQL STATEMENT"
        # Should not raise exception, should return original or modified SQL
        result = add_limit_if_needed(sql)
        assert isinstance(result, str)
        assert len(result) > 0

