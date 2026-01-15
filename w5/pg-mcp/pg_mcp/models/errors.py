"""Error models and exception classes"""

from enum import Enum


class ErrorCode(str, Enum):
    """错误码枚举"""

    DATABASE_CONNECTION_ERROR = "E001"
    SCHEMA_LOAD_ERROR = "E002"
    LLM_ERROR = "E003"
    SQL_GENERATION_ERROR = "E004"
    SECURITY_VIOLATION = "E005"
    SQL_EXECUTION_ERROR = "E006"
    VALIDATION_ERROR = "E007"
    TIMEOUT_ERROR = "E008"
    CONFIGURATION_ERROR = "E009"
    RATE_LIMITED = "E010"
    CIRCUIT_BREAKER_OPEN = "E011"


class PgMcpError(Exception):
    """基础异常类"""

    def __init__(
        self,
        code: ErrorCode,
        message: str,
        details: dict | None = None,
        retryable: bool = False,
        suggestion: str | None = None,
    ):
        self.code = code
        self.message = message
        self.details = details or {}
        self.retryable = retryable
        self.suggestion = suggestion
        super().__init__(message)


class SecurityViolationError(PgMcpError):
    """安全违规异常"""

    def __init__(self, message: str, sql: str, violation: str):
        super().__init__(
            code=ErrorCode.SECURITY_VIOLATION,
            message=message,
            details={"sql": sql, "violation": violation},
            retryable=False,
        )


class SQLExecutionError(PgMcpError):
    """SQL执行异常"""

    def __init__(self, message: str, sql: str, pg_error: str):
        super().__init__(
            code=ErrorCode.SQL_EXECUTION_ERROR,
            message=message,
            details={"sql": sql, "pg_error": pg_error},
            retryable=True,
            suggestion="检查SQL语法或重新描述查询需求",
        )

