"""Query service - orchestrates NL2SQL flow"""

import asyncio
import json
import re
import time
from decimal import Decimal
from typing import Any

import sqlglot
from sqlglot import exp
from sqlglot.errors import ParseError

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
from pg_mcp.security.access_control import AccessControl
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
        self.access_control = AccessControl(self.sanitizer)
        self.validation_service = validation_service
        self.metrics = metrics
        self.token_meter = token_meter
        self.log_sanitizer = log_sanitizer

    async def execute_query(self, request: QueryRequest) -> QueryResponse:
        """执行自然语言查询"""
        try:
            # 1. 确定目标数据库
            db_name = self._select_database(request.database)
            # 获取数据库类型
            db_type = self.db_pool.get_db_type(db_name)

            # 2. 获取schema上下文
            schema_context = self.schema_service.format_for_llm(
                db_name, request.schema_name
            )
            if not schema_context:
                raise PgMcpError(
                    code=ErrorCode.SCHEMA_LOAD_ERROR,
                    message=f"Schema {request.schema_name} 未找到",
                )

            # 3. 调用LLM生成SQL（含限流，传递数据库类型）
            llm_result = await self._call_llm_with_retries(
                self.llm_client.generate_sql,
                request.query,
                schema_context,
                db_type,
            )

            sql = llm_result.get("sql", "")
            explanation = llm_result.get("explanation", "")
            confidence = llm_result.get("confidence", 0.5)

            # 4. SQL安全校验（根据数据库类型选择方言）
            # 创建对应数据库类型的 SQLValidator
            sql_validator = SQLValidator(self.settings.security.allowed_functions, db_type)
            validated_sql = sql_validator.validate_or_raise(sql, db_type)

            # 5. 检查SQL中的文字常量（长度限制、特殊字符告警）
            self._check_literal_constants(validated_sql)

            # 6. 表/列访问控制
            db_info = self.schema_service.get_cached(db_name)
            if not db_info:
                raise PgMcpError(
                    code=ErrorCode.SCHEMA_LOAD_ERROR,
                    message=f"数据库 {db_name} 的schema未加载",
                )
            self.access_control.validate_or_raise(
                validated_sql, db_info, request.schema_name
            )

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

            # 7. 如果只需要SQL，直接返回
            if request.return_type == "sql":
                return QueryResponse(
                    success=True,
                    data=SQLGenerationResult(
                        sql=validated_sql,
                        explanation=explanation,
                        confidence=confidence,
                    ),
                )

            # 8. 执行SQL
            result_data = await self._execute_sql(
                db_name, validated_sql, request, explanation
            )

            # 9. 结果验证（可选）
            if self.settings.security.enable_result_validation and not self.token_meter.should_skip_validation():
                await self._validate_result(
                    request.query, validated_sql, result_data
                )

            return QueryResponse(success=True, data=result_data)

        except PgMcpError as e:
            retry_after_ms = None
            if isinstance(e.details, dict):
                retry_after_ms = e.details.get("retry_after_ms")
            return QueryResponse(
                success=False,
                error=ErrorDetail(
                    code=e.code.value,
                    type=e.code.name,
                    message=e.message,
                    details=e.details,
                    retryable=e.retryable,
                    suggestion=e.suggestion,
                    retry_after_ms=retry_after_ms,
                ),
            )

    def _check_literal_constants(self, sql: str) -> None:
        """检查SQL中的文字常量（长度限制、特殊字符告警）"""
        # 仅检查单引号字符串字面量，避免误判双引号标识符
        string_pattern = r"'([^']|'')*'"
        matches = re.finditer(string_pattern, sql)

        for match in matches:
            literal = match.group(0)
            # 去掉首尾引号并还原转义单引号
            content = literal[1:-1].replace("''", "'")
            # 检查长度
            if len(content) > 1000:
                raise SecurityViolationError(
                    message="SQL中的字符串常量过长",
                    sql=sql,
                    violation=f"字符串长度 {len(content)} > 1000",
                )
            # 检查异常转义序列
            if "\\x" in content or "\\u" in content:
                raise SecurityViolationError(
                    message="SQL中包含可疑的转义序列",
                    sql=sql,
                    violation="检测到异常转义序列",
                )

    async def _execute_sql(
        self,
        db_name: str,
        sql: str,
        request: QueryRequest,
        explanation: str,
    ) -> QueryResultData:
        """执行SQL并返回结果（禁止额外拼接，直接使用conn.fetch）"""
        # 获取数据库类型
        db_type = self.db_pool.get_db_type(db_name)
        
        # 计算分页
        max_rows = min(
            request.max_rows or self.settings.security.max_rows,
            self.settings.security.hard_max_rows,
        )
        offset = (request.page - 1) * request.page_size
        limit = min(request.page_size, max_rows)

        # 添加LIMIT/OFFSET（如果原SQL没有）
        paginated_sql = self._add_pagination(
            sql, limit + 1, offset, db_type
        )  # +1检测是否有更多

        await self.rate_limiter.acquire_db()
        start_time = time.monotonic()
        try:
            async with self.db_pool.acquire_readonly(
                db_name, self.settings.security.query_timeout
            ) as conn:
                if self.settings.security.enable_explain_check:
                    await self._validate_explain_plan(conn, sql, db_type)
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

        # 处理结果 - MySQL 和 PostgreSQL 结果格式不同
        truncated = len(rows) > limit
        if truncated:
            rows = rows[:limit]
            self.metrics.record_truncation()

        # MySQL (使用DictCursor) 和 PostgreSQL 都返回字典格式
        if rows:
            # 两种数据库都返回字典格式（MySQL使用DictCursor，PostgreSQL使用Record）
            columns = list(rows[0].keys())
            row_dicts = [self._serialize_row(dict(row)) for row in rows]
        else:
            columns = []
            row_dicts = []

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

    def _serialize_row(self, row: dict[str, Any]) -> dict[str, Any]:
        """将数据库行转换为可 JSON 序列化的格式"""
        result = {}
        for key, value in row.items():
            if isinstance(value, Decimal):
                result[key] = float(value)
            elif hasattr(value, 'isoformat'):  # datetime, date, time
                result[key] = value.isoformat()
            else:
                result[key] = value
        return result

    def _add_pagination(self, sql: str, limit: int, offset: int, db_type: str = "postgresql") -> str:
        """为SQL添加分页"""
        dialect = "mysql" if db_type == "mysql" else "postgres"
        try:
            parsed = sqlglot.parse_one(sql, dialect=dialect)
        except ParseError:
            sql_lower = sql.lower().strip()
            if "limit" not in sql_lower:
                sql = f"{sql.rstrip(';')} LIMIT {limit}"
            if offset > 0 and "offset" not in sql_lower:
                sql = f"{sql} OFFSET {offset}"
            return sql

        if isinstance(parsed, exp.Select):
            if parsed.args.get("limit") is None:
                parsed = parsed.limit(limit)
            if offset > 0 and parsed.args.get("offset") is None:
                parsed = parsed.offset(offset)
            return parsed.sql(dialect=dialect)

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
            validation = await self._call_llm_with_retries(
                self.validation_service.validate, user_query, sql, result
            )
        else:
            # 兼容直接调用模式
            summary = self.sanitizer.generate_summary(
                result.columns, result.rows, result.row_count
            )
            validation = await self._call_llm_with_retries(
                self.llm_client.validate_result, user_query, sql, summary
            )

        if not validation.get("is_valid", True):
            # 可以记录日志或添加警告，但不阻塞返回
            result.explanation += (
                f"\n[验证警告] {validation.get('reason', '')}"
            )

    def _select_database(self, requested: str | None) -> str:
        databases = self.db_pool.list_databases()
        if not databases:
            raise PgMcpError(
                code=ErrorCode.DATABASE_CONNECTION_ERROR,
                message="未配置任何数据库",
            )
        if requested:
            if requested not in databases:
                raise PgMcpError(
                    code=ErrorCode.DATABASE_CONNECTION_ERROR,
                    message=f"数据库 {requested} 未配置",
                )
            return requested
        if len(databases) > 1:
            raise PgMcpError(
                code=ErrorCode.CONFIGURATION_ERROR,
                message="存在多个数据库配置，请显式指定database参数",
            )
        return databases[0]

    async def _call_llm_with_retries(self, func, *args) -> dict[str, Any]:
        attempts = max(1, self.settings.security.max_retry_attempts)
        last_error: Exception | None = None
        for attempt in range(1, attempts + 1):
            await self.rate_limiter.acquire_llm()
            try:
                result = await func(*args)
                self.rate_limiter.record_llm_success()
                self.metrics.record_llm_call(True)
                usage = result.get("_token_usage") if isinstance(result, dict) else None
                if usage:
                    self.metrics.record_tokens(
                        usage.get("total_tokens", 0),
                        0.0,
                    )
                    self.token_meter.record_usage(
                        usage.get("prompt_tokens", 0),
                        usage.get("completion_tokens", 0),
                    )
                return result
            except Exception as exc:
                last_error = exc
                self.rate_limiter.record_llm_failure()
                self.metrics.record_llm_call(False)
                if attempt < attempts:
                    await asyncio.sleep(min(2 ** attempt, 8))
        if last_error:
            raise last_error
        raise PgMcpError(
            code=ErrorCode.LLM_ERROR,
            message="LLM调用失败",
            retryable=True,
        )

    async def _validate_explain_plan(self, conn, sql: str, db_type: str = "postgresql") -> None:
        """验证EXPLAIN计划"""
        if db_type == "mysql":
            # MySQL EXPLAIN 格式不同
            explain_sql = f"EXPLAIN {sql}"
            plan_rows = await conn.fetch(explain_sql)
            if plan_rows:
                # MySQL EXPLAIN 返回表格式，检查 rows 列
                for row in plan_rows:
                    rows = row.get("rows", 0) if isinstance(row, dict) else 0
                    if (
                        self.settings.security.explain_max_rows is not None
                        and rows > self.settings.security.explain_max_rows
                    ):
                        raise SecurityViolationError(
                            message="查询计划行数过多，已阻止执行",
                            sql=sql,
                            violation=f"Plan Rows {rows} 超过限制",
                        )
        else:
            # PostgreSQL EXPLAIN
            explain_sql = f"EXPLAIN (FORMAT JSON) {sql}"
            plan_raw = await conn.fetchval(explain_sql)
            if isinstance(plan_raw, str):
                plan_data = json.loads(plan_raw)
            else:
                plan_data = plan_raw
            if not plan_data:
                return
            plan_root = plan_data[0].get("Plan", {}) if isinstance(plan_data, list) else {}
            total_cost = self._get_plan_metric(plan_root, "Total Cost")
            plan_rows = self._get_plan_metric(plan_root, "Plan Rows")
            if (
                self.settings.security.explain_max_cost is not None
                and total_cost is not None
                and total_cost > self.settings.security.explain_max_cost
            ):
                raise SecurityViolationError(
                    message="查询计划成本过高，已阻止执行",
                    sql=sql,
                    violation=f"Total Cost {total_cost} 超过限制",
                )
            if (
                self.settings.security.explain_max_rows is not None
                and plan_rows is not None
                and plan_rows > self.settings.security.explain_max_rows
            ):
                raise SecurityViolationError(
                    message="查询计划行数过高，已阻止执行",
                    sql=sql,
                    violation=f"Plan Rows {plan_rows} 超过限制",
                )

    def _get_plan_metric(self, plan: dict[str, Any], key: str) -> float | int | None:
        for plan_key, value in plan.items():
            if plan_key.lower() == key.lower():
                return value
        return None

