"""Unit tests for MySQL SQL validator"""

from pg_mcp.security.sql_validator import SQLValidator


def test_mysql_dialect_parsing():
    """Test MySQL SQL parsing with MySQL dialect"""
    validator = SQLValidator(db_type="mysql")
    
    # MySQL specific syntax
    sql = "SELECT * FROM users LIMIT 10 OFFSET 5"
    result = validator.validate(sql, db_type="mysql")
    assert result.is_valid
    
    # MySQL LIMIT syntax: LIMIT offset, count
    sql2 = "SELECT * FROM users LIMIT 5, 10"
    result2 = validator.validate(sql2, db_type="mysql")
    assert result2.is_valid


def test_postgres_dialect_parsing():
    """Test PostgreSQL SQL parsing with PostgreSQL dialect"""
    validator = SQLValidator(db_type="postgresql")
    
    # PostgreSQL syntax
    sql = "SELECT * FROM users LIMIT 10 OFFSET 5"
    result = validator.validate(sql, db_type="postgresql")
    assert result.is_valid


def test_mysql_dangerous_functions():
    """Test MySQL dangerous functions are blocked"""
    validator = SQLValidator(db_type="mysql")
    
    dangerous_sqls = [
        "SELECT SLEEP(5)",
        "SELECT BENCHMARK(1000000, MD5('test'))",
        "SELECT LOAD_FILE('/etc/passwd')",
    ]
    
    for sql in dangerous_sqls:
        result = validator.validate(sql, db_type="mysql")
        # Should be blocked or at least detected
        assert not result.is_valid or any("禁止" in v or "危险" in v for v in result.violations)


def test_postgres_dangerous_functions():
    """Test PostgreSQL dangerous functions are blocked"""
    validator = SQLValidator(db_type="postgresql")
    
    dangerous_sqls = [
        "SELECT pg_sleep(5)",
        "SELECT pg_terminate_backend(12345)",
    ]
    
    for sql in dangerous_sqls:
        result = validator.validate(sql, db_type="postgresql")
        assert not result.is_valid or any("禁止" in v or "危险" in v for v in result.violations)


def test_mysql_safe_functions():
    """Test MySQL safe functions are allowed"""
    validator = SQLValidator(db_type="mysql")
    
    safe_sqls = [
        "SELECT COUNT(*) FROM users",
        "SELECT GROUP_CONCAT(name) FROM users",
        "SELECT CONCAT(first_name, ' ', last_name) FROM users",
        "SELECT DATE_FORMAT(created_at, '%Y-%m-%d') FROM users",
    ]
    
    for sql in safe_sqls:
        result = validator.validate(sql, db_type="mysql")
        # These should be valid
        assert result.is_valid, f"SQL should be valid: {sql}, violations: {result.violations}"


def test_dialect_specific_syntax():
    """Test database-specific syntax differences"""
    validator_mysql = SQLValidator(db_type="mysql")
    validator_postgres = SQLValidator(db_type="postgresql")
    
    # MySQL uses backticks for identifiers
    mysql_sql = "SELECT * FROM `users` WHERE `id` = 1"
    result_mysql = validator_mysql.validate(mysql_sql, db_type="mysql")
    assert result_mysql.is_valid
    
    # PostgreSQL uses double quotes
    postgres_sql = 'SELECT * FROM "users" WHERE "id" = 1'
    result_postgres = validator_postgres.validate(postgres_sql, db_type="postgresql")
    assert result_postgres.is_valid


def test_mysql_limit_syntax():
    """Test MySQL LIMIT syntax variations"""
    validator = SQLValidator(db_type="mysql")
    
    # Standard LIMIT n OFFSET m
    sql1 = "SELECT * FROM users LIMIT 10 OFFSET 5"
    result1 = validator.validate(sql1, db_type="mysql")
    assert result1.is_valid
    
    # MySQL specific: LIMIT offset, count
    sql2 = "SELECT * FROM users LIMIT 5, 10"
    result2 = validator.validate(sql2, db_type="mysql")
    assert result2.is_valid


def test_postgres_limit_syntax():
    """Test PostgreSQL LIMIT syntax"""
    validator = SQLValidator(db_type="postgresql")
    
    sql = "SELECT * FROM users LIMIT 10 OFFSET 5"
    result = validator.validate(sql, db_type="postgresql")
    assert result.is_valid


def test_mysql_string_functions():
    """Test MySQL string functions"""
    validator = SQLValidator(db_type="mysql")
    
    sqls = [
        "SELECT CONCAT(first_name, last_name) FROM users",
        "SELECT SUBSTRING(name, 1, 5) FROM users",
        "SELECT CHAR_LENGTH(name) FROM users",
    ]
    
    for sql in sqls:
        result = validator.validate(sql, db_type="mysql")
        assert result.is_valid, f"SQL should be valid: {sql}"


def test_postgres_string_functions():
    """Test PostgreSQL string functions"""
    validator = SQLValidator(db_type="postgresql")
    
    sqls = [
        "SELECT first_name || last_name FROM users",
        "SELECT SUBSTRING(name FROM 1 FOR 5) FROM users",
        "SELECT LENGTH(name) FROM users",
    ]
    
    for sql in sqls:
        result = validator.validate(sql, db_type="postgresql")
        assert result.is_valid, f"SQL should be valid: {sql}"

