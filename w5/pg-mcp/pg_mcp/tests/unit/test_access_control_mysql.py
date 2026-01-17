"""Unit tests for MySQL access control"""

import pytest
from pg_mcp.security.access_control import AccessControl
from pg_mcp.security.sanitizer import Sanitizer
from pg_mcp.models.schema import DatabaseInfo, SchemaInfo, TableInfo, ColumnInfo
from pg_mcp.models.errors import SecurityViolationError


def build_mysql_db_info() -> DatabaseInfo:
    """Build MySQL database info for testing"""
    schema_info = SchemaInfo(name="test_schema")
    schema_info.tables["users"] = TableInfo(
        schema_name="test_schema",
        table_name="users",
        columns=[
            ColumnInfo(name="id", data_type="int", nullable=False),
            ColumnInfo(name="email", data_type="varchar", nullable=True),
            ColumnInfo(name="password", data_type="varchar", nullable=True),
        ],
    )
    schema_info.tables["orders"] = TableInfo(
        schema_name="test_schema",
        table_name="orders",
        columns=[
            ColumnInfo(name="id", data_type="int", nullable=False),
            ColumnInfo(name="user_id", data_type="int", nullable=False),
        ],
    )
    return DatabaseInfo(name="mysql_test_db", schemas={"test_schema": schema_info})


def test_mysql_table_access_control():
    """Test MySQL table access control"""
    sanitizer = Sanitizer(["password"])
    access_control = AccessControl(sanitizer)
    db_info = build_mysql_db_info()

    # Valid query
    sql = "SELECT users.id, orders.user_id FROM users JOIN orders ON users.id = orders.user_id"
    access_control.validate_or_raise(sql, db_info, "test_schema")

    # Invalid table
    with pytest.raises(SecurityViolationError):
        access_control.validate_or_raise(
            "SELECT * FROM unknown_table", db_info, "test_schema"
        )


def test_postgres_table_access_control():
    """Test PostgreSQL table access control"""
    sanitizer = Sanitizer(["password"])
    access_control = AccessControl(sanitizer)
    db_info = build_mysql_db_info()  # Same structure for testing

    sql = "SELECT users.id, orders.user_id FROM users JOIN orders ON users.id = orders.user_id"
    access_control.validate_or_raise(sql, db_info, "test_schema")


def test_mysql_sensitive_column_filtering():
    """Test MySQL sensitive column filtering"""
    sanitizer = Sanitizer(["password"])
    access_control = AccessControl(sanitizer)
    db_info = build_mysql_db_info()

    # Should block direct access to password column
    with pytest.raises(SecurityViolationError):
        access_control.validate_or_raise(
            "SELECT password FROM users", db_info, "test_schema"
        )

    # Should block SELECT * on table with sensitive columns
    with pytest.raises(SecurityViolationError):
        access_control.validate_or_raise(
            "SELECT * FROM users", db_info, "test_schema"
        )

    # Should allow SELECT * from CTE that doesn't include sensitive columns
    sql = "WITH u AS (SELECT id, email FROM users) SELECT * FROM u"
    access_control.validate_or_raise(sql, db_info, "test_schema")


def test_cross_database_access_blocked():
    """Test cross-database access is blocked"""
    sanitizer = Sanitizer(["password"])
    access_control = AccessControl(sanitizer)
    db_info = build_mysql_db_info()

    # This should be blocked by schema isolation
    # The test depends on how schema isolation is implemented
    # For now, we test that accessing a different schema raises an error
    other_schema = SchemaInfo(name="other_schema")
    other_schema.tables["other_table"] = TableInfo(
        schema_name="other_schema",
        table_name="other_table",
        columns=[ColumnInfo(name="id", data_type="int", nullable=False)],
    )
    db_info.schemas["other_schema"] = other_schema

    # Accessing other schema should be blocked if schema_name doesn't match
    with pytest.raises(SecurityViolationError):
        access_control.validate_or_raise(
            "SELECT * FROM other_table", db_info, "test_schema"
        )


def test_mysql_cte_access_control():
    """Test MySQL CTE access control"""
    sanitizer = Sanitizer(["password"])
    access_control = AccessControl(sanitizer)
    db_info = build_mysql_db_info()

    # CTE with SELECT * from non-sensitive columns should be allowed
    sql = "WITH u AS (SELECT id, email FROM users) SELECT * FROM u"
    access_control.validate_or_raise(sql, db_info, "test_schema")

    # CTE that includes sensitive column should be blocked
    with pytest.raises(SecurityViolationError):
        access_control.validate_or_raise(
            "WITH u AS (SELECT id, password FROM users) SELECT * FROM u",
            db_info,
            "test_schema",
        )


def test_mysql_schema_isolation():
    """Test MySQL schema isolation"""
    sanitizer = Sanitizer(["password"])
    access_control = AccessControl(sanitizer)
    
    # Create database with multiple schemas
    schema1 = SchemaInfo(name="schema1")
    schema1.tables["table1"] = TableInfo(
        schema_name="schema1",
        table_name="table1",
        columns=[ColumnInfo(name="id", data_type="int", nullable=False)],
    )
    
    schema2 = SchemaInfo(name="schema2")
    schema2.tables["table2"] = TableInfo(
        schema_name="schema2",
        table_name="table2",
        columns=[ColumnInfo(name="id", data_type="int", nullable=False)],
    )
    
    db_info = DatabaseInfo(
        name="test_db",
        schemas={"schema1": schema1, "schema2": schema2},
    )

    # Accessing schema1 table from schema1 should work
    access_control.validate_or_raise("SELECT * FROM table1", db_info, "schema1")

    # Accessing schema2 table from schema1 should be blocked
    with pytest.raises(SecurityViolationError):
        access_control.validate_or_raise("SELECT * FROM table2", db_info, "schema1")

