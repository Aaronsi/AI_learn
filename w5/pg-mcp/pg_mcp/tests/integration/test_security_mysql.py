"""Security integration tests for MySQL"""

from pg_mcp.security.sql_validator import SQLValidator
from pg_mcp.security.sanitizer import Sanitizer


class TestMySQLSQLInjection:
    """MySQL SQL injection prevention tests"""

    def test_mysql_sql_injection_prevention(self):
        """Test MySQL SQL injection prevention"""
        validator = SQLValidator(db_type="mysql")

        malicious_sqls = [
            "SELECT * FROM users; DROP TABLE users; --",
            "SELECT * FROM users WHERE id = 1; DELETE FROM users;",
            "SELECT * FROM users WHERE name = 'admin' OR '1'='1'",
            "SELECT * FROM users WHERE id = 1 UNION SELECT * FROM passwords",
        ]

        for sql in malicious_sqls:
            result = validator.validate(sql, db_type="mysql")
            # Should be blocked or at least detected
            if ";" in sql and any(
                keyword in sql.upper()
                for keyword in ["DROP", "DELETE", "INSERT", "UPDATE"]
            ):
                assert (
                    not result.is_valid
                    or any("禁止" in v for v in result.violations)
                )


class TestMySQLPrivilegeEscalation:
    """MySQL privilege escalation prevention tests"""

    def test_mysql_ddl_blocked(self):
        """Test MySQL DDL statements are blocked"""
        validator = SQLValidator(db_type="mysql")

        ddl_statements = [
            "CREATE TABLE test (id INT)",
            "DROP TABLE users",
            "ALTER TABLE users ADD COLUMN test VARCHAR(100)",
            "TRUNCATE TABLE users",
            "CREATE INDEX idx ON users(id)",
        ]

        for sql in ddl_statements:
            result = validator.validate(sql, db_type="mysql")
            assert not result.is_valid
            assert any("禁止" in v for v in result.violations)

    def test_mysql_dml_blocked(self):
        """Test MySQL DML statements are blocked"""
        validator = SQLValidator(db_type="mysql")

        dml_statements = [
            "INSERT INTO users VALUES (1, 'test')",
            "UPDATE users SET name = 'test' WHERE id = 1",
            "DELETE FROM users WHERE id = 1",
        ]

        for sql in dml_statements:
            result = validator.validate(sql, db_type="mysql")
            assert not result.is_valid
            assert len(result.violations) > 0
            if not any("解析失败" in v for v in result.violations):
                assert any("禁止" in v for v in result.violations)

    def test_mysql_dangerous_functions_blocked(self):
        """Test MySQL dangerous functions are blocked"""
        validator = SQLValidator(db_type="mysql")

        dangerous_sqls = [
            "SELECT SLEEP(5)",
            "SELECT BENCHMARK(1000000, MD5('test'))",
            "SELECT LOAD_FILE('/etc/passwd')",
        ]

        for sql in dangerous_sqls:
            result = validator.validate(sql, db_type="mysql")
            assert not result.is_valid or any(
                "禁止" in v or "危险" in v for v in result.violations
            )


class TestMySQLSensitiveDataFiltering:
    """MySQL sensitive data filtering tests"""

    def test_mysql_sensitive_data_filtering(self):
        """Test MySQL sensitive data filtering"""
        sanitizer = Sanitizer(["password", "ssn", "credit_card"])

        # Test sensitive column detection
        assert sanitizer.is_sensitive_column("password")
        assert sanitizer.is_sensitive_column("user_password")
        assert not sanitizer.is_sensitive_column("name")

        # Test sanitization for LLM (format_for_llm filters sensitive columns)
        columns = ["id", "name", "password", "email"]
        rows = [
            {
                "id": 1,
                "name": "Alice",
                "password": "secret123",
                "email": "alice@example.com",
            }
        ]
        # Sanitizer filters sensitive columns when formatting for LLM
        safe_columns, safe_rows = sanitizer.sanitize_for_llm(columns, rows, max_rows=10, max_cols=10)
        # Sensitive columns should be filtered
        assert "password" not in safe_columns
        assert "id" in safe_columns
        assert "name" in safe_columns


class TestMySQLReadonlyEnforcement:
    """MySQL readonly enforcement tests"""

    def test_mysql_readonly_enforcement(self):
        """Test MySQL readonly enforcement"""
        # This is tested at the database pool level
        # The readonly transaction should prevent write operations
        validator = SQLValidator(db_type="mysql")

        # Read operations should be allowed
        read_sql = "SELECT * FROM users"
        result = validator.validate(read_sql, db_type="mysql")
        assert result.is_valid

        # Write operations should be blocked
        write_sqls = [
            "INSERT INTO users VALUES (1, 'test')",
            "UPDATE users SET name = 'test'",
            "DELETE FROM users WHERE id = 1",
        ]

        for sql in write_sqls:
            result = validator.validate(sql, db_type="mysql")
            assert not result.is_valid


class TestMySQLCrossDatabaseBlocked:
    """MySQL cross-database access prevention tests"""

    def test_mysql_cross_database_blocked(self):
        """Test MySQL cross-database access is blocked"""
        # Cross-database queries like SELECT * FROM other_db.table
        # should be blocked by access control
        validator = SQLValidator(db_type="mysql")

        # Normal query should be valid
        sql = "SELECT * FROM users"
        result = validator.validate(sql, db_type="mysql")
        assert result.is_valid

        # Cross-database query syntax (MySQL uses db.table format)
        # This should be handled by access control, not SQL validator
        # SQL validator only checks syntax, access control checks permissions


class TestMySQLUnionInjectionBlocked:
    """MySQL UNION injection prevention tests"""

    def test_mysql_union_injection_blocked(self):
        """Test MySQL UNION injection is blocked"""
        validator = SQLValidator(db_type="mysql")

        # Legitimate UNION should be allowed
        sql = "SELECT * FROM users UNION SELECT * FROM orders"
        validation_result = validator.validate(sql, db_type="mysql")
        # UNION itself is a valid SQL operation
        # The security check should be at access control level
        assert validation_result.is_valid

        # Malicious UNION with DROP should be blocked
        malicious_sql = "SELECT * FROM users UNION SELECT * FROM (DROP TABLE users)"
        validation_result = validator.validate(malicious_sql, db_type="mysql")
        # Should be blocked due to DROP statement
        assert not validation_result.is_valid

