"""Security integration tests"""


from pg_mcp.security.sql_validator import SQLValidator
from pg_mcp.security.sanitizer import Sanitizer


class TestSQLInjection:
    """P6-2a: SQL 注入测试"""

    def test_sql_injection_attempts(self):
        """测试各种 SQL 注入尝试"""
        validator = SQLValidator()

        # 尝试注入 DROP TABLE
        malicious_sqls = [
            "SELECT * FROM users; DROP TABLE users; --",
            "SELECT * FROM users WHERE id = 1; DELETE FROM users;",
            "SELECT * FROM users UNION SELECT * FROM passwords",
            "SELECT * FROM users WHERE name = 'admin' OR '1'='1'",
        ]

        for sql in malicious_sqls:
            result = validator.validate(sql)
            # 如果包含多个语句，应该被检测到
            if ";" in sql and any(
                keyword in sql.upper()
                for keyword in ["DROP", "DELETE", "INSERT", "UPDATE"]
            ):
                # 应该被拒绝或至少被检测
                assert (
                    not result.is_valid
                    or any("禁止" in v for v in result.violations)
                )

    def test_comment_injection(self):
        """测试注释注入"""
        validator = SQLValidator()

        # PostgreSQL 注释
        sql = "SELECT * FROM users -- ; DROP TABLE users;"
        result = validator.validate(sql)
        # 注释中的 DROP 不应该被执行，但如果有多个语句会被检测
        assert result.is_valid  # 注释中的内容不应该影响解析

    def test_union_injection(self):
        """测试 UNION 注入"""
        validator = SQLValidator()

        # UNION 本身是合法的，但如果尝试访问敏感表应该被函数守卫拦截
        sql = "SELECT id FROM users UNION SELECT password FROM users"
        result = validator.validate(sql)
        # UNION 本身是合法的 SELECT 操作
        assert result.is_valid


class TestPrivilegeEscalation:
    """P6-2b: 权限提升测试"""

    def test_ddl_statements_blocked(self):
        """测试 DDL 语句被阻止"""
        validator = SQLValidator()

        ddl_statements = [
            "CREATE TABLE test (id INT)",
            "DROP TABLE users",
            "ALTER TABLE users ADD COLUMN test VARCHAR",
            "TRUNCATE TABLE users",
            "CREATE INDEX idx ON users(id)",
        ]

        for sql in ddl_statements:
            result = validator.validate(sql)
            assert not result.is_valid
            assert any("禁止" in v for v in result.violations)

    def test_dml_statements_blocked(self):
        """测试 DML 语句被阻止"""
        validator = SQLValidator()

        dml_statements = [
            "INSERT INTO users VALUES (1, 'test')",
            "UPDATE users SET name = 'test' WHERE id = 1",
            "DELETE FROM users WHERE id = 1",
            "MERGE INTO users USING (SELECT 1) AS src ON users.id = src.id WHEN MATCHED THEN UPDATE SET name = 'test'",
        ]

        for sql in dml_statements:
            result = validator.validate(sql)
            assert not result.is_valid
            # 对于解析失败的SQL，错误消息可能不包含"禁止"，但至少应该被拒绝
            assert len(result.violations) > 0
            # 对于可解析的SQL，应该包含"禁止"
            if not any("解析失败" in v for v in result.violations):
                assert any("禁止" in v for v in result.violations)

    def test_dangerous_functions_blocked(self):
        """测试危险函数被阻止"""
        validator = SQLValidator()

        dangerous_sqls = [
            "SELECT pg_sleep(100)",
            "SELECT pg_terminate_backend(123)",
            "SELECT pg_cancel_backend(123)",
            "SELECT lo_import('/etc/passwd')",
        ]

        for sql in dangerous_sqls:
            result = validator.validate(sql)
            assert not result.is_valid
            assert any("危险函数" in v or "pg_sleep" in v for v in result.violations)

    def test_select_into_blocked(self):
        """测试 SELECT INTO 被阻止"""
        validator = SQLValidator()

        sql = "SELECT * INTO new_table FROM users"
        result = validator.validate(sql)
        assert not result.is_valid
        assert any("Into" in v for v in result.violations)

    def test_cte_with_dml_blocked(self):
        """测试 CTE 中包含 DML 被阻止"""
        validator = SQLValidator()

        sql = "WITH deleted AS (DELETE FROM users RETURNING *) SELECT * FROM deleted"
        result = validator.validate(sql)
        assert not result.is_valid
        assert any("CTE" in v for v in result.violations)


class TestSensitiveDataLeakage:
    """P6-2c: 敏感数据泄露测试"""

    def test_sensitive_columns_filtered(self):
        """测试敏感列被过滤"""
        sanitizer = Sanitizer(["password", "secret", "token"])

        columns = ["id", "name", "email", "password", "secret_key", "token"]
        rows = [
            {
                "id": 1,
                "name": "Alice",
                "email": "alice@example.com",
                "password": "secret123",
                "secret_key": "key123",
                "token": "token123",
            }
        ]

        safe_cols, safe_rows = sanitizer.sanitize_for_llm(columns, rows)

        assert "password" not in safe_cols
        assert "secret_key" not in safe_cols
        assert "token" not in safe_cols
        assert "id" in safe_cols
        assert "name" in safe_cols
        assert "email" in safe_cols

        # 验证行数据也被过滤
        assert "password" not in safe_rows[0]
        assert "secret_key" not in safe_rows[0]
        assert "token" not in safe_rows[0]

    def test_sensitive_data_not_in_summary(self):
        """测试敏感数据不出现在摘要中"""
        sanitizer = Sanitizer(["password", "secret"])

        columns = ["id", "name", "password"]
        rows = [
            {"id": 1, "name": "Alice", "password": "secret123"},
            {"id": 2, "name": "Bob", "password": "secret456"},
        ]

        summary = sanitizer.generate_summary(columns, rows, total_count=2)

        assert "password" not in summary["column_stats"]
        assert "id" in summary["column_stats"]
        assert "name" in summary["column_stats"]

    def test_sensitive_pattern_matching(self):
        """测试敏感模式匹配"""
        sanitizer = Sanitizer(["password", "secret", "token"])

        # 测试各种变体
        assert sanitizer.is_sensitive_column("password") is True
        assert sanitizer.is_sensitive_column("user_password") is True
        assert sanitizer.is_sensitive_column("password_hash") is True
        assert sanitizer.is_sensitive_column("secret_key") is True
        assert sanitizer.is_sensitive_column("api_token") is True
        assert sanitizer.is_sensitive_column("name") is False
        assert sanitizer.is_sensitive_column("email") is False

