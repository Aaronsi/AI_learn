"""Unit tests for access control."""

import pytest

from pg_mcp.security.access_control import AccessControl
from pg_mcp.security.sanitizer import Sanitizer
from pg_mcp.models.schema import DatabaseInfo, SchemaInfo, TableInfo, ColumnInfo
from pg_mcp.models.errors import SecurityViolationError


def build_db_info() -> DatabaseInfo:
    schema_info = SchemaInfo(name="public")
    schema_info.tables["users"] = TableInfo(
        schema_name="public",
        table_name="users",
        columns=[
            ColumnInfo(name="id", data_type="integer", nullable=False),
            ColumnInfo(name="email", data_type="varchar", nullable=True),
            ColumnInfo(name="password", data_type="varchar", nullable=True),
        ],
    )
    schema_info.tables["orders"] = TableInfo(
        schema_name="public",
        table_name="orders",
        columns=[
            ColumnInfo(name="id", data_type="integer", nullable=False),
            ColumnInfo(name="user_id", data_type="integer", nullable=False),
        ],
    )
    return DatabaseInfo(name="test_db", schemas={"public": schema_info})


def test_access_control_allows_known_tables_and_columns():
    sanitizer = Sanitizer(["password"])
    access_control = AccessControl(sanitizer)
    db_info = build_db_info()

    sql = "SELECT users.id, orders.user_id FROM users JOIN orders ON users.id = orders.user_id"
    access_control.validate_or_raise(sql, db_info, "public")


def test_access_control_blocks_unknown_table():
    sanitizer = Sanitizer(["password"])
    access_control = AccessControl(sanitizer)
    db_info = build_db_info()

    with pytest.raises(SecurityViolationError):
        access_control.validate_or_raise(
            "SELECT * FROM secrets", db_info, "public"
        )


def test_access_control_blocks_sensitive_columns():
    sanitizer = Sanitizer(["password"])
    access_control = AccessControl(sanitizer)
    db_info = build_db_info()

    with pytest.raises(SecurityViolationError):
        access_control.validate_or_raise(
            "SELECT password FROM users", db_info, "public"
        )


def test_access_control_blocks_select_star_on_sensitive_table():
    sanitizer = Sanitizer(["password"])
    access_control = AccessControl(sanitizer)
    db_info = build_db_info()

    with pytest.raises(SecurityViolationError):
        access_control.validate_or_raise("SELECT * FROM users", db_info, "public")


def test_access_control_allows_cte_reference():
    sanitizer = Sanitizer(["password"])
    access_control = AccessControl(sanitizer)
    db_info = build_db_info()

    sql = "WITH u AS (SELECT id FROM users) SELECT * FROM u"
    access_control.validate_or_raise(sql, db_info, "public")

