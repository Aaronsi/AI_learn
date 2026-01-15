"""Data sanitizer for sensitive information filtering"""

import re
from typing import Any


class Sanitizer:
    """敏感数据脱敏器"""

    def __init__(self, sensitive_patterns: list[str]):
        self.sensitive_patterns = [
            re.compile(p, re.IGNORECASE) for p in sensitive_patterns
        ]

    def is_sensitive_column(self, column_name: str) -> bool:
        """检查列名是否匹配敏感模式"""
        return any(p.search(column_name) for p in self.sensitive_patterns)

    def sanitize_for_llm(
        self,
        columns: list[str],
        rows: list[dict[str, Any]],
        max_rows: int = 20,
        max_cols: int = 10,
    ) -> tuple[list[str], list[dict[str, Any]]]:
        """为发送给LLM准备脱敏采样数据"""
        # 过滤敏感列
        safe_columns = [c for c in columns if not self.is_sensitive_column(c)]

        # 限制列数
        if len(safe_columns) > max_cols:
            safe_columns = safe_columns[:max_cols]

        # 限制行数并过滤敏感列数据
        safe_rows = []
        for row in rows[:max_rows]:
            safe_row = {k: v for k, v in row.items() if k in safe_columns}
            safe_rows.append(safe_row)

        return safe_columns, safe_rows

    def generate_summary(
        self,
        columns: list[str],
        rows: list[dict[str, Any]],
        total_count: int,
    ) -> dict[str, Any]:
        """生成结果摘要（用于LLM验证）"""
        summary = {
            "total_rows": total_count,
            "sample_rows": len(rows),
            "columns": columns,
            "column_stats": {},
        }

        for col in columns:
            if self.is_sensitive_column(col):
                continue

            values = [r.get(col) for r in rows if r.get(col) is not None]
            if not values:
                continue

            col_stat: dict[str, Any] = {"non_null_count": len(values)}

            # 数值类型统计
            if all(isinstance(v, (int, float)) for v in values):
                col_stat["min"] = min(values)
                col_stat["max"] = max(values)
                col_stat["avg"] = sum(values) / len(values)
            else:
                # 字符串类型：显示唯一值数量
                col_stat["unique_count"] = len(set(str(v) for v in values))

            summary["column_stats"][col] = col_stat

        return summary

