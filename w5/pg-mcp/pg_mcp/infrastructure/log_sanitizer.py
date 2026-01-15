"""Log sanitization utilities"""

import re
from typing import Any


class LogSanitizer:
    """日志脱敏器"""

    def __init__(self, sensitive_patterns: list[str]):
        self.sensitive_patterns = [
            re.compile(p, re.IGNORECASE) for p in sensitive_patterns
        ]
        self.sensitive_keywords = set(p.lower() for p in sensitive_patterns)

    def is_sensitive_key(self, key: str) -> bool:
        """检查键名是否敏感"""
        key_lower = key.lower()
        return any(keyword in key_lower for keyword in self.sensitive_keywords)

    def sanitize_dict(self, data: dict[str, Any]) -> dict[str, Any]:
        """脱敏字典数据"""
        sanitized = {}
        for key, value in data.items():
            if self.is_sensitive_key(key):
                sanitized[key] = "[REDACTED]"
            elif isinstance(value, dict):
                sanitized[key] = self.sanitize_dict(value)
            elif isinstance(value, list):
                sanitized[key] = [
                    self.sanitize_dict(item) if isinstance(item, dict) else "[REDACTED]"
                    if self._is_sensitive_value(str(item))
                    else item
                    for item in value[:5]  # 只保留前5个元素
                ]
            elif self._is_sensitive_value(str(value)):
                sanitized[key] = "[REDACTED]"
            else:
                sanitized[key] = value
        return sanitized

    def _is_sensitive_value(self, value: str) -> bool:
        """检查值是否敏感（简单启发式）"""
        # 检查是否包含敏感关键词
        value_lower = value.lower()
        if any(keyword in value_lower for keyword in self.sensitive_keywords):
            return True
        # 检查是否是密码格式（长度>8，包含字母和数字）
        if len(value) > 8 and re.search(r"[a-zA-Z]", value) and re.search(
            r"\d", value
        ):
            return True
        return False

    def sanitize_sql_error(self, error: str, sql: str) -> str:
        """脱敏SQL错误信息"""
        # 只返回错误摘要，不泄露完整SQL
        error_lines = error.split("\n")
        summary = error_lines[0] if error_lines else "SQL execution error"
        return f"{summary} (SQL redacted for security)"

    def sanitize_llm_request(self, request: dict[str, Any]) -> dict[str, Any]:
        """脱敏LLM请求"""
        sanitized = {}
        for key, value in request.items():
            if key == "messages" and isinstance(value, list):
                sanitized[key] = [
                    {
                        "role": msg.get("role"),
                        "content": self._sanitize_content(msg.get("content", "")),
                    }
                    for msg in value
                ]
            else:
                sanitized[key] = value
        return sanitized

    def _sanitize_content(self, content: str) -> str:
        """脱敏内容"""
        # 移除敏感列名和样本值
        lines = content.split("\n")
        sanitized_lines = []
        for line in lines:
            if any(
                pattern.search(line) for pattern in self.sensitive_patterns
            ):
                sanitized_lines.append("[REDACTED LINE]")
            else:
                sanitized_lines.append(line)
        return "\n".join(sanitized_lines)

