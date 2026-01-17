"""SQL access control based on cached schema metadata."""

from __future__ import annotations

import sqlglot
from sqlglot import exp
from sqlglot.errors import ParseError

from pg_mcp.models.errors import SecurityViolationError
from pg_mcp.models.schema import DatabaseInfo
from pg_mcp.security.sanitizer import Sanitizer


class AccessControl:
    """Enforce table/column access rules using cached schema info."""

    def __init__(self, sanitizer: Sanitizer):
        self.sanitizer = sanitizer

    def validate_or_raise(
        self, sql: str, db_info: DatabaseInfo, schema_name: str
    ) -> None:
        """Validate SQL references against schema metadata."""
        schema_info = db_info.schemas.get(schema_name)
        if not schema_info:
            raise SecurityViolationError(
                message="Schema 未加载或不可用",
                sql=sql,
                violation=f"Schema {schema_name} 未在缓存中",
            )

        try:
            stmt = sqlglot.parse_one(sql, dialect="postgres")
        except ParseError as exc:
            raise SecurityViolationError(
                message="SQL解析失败，无法进行访问控制校验",
                sql=sql,
                violation=str(exc),
            )

        available_tables = {
            name.lower() for name in schema_info.tables.keys()
        } | {name.lower() for name in schema_info.views.keys()}
        table_columns = {
            name.lower(): {col.name.lower() for col in table.columns}
            for name, table in schema_info.tables.items()
        }
        view_columns = {
            name.lower(): {col.name.lower() for col in view.columns}
            for name, view in schema_info.views.items()
        }

        cte_names = {self._get_cte_name(cte) for cte in stmt.find_all(exp.CTE)}
        cte_names = {name for name in cte_names if name}

        alias_map: dict[str, str] = {}
        referenced_tables: set[str] = set()
        for table in stmt.find_all(exp.Table):
            table_name = table.name
            if not table_name:
                continue
            table_key = table_name.lower()
            if table_key in cte_names:
                alias_map.update(self._alias_entries(table, table_key))
                continue

            schema = self._get_table_schema(table)
            if schema and schema != schema_name:
                raise SecurityViolationError(
                    message="SQL访问了未授权的schema",
                    sql=sql,
                    violation=f"表 {table_name} 属于schema {schema}",
                )

            if table_key not in available_tables:
                raise SecurityViolationError(
                    message="SQL访问了未授权的表或视图",
                    sql=sql,
                    violation=f"表或视图 {table_name} 不在允许列表中",
                )
            referenced_tables.add(table_key)
            alias_map.update(self._alias_entries(table, table_key))

        for column in stmt.find_all(exp.Column):
            column_name = column.name
            if not column_name:
                continue
            if self.sanitizer.is_sensitive_column(column_name):
                raise SecurityViolationError(
                    message="SQL访问了敏感列",
                    sql=sql,
                    violation=f"敏感列 {column_name} 不允许查询",
                )

            table_alias = (column.table or "").lower()
            if table_alias in cte_names:
                continue

            if table_alias:
                table_key = alias_map.get(table_alias)
                if not table_key:
                    raise SecurityViolationError(
                        message="SQL引用了未知表别名",
                        sql=sql,
                        violation=f"未知表别名 {column.table}",
                    )
                if not self._column_exists(
                    table_key, column_name, table_columns, view_columns
                ):
                    raise SecurityViolationError(
                        message="SQL引用了不存在的列",
                        sql=sql,
                        violation=f"{table_key}.{column_name} 不存在",
                    )
                continue

            if not referenced_tables:
                continue
            if not self._column_in_any_table(
                column_name, referenced_tables, table_columns, view_columns
            ):
                raise SecurityViolationError(
                    message="SQL引用了不存在的列",
                    sql=sql,
                    violation=f"列 {column_name} 不在查询表中",
                )

        for star in stmt.find_all(exp.Star):
            # 检查 SELECT * 是否来自 CTE
            # 找到包含这个 Star 的 SELECT 语句
            select_stmt = star
            while select_stmt and not isinstance(select_stmt, exp.Select):
                select_stmt = select_stmt.parent
            
            if select_stmt:
                # 检查 FROM 子句中的表是否是 CTE
                from_tables = select_stmt.find_all(exp.Table)
                is_from_cte = False
                for table in from_tables:
                    table_name = table.name
                    if table_name and table_name.lower() in cte_names:
                        is_from_cte = True
                        break
                if is_from_cte:
                    # SELECT * FROM CTE，跳过检查（CTE 的定义已经检查过了）
                    continue
            
            table_alias = self._get_star_table(star)
            if table_alias and table_alias.lower() in cte_names:
                continue
            target_tables = referenced_tables
            if table_alias:
                table_key = alias_map.get(table_alias.lower())
                if not table_key:
                    raise SecurityViolationError(
                        message="SQL引用了未知表别名",
                        sql=sql,
                        violation=f"未知表别名 {table_alias}",
                    )
                target_tables = {table_key}
            for table_key in target_tables:
                if self._table_has_sensitive_columns(
                    table_key, table_columns, view_columns
                ):
                    raise SecurityViolationError(
                        message="SQL使用了SELECT * 访问敏感列",
                        sql=sql,
                        violation=f"{table_key} 包含敏感列，禁止SELECT *",
                    )

    def _get_cte_name(self, cte: exp.CTE) -> str | None:
        alias = cte.args.get("alias")
        if alias and hasattr(alias, "name"):
            return alias.name.lower()
        if hasattr(cte, "alias_or_name"):
            return cte.alias_or_name.lower()
        return None

    def _get_table_schema(self, table: exp.Table) -> str | None:
        schema = table.args.get("db")
        if isinstance(schema, exp.Identifier):
            return schema.name
        if isinstance(schema, str):
            return schema
        return None

    def _alias_entries(self, table: exp.Table, table_key: str) -> dict[str, str]:
        alias_map = {table_key: table_key}
        alias = table.args.get("alias")
        if alias and hasattr(alias, "name") and alias.name:
            alias_map[alias.name.lower()] = table_key
        return alias_map

    def _column_exists(
        self,
        table_key: str,
        column_name: str,
        table_columns: dict[str, set[str]],
        view_columns: dict[str, set[str]],
    ) -> bool:
        column_lower = column_name.lower()
        return column_lower in table_columns.get(
            table_key, set()
        ) or column_lower in view_columns.get(table_key, set())

    def _column_in_any_table(
        self,
        column_name: str,
        tables: set[str],
        table_columns: dict[str, set[str]],
        view_columns: dict[str, set[str]],
    ) -> bool:
        column_lower = column_name.lower()
        for table_key in tables:
            if column_lower in table_columns.get(table_key, set()):
                return True
            if column_lower in view_columns.get(table_key, set()):
                return True
        return False

    def _table_has_sensitive_columns(
        self,
        table_key: str,
        table_columns: dict[str, set[str]],
        view_columns: dict[str, set[str]],
    ) -> bool:
        columns = table_columns.get(table_key) or view_columns.get(table_key) or set()
        return any(self.sanitizer.is_sensitive_column(col) for col in columns)

    def _get_star_table(self, star: exp.Star) -> str | None:
        table = star.args.get("table")
        if isinstance(table, exp.Identifier):
            return table.name
        if isinstance(table, str):
            return table
        return None

