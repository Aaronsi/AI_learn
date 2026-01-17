"""Function whitelist guard for SQL security"""

from sqlglot import exp


class FunctionGuard:
    """函数白名单守卫，用于加强可变函数拦截"""

    # 通用安全函数（所有数据库都支持）
    COMMON_SAFE_FUNCS = {
        # 聚合函数
        "count",
        "sum",
        "avg",
        "min",
        "max",
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
        "extract",
        # 数学函数
        "abs",
        "ceil",
        "floor",
        "round",
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
    }

    # PostgreSQL 特有安全函数
    POSTGRESQL_SAFE_FUNCS = {
        "array_agg",
        "string_agg",
        "date_trunc",
        "age",
        "date_part",
        "to_char",
        "to_date",
        "to_timestamp",
        "trunc",
        "json_agg",
        "jsonb_agg",
        "json_build_object",
        "jsonb_build_object",
        "json_extract_path",
        "jsonb_extract_path",
        "row_number",
        "rank",
        "dense_rank",
        "ntile",
        "lag",
        "lead",
        "first_value",
        "last_value",
    }

    # MySQL 特有安全函数
    MYSQL_SAFE_FUNCS = {
        "group_concat",  # MySQL 特有聚合函数
        "groupconcat",  # SQLGlot 解析后的名称（无下划线）
        "date_format",
        "dateformat",  # SQLGlot 可能解析为无下划线
        "timetostr",  # SQLGlot 解析 DATE_FORMAT 为 timetostr
        "str_to_date",
        "strtodate",  # SQLGlot 可能解析为无下划线
        "ifnull",
        "if",
        "datediff",
        "timestampdiff",
        "char_length",  # MySQL 字符串长度函数
        "substring_index",
    }

    def __init__(self, allowed_functions: list[str] | None = None, db_type: str = "postgresql"):
        self.allowed = set(allowed_functions or [])
        self.allowed |= self.COMMON_SAFE_FUNCS
        if db_type == "mysql":
            self.allowed |= self.MYSQL_SAFE_FUNCS
        else:
            self.allowed |= self.POSTGRESQL_SAFE_FUNCS

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

