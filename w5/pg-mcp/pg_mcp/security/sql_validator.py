"""SQL security validator using SQLGlot AST analysis"""

import sqlglot
from sqlglot import exp
from sqlglot.errors import ParseError
from typing import NamedTuple

from pg_mcp.models.errors import SecurityViolationError
from pg_mcp.security.function_guard import FunctionGuard


class ValidationResult(NamedTuple):
    """校验结果"""

    is_valid: bool
    violations: list[str]
    normalized_sql: str | None


class SQLValidator:
    """SQL安全校验器 - 使用SQLGlot进行AST级别分析"""

    # 禁止的语句类型
    FORBIDDEN_STATEMENT_TYPES: set[type] = {
        exp.Insert,
        exp.Update,
        exp.Delete,
        exp.Merge,
        exp.Drop,
        exp.Create,
        exp.Alter,
        exp.TruncateTable,
        exp.Grant,
        exp.Revoke,
        exp.Commit,
        exp.Rollback,
    }

    # 禁止的表达式类型
    FORBIDDEN_EXPRESSION_TYPES: set[type] = {
        exp.Into,  # SELECT ... INTO
        exp.Command,  # COPY, EXECUTE, CALL, DO
    }

    # 危险函数黑名单（默认拒绝可变函数）
    DANGEROUS_FUNCTIONS: set[str] = {
        "pg_sleep",
        "pg_terminate_backend",
        "pg_cancel_backend",
        "pg_reload_conf",
        "lo_import",
        "lo_export",
        "dblink",
        "dblink_exec",
    }

    def __init__(self, allowed_functions: list[str] | None = None):
        self.allowed_functions = set(allowed_functions or [])
        self.function_guard = FunctionGuard(allowed_functions)

    def validate(self, sql: str) -> ValidationResult:
        """验证SQL安全性"""
        violations: list[str] = []

        try:
            # 解析SQL为AST
            parsed = sqlglot.parse(sql, dialect="postgres")
        except ParseError as e:
            return ValidationResult(
                is_valid=False,
                violations=[f"SQL解析失败: {e}"],
                normalized_sql=None,
            )

        for statement in parsed:
            if statement is None:
                continue

            # 检查语句类型
            stmt_violations = self._check_statement_type(statement)
            violations.extend(stmt_violations)

            # 检查CTE中的DML
            cte_violations = self._check_cte_safety(statement)
            violations.extend(cte_violations)

            # 检查危险表达式
            expr_violations = self._check_expressions(statement)
            violations.extend(expr_violations)

            # 检查函数调用
            func_violations = self._check_functions(statement)
            violations.extend(func_violations)

        is_valid = len(violations) == 0
        normalized = (
            parsed[0].sql(dialect="postgres") if is_valid and parsed else None
        )

        return ValidationResult(
            is_valid=is_valid,
            violations=violations,
            normalized_sql=normalized,
        )

    def _check_statement_type(self, stmt: exp.Expression) -> list[str]:
        """检查语句类型是否允许"""
        violations = []
        for forbidden in self.FORBIDDEN_STATEMENT_TYPES:
            if isinstance(stmt, forbidden):
                violations.append(f"禁止的语句类型: {forbidden.__name__}")
        return violations

    def _check_cte_safety(self, stmt: exp.Expression) -> list[str]:
        """检查CTE中是否包含DML"""
        violations = []
        for cte in stmt.find_all(exp.CTE):
            cte_expr = cte.this
            for forbidden in self.FORBIDDEN_STATEMENT_TYPES:
                if isinstance(cte_expr, forbidden):
                    violations.append(
                        f"CTE中包含禁止的操作: {forbidden.__name__}"
                    )
        return violations

    def _check_expressions(self, stmt: exp.Expression) -> list[str]:
        """检查危险表达式"""
        violations = []
        for forbidden in self.FORBIDDEN_EXPRESSION_TYPES:
            if stmt.find(forbidden):
                violations.append(f"禁止的表达式: {forbidden.__name__}")
        return violations

    def _check_functions(self, stmt: exp.Expression) -> list[str]:
        """检查函数调用安全性"""
        violations = []
        for func in stmt.find_all(exp.Func):
            func_name = (
                func.name.lower()
                if hasattr(func, "name") and func.name
                else str(func.key).lower()
            )

            # 检查黑名单
            if func_name in self.DANGEROUS_FUNCTIONS:
                violations.append(f"禁止调用危险函数: {func_name}")

            # 如果配置了白名单，则检查白名单
            if self.allowed_functions and func_name not in self.allowed_functions:
                # 允许常见的聚合和标准函数
                if not self._is_safe_builtin(func_name):
                    violations.append(f"函数不在白名单中: {func_name}")

        # 使用 FunctionGuard 再次校验（补充可变函数拦截）
        violations.extend(self.function_guard.validate_functions(stmt))

        return violations

    def _is_safe_builtin(self, func_name: str) -> bool:
        """检查是否是安全的内置函数"""
        safe_builtins = {
            # 聚合函数
            "count",
            "sum",
            "avg",
            "min",
            "max",
            "array_agg",
            "string_agg",
            # 字符串函数
            "lower",
            "upper",
            "trim",
            "substring",
            "length",
            "concat",
            "replace",
            # 日期函数
            "now",
            "current_date",
            "current_timestamp",
            "date_trunc",
            "extract",
            "age",
            "date_part",
            "to_char",
            "to_date",
            "to_timestamp",
            # 数学函数
            "abs",
            "ceil",
            "floor",
            "round",
            "trunc",
            "mod",
            "power",
            "sqrt",
            # 条件函数
            "coalesce",
            "nullif",
            "greatest",
            "least",
            "case",
            # 类型转换
            "cast",
            "convert",
            # JSON函数
            "json_agg",
            "jsonb_agg",
            "json_build_object",
            "jsonb_build_object",
            "json_extract_path",
            "jsonb_extract_path",
            # 窗口函数
            "row_number",
            "rank",
            "dense_rank",
            "ntile",
            "lag",
            "lead",
            "first_value",
            "last_value",
        }
        return func_name in safe_builtins

    def validate_or_raise(self, sql: str) -> str:
        """验证SQL，如果无效则抛出异常，返回规范化的SQL"""
        result = self.validate(sql)
        if not result.is_valid:
            raise SecurityViolationError(
                message="SQL安全校验失败",
                sql=sql,
                violation="; ".join(result.violations),
            )
        return result.normalized_sql or sql

