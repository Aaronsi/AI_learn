"""Function whitelist guard for SQL security"""

from sqlglot import exp


class FunctionGuard:
    """函数白名单守卫，用于加强可变函数拦截"""

    # 默认允许的纯函数（补充 SQLValidator 内置判断）
    DEFAULT_SAFE_FUNCS = {
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

    def __init__(self, allowed_functions: list[str] | None = None):
        self.allowed = set(allowed_functions or [])
        self.allowed |= self.DEFAULT_SAFE_FUNCS

    def validate_functions(self, stmt: exp.Expression) -> list[str]:
        """检查表达式中调用的函数是否在白名单"""
        violations: list[str] = []
        for func in stmt.find_all(exp.Func):
            func_name = (
                func.name.lower()
                if hasattr(func, "name") and func.name
                else str(func.key).lower()
            )
            # 跳过特殊符号（如 * 在 COUNT(*) 中）
            if func_name in ("*", ""):
                continue
            if func_name not in self.allowed:
                violations.append(f"函数不在白名单: {func_name}")
        return violations

