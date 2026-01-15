"""Query service - orchestrates NL2SQL flow"""

import re
import time
from typing import Any

from pg_mcp.config.settings import Settings
from pg_mcp.infrastructure.db_pool import DBPoolManager
from pg_mcp.infrastructure.llm_client import LLMClient
from pg_mcp.infrastructure.rate_limiter import RateLimiter
from pg_mcp.infrastructure.metrics import Metrics
from pg_mcp.infrastructure.token_meter import TokenMeter
from pg_mcp.infrastructure.log_sanitizer import LogSanitizer
from pg_mcp.models.query import (
    QueryRequest,
    QueryResponse,
    QueryResultData,
    SQLGenerationResult,
    ErrorDetail,
)
from pg_mcp.models.errors import (
    PgMcpError,
    ErrorCode,
    SecurityViolationError,
    SQLExecutionError,
)
from pg_mcp.security.sql_validator import SQLValidator
from pg_mcp.security.sanitizer import Sanitizer
from pg_mcp.services.schema_service import SchemaService
from pg_mcp.services.validation_service import ValidationService


class QueryService:
    """查询服务 - 编排NL2SQL的完整流程"""

    def __init__(
        self,
        settings: Settings,
        db_pool: DBPoolManager,
        schema_service: SchemaService,
        llm_client: LLMClient,
        rate_limiter: RateLimiter,
        metrics: Metrics,
        token_meter: TokenMeter,
        log_sanitizer: LogSanitizer | None = None,
        validation_service: ValidationService | None = None,
    ):
        self.settings = settings
        self.db_pool = db_pool
        self.schema_service = schema_service
        self.llm_client = llm_client
        self.rate_limiter = rate_limiter
        self.sql_validator = SQLValidator(settings.security.allowed_functions)
        self.sanitizer = Sanitizer(settings.security.sensitive_columns)
        self.validation_service = validation_service
        self.metrics = metrics
        self.token_meter = token_meter
        self.log_sanitizer = log_sanitizer

    async def execute_query(self, request: QueryRequest) -> QueryResponse:
        """执行自然语言查询"""
        try:
            # 1. 确定目标数据库
            db_name = request.database or self.db_pool.list_databases()[0]

            # 2. 获取schema上下文
            schema_context = self.schema_service.format_for_llm(
                db_name, request.schema_name
            )
            if not schema_context:
                raise PgMcpError(
                    code=ErrorCode.SCHEMA_LOAD_ERROR,
                    message=f"Schema {request.schema_name} 未找到",
                )

            # 3. 调用LLM生成SQL（含限流）
            await self.rate_limiter.acquire_llm()
            try:
                llm_result = await self.llm_client.generate_sql(
                    request.query, schema_context
                )
                self.rate_limiter.record_llm_success()
                self.metrics.record_llm_call(True)
                usage = llm_result.get("_token_usage")
                if usage:
                    self.metrics.record_tokens(
                        usage.get("total_tokens", 0),
                        0.0,
                    )
                    self.token_meter.record_usage(
                        usage.get("prompt_tokens", 0),
                        usage.get("completion_tokens", 0),
                    )
            except Exception as e:
                self.rate_limiter.record_llm_failure()
                self.metrics.record_llm_call(False)
                raise

            sql = llm_result.get("sql", "")
            explanation = llm_result.get("explanation", "")
            confidence = llm_result.get("confidence", 0.5)

            # 4. SQL安全校验
            validated_sql = self.sql_validator.validate_or_raise(sql)

            # 5. 检查SQL中的文字常量（长度限制、特殊字符告警、禁止直接字符串字面量以强制参数化）
            self._check_literal_constants(validated_sql)
            self._reject_string_literals(validated_sql)

            # Token/成本阈值降级策略：如需仅返回SQL
            if self.token_meter.should_return_sql_only():
                return QueryResponse(
                    success=True,
                    data=SQLGenerationResult(
                        sql=validated_sql,
                        explanation=f"{explanation}\n[降级] token/cost 触发，仅返回SQL",
                        confidence=confidence,
                    ),
                )

            # 6. 如果只需要SQL，直接返回
            if request.return_type == "sql":
                return QueryResponse(
                    success=True,
                    data=SQLGenerationResult(
                        sql=validated_sql,
                        explanation=explanation,
                        confidence=confidence,
                    ),
                )

            # 7. 执行SQL
            result_data = await self._execute_sql(
                db_name, validated_sql, request, explanation
            )

            # 8. 结果验证（可选）
            if self.settings.security.enable_result_validation and not self.token_meter.should_skip_validation():
                await self._validate_result(
                    request.query, validated_sql, result_data
                )

            return QueryResponse(success=True, data=result_data)

        except PgMcpError as e:
            return QueryResponse(
                success=False,
                error=ErrorDetail(
                    code=e.code.value,
                    type=e.code.name,
                    message=e.message,
                    details=e.details,
                    retryable=e.retryable,
                    suggestion=e.suggestion,
                ),
            )

    def _check_literal_constants(self, sql: str) -> None:
        """检查SQL中的文字常量（长度限制、特殊字符告警）"""
        # 匹配字符串字面量（单引号或双引号）
        string_pattern = r"['\"]([^'\"]*)['\"]"
        matches = re.finditer(string_pattern, sql)

        for match in matches:
            literal = match.group(1)
            # 检查长度
            if len(literal) > 1000:
                raise SecurityViolationError(
                    message="SQL中的字符串常量过长",
                    sql=sql,
                    violation=f"字符串长度 {len(literal)} > 1000",
                )
            # 检查异常转义序列
            if "\\x" in literal or "\\u" in literal:
                raise SecurityViolationError(
                    message="SQL中包含可疑的转义序列",
                    sql=sql,
                    violation="检测到异常转义序列",
                )

    def _reject_string_literals(self, sql: str) -> None:
        """禁止直接使用字符串字面量，要求参数化"""
        string_pattern = r"'[^']*'|\"[^\"]*\""
        if re.search(string_pattern, sql):
            raise SecurityViolationError(
                message="SQL中包含直接字符串字面量，需改为参数化查询",
                sql=sql,
                violation="检测到字符串字面量",
            )

    async def _execute_sql(
        self,
        db_name: str,
        sql: str,
        request: QueryRequest,
        explanation: str,
    ) -> QueryResultData:
        """执行SQL并返回结果（禁止额外拼接，直接使用conn.fetch）"""
        # 计算分页
        max_rows = min(
            request.max_rows or self.settings.security.max_rows,
            self.settings.security.hard_max_rows,
        )
        offset = (request.page - 1) * request.page_size
        limit = min(request.page_size, max_rows)

        # 添加LIMIT/OFFSET（如果原SQL没有）
        paginated_sql = self._add_pagination(
            sql, limit + 1, offset
        )  # +1检测是否有更多

        await self.rate_limiter.acquire_db()
        start_time = time.monotonic()
        try:
            async with self.db_pool.acquire_readonly(
                db_name, self.settings.security.query_timeout
            ) as conn:
                # 直接使用 conn.fetch，禁止任何字符串拼接
                rows = await conn.fetch(paginated_sql)
            self.rate_limiter.record_db_success()
            self.metrics.record_db_query(True)
        except Exception as e:
            self.rate_limiter.record_db_failure()
            self.metrics.record_db_query(False)
            error_msg = str(e)
            if self.log_sanitizer:
                error_msg = self.log_sanitizer.sanitize_sql_error(error_msg, sql)
            raise SQLExecutionError(
                message=f"SQL执行失败: {error_msg}",
                sql=sql,
                pg_error=error_msg,
            )

        execution_time_ms = int((time.monotonic() - start_time) * 1000)

        # 处理结果
        truncated = len(rows) > limit
        if truncated:
            rows = rows[:limit]
            self.metrics.record_truncation()

        columns = list(rows[0].keys()) if rows else []
        row_dicts = [dict(r) for r in rows]

        self.metrics.record_query_time(execution_time_ms)

        return QueryResultData(
            sql=sql,
            columns=columns,
            rows=row_dicts,
            row_count=len(row_dicts),
            truncated=truncated,
            page=request.page,
            page_size=request.page_size,
            execution_time_ms=execution_time_ms,
            explanation=explanation,
        )

    def _add_pagination(self, sql: str, limit: int, offset: int) -> str:
        """为SQL添加分页"""
        sql_lower = sql.lower().strip()
        if "limit" not in sql_lower:
            sql = f"{sql.rstrip(';')} LIMIT {limit}"
        if offset > 0 and "offset" not in sql_lower:
            sql = f"{sql} OFFSET {offset}"
        return sql

    async def _validate_result(
        self,
        user_query: str,
        sql: str,
        result: QueryResultData,
    ) -> None:
        """验证结果是否符合用户意图"""
        if self.validation_service:
            validation = await self.validation_service.validate(
                user_query, sql, result
            )
        else:
            # 兼容直接调用模式
            summary = self.sanitizer.generate_summary(
                result.columns, result.rows, result.row_count
            )
            validation = await self.llm_client.validate_result(
                user_query, sql, summary
            )

        if not validation.get("is_valid", True):
            # 可以记录日志或添加警告，但不阻塞返回
            result.explanation += (
                f"\n[验证警告] {validation.get('reason', '')}"
            )

