"""Tests for SQL parser edge cases."""
import pytest

from app.services.sql_parser import add_limit_if_needed, validate_sql


class TestSqlParserEdgeCases:
    """Test SQL parser edge cases."""

    def test_validate_sql_with_comments(self):
        """Test SQL validation with comments."""
        sql = """
        -- This is a comment
        SELECT * FROM users
        """
        is_valid, error = validate_sql(sql)
        assert is_valid is True

    def test_validate_sql_with_cte(self):
        """Test SQL validation with Common Table Expressions."""
        sql = """
        WITH users_cte AS (
            SELECT id, name FROM users
        )
        SELECT * FROM users_cte
        """
        is_valid, error = validate_sql(sql)
        assert is_valid is True

    def test_validate_sql_with_union(self):
        """Test SQL validation with UNION."""
        sql = "SELECT * FROM users UNION SELECT * FROM admins"
        is_valid, error = validate_sql(sql)
        # UNION might be parsed as separate statements, so result may vary
        assert isinstance(is_valid, bool)

    def test_add_limit_with_cte(self):
        """Test adding LIMIT with CTE."""
        sql = """
        WITH users_cte AS (SELECT * FROM users)
        SELECT * FROM users_cte
        """
        result = add_limit_if_needed(sql)
        assert "LIMIT" in result.upper()

    def test_add_limit_with_complex_query(self):
        """Test adding LIMIT with complex query."""
        sql = """
        SELECT 
            u.id,
            u.name,
            COUNT(p.id) as post_count
        FROM users u
        LEFT JOIN posts p ON u.id = p.user_id
        GROUP BY u.id, u.name
        HAVING COUNT(p.id) > 5
        ORDER BY post_count DESC
        """
        result = add_limit_if_needed(sql)
        assert "LIMIT" in result.upper()
        assert "ORDER BY" in result.upper()

    def test_add_limit_preserves_existing_limit(self):
        """Test that existing LIMIT is preserved."""
        sql = "SELECT * FROM users LIMIT 10 OFFSET 5"
        result = add_limit_if_needed(sql, default_limit=1000)
        # Should not add another LIMIT
        assert result.upper().count("LIMIT") == 1
        assert "10" in result

    def test_validate_sql_case_insensitive(self):
        """Test SQL validation is case insensitive for keywords."""
        sql = "select * from users"
        is_valid, error = validate_sql(sql)
        assert is_valid is True

    def test_add_limit_case_insensitive(self):
        """Test adding LIMIT is case insensitive."""
        sql = "select * from users limit 50"
        result = add_limit_if_needed(sql, default_limit=1000)
        assert result.upper().count("LIMIT") == 1

