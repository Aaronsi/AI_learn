# PostgreSQL MCP Server 设计文档

## 文档信息

| 项目 | 内容 |
|------|------|
| 文档版本 | v0.1 |
| 创建日期 | 2026-01-11 |
| 状态 | 草稿 |
| 关联PRD | 0001-pg-mcp-prd.md |

---

## 1. 技术栈选型

| 组件 | 技术选型 | 版本要求 | 选型理由 |
|------|----------|----------|----------|
| MCP框架 | FastMCP | ≥2.0 | 官方推荐的高性能Python MCP SDK，支持异步 |
| 数据库驱动 | asyncpg | ≥0.29 | PostgreSQL最快的异步驱动，原生支持连接池 |
| SQL解析 | SQLGlot | ≥25.0 | 纯Python SQL解析器，支持AST分析和方言转换 |
| 数据验证 | Pydantic | ≥2.0 | 现代Python数据验证，支持Settings管理 |
| LLM客户端 | openai | ≥1.0 | OpenAI兼容API，可直接对接DeepSeek |
| 配置管理 | pydantic-settings | ≥2.0 | 支持环境变量和YAML配置 |
| 日志 | structlog | ≥24.0 | 结构化日志，便于监控和审计 |
| 限流 | aiolimiter | ≥1.1 | 异步限流器 |

---

## 2. 系统架构

### 2.1 整体架构图

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              MCP Client (Cursor/Claude)                      │
└─────────────────────────────────────────────────────────────────────────────┘
                                        │
                                        ▼ MCP Protocol (stdio/SSE)
┌─────────────────────────────────────────────────────────────────────────────┐
│                              FastMCP Server Layer                            │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────────────┐    │
│  │ query tool  │ │ list_* tools│ │describe_tbl │ │ refresh_schema tool │    │
│  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────────────┘    │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                         Resource Handlers                            │    │
│  │   schema://databases  schema://{db}/schemas  schema://{db}/{s}/{t}  │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────────┘
                                        │
                    ┌───────────────────┼───────────────────┐
                    ▼                   ▼                   ▼
┌───────────────────────┐ ┌───────────────────────┐ ┌───────────────────────┐
│   Query Service       │ │   Schema Service      │ │   Validation Service  │
│  ┌─────────────────┐  │ │  ┌─────────────────┐  │ │  ┌─────────────────┐  │
│  │ NL2SQL Handler  │  │ │  │ Schema Loader   │  │ │  │ Result Validator│  │
│  │ SQL Executor    │  │ │  │ Cache Manager   │  │ │  │ Intent Checker  │  │
│  │ Result Formatter│  │ │  │ Disk Persister  │  │ │  └─────────────────┘  │
│  └─────────────────┘  │ │  └─────────────────┘  │ └───────────────────────┘
└───────────────────────┘ └───────────────────────┘             │
            │                       │                           │
            ▼                       ▼                           ▼
┌───────────────────────────────────────────────────────────────────────────┐
│                          Security Layer                                    │
│  ┌────────────────┐ ┌────────────────┐ ┌────────────────┐                 │
│  │ SQL Validator  │ │ Function Guard │ │ Sanitizer      │                 │
│  │ (SQLGlot AST)  │ │ (Whitelist)    │ │ (Sensitive)    │                 │
│  └────────────────┘ └────────────────┘ └────────────────┘                 │
└───────────────────────────────────────────────────────────────────────────┘
            │                       │                           │
            ▼                       ▼                           ▼
┌───────────────────────────────────────────────────────────────────────────┐
│                          Infrastructure Layer                              │
│  ┌────────────────┐ ┌────────────────┐ ┌────────────────┐ ┌────────────┐  │
│  │ DB Pool Manager│ │ LLM Client     │ │ Rate Limiter   │ │ Circuit    │  │
│  │ (asyncpg)      │ │ (openai)       │ │ (aiolimiter)   │ │ Breaker    │  │
│  └────────────────┘ └────────────────┘ └────────────────┘ └────────────┘  │
└───────────────────────────────────────────────────────────────────────────┘
            │                       │
            ▼                       ▼
    ┌───────────────┐       ┌───────────────┐
    │  PostgreSQL   │       │  DeepSeek API │
    │  Database(s)  │       │  (OpenAI兼容) │
    └───────────────┘       └───────────────┘
```

### 2.2 分层架构说明

| 层级 | 职责 | 核心组件 |
|------|------|----------|
| **MCP协议层** | 处理MCP协议通信，暴露Tools和Resources | FastMCP Server |
| **服务层** | 业务逻辑编排，协调各组件完成查询 | QueryService, SchemaService, ValidationService |
| **安全层** | SQL安全校验，敏感数据过滤 | SQLValidator, FunctionGuard, Sanitizer |
| **基础设施层** | 外部依赖封装，连接池/限流/熔断 | DBPoolManager, LLMClient, RateLimiter |

---

## 3. 核心模块设计

### 3.1 项目结构

```
pg_mcp/
├── __init__.py
├── __main__.py              # 入口点
├── server.py                # FastMCP服务器定义
├── config/
│   ├── __init__.py
│   └── settings.py          # Pydantic Settings配置
├── models/
│   ├── __init__.py
│   ├── schema.py            # Schema数据模型
│   ├── query.py             # 查询请求/响应模型
│   └── errors.py            # 错误模型
├── services/
│   ├── __init__.py
│   ├── query_service.py     # 查询服务
│   ├── schema_service.py    # Schema管理服务
│   └── validation_service.py # 结果验证服务
├── security/
│   ├── __init__.py
│   ├── sql_validator.py     # SQL安全校验器
│   ├── function_guard.py    # 函数白名单守卫
│   └── sanitizer.py         # 敏感数据脱敏
├── infrastructure/
│   ├── __init__.py
│   ├── db_pool.py           # 数据库连接池管理
│   ├── llm_client.py        # LLM客户端封装
│   ├── rate_limiter.py      # 限流器
│   └── circuit_breaker.py   # 熔断器
├── tools/
│   ├── __init__.py
│   ├── query_tool.py        # query工具
│   ├── schema_tools.py      # list_*/describe_*工具
│   └── admin_tools.py       # refresh_schema等管理工具
└── resources/
    ├── __init__.py
    └── schema_resources.py  # schema://资源处理
```

### 3.2 配置管理 (config/settings.py)

```python
from pydantic import BaseModel, Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Literal
from pathlib import Path


class DatabaseConfig(BaseModel):
    """单个数据库连接配置"""
    name: str = Field(..., description="数据库别名")
    host: str = Field(default="localhost")
    port: int = Field(default=5432)
    database: str = Field(..., description="数据库名")
    username: str
    password: SecretStr
    ssl_mode: Literal["disable", "prefer", "require", "verify-ca", "verify-full"] = "prefer"
    schemas: list[str] = Field(default=["public"])
    exclude_tables: list[str] = Field(default_factory=list)
    min_pool_size: int = Field(default=2, ge=1)
    max_pool_size: int = Field(default=10, ge=1)


class LLMConfig(BaseModel):
    """LLM配置（DeepSeek使用OpenAI兼容API）"""
    api_key: SecretStr
    base_url: str = Field(default="https://api.deepseek.com/v1")
    model: str = Field(default="deepseek-chat")
    temperature: float = Field(default=0.1, ge=0, le=2)
    max_tokens: int = Field(default=2048, ge=1)
    timeout: int = Field(default=30, ge=1)


class SecurityConfig(BaseModel):
    """安全配置"""
    max_rows: int = Field(default=200, ge=1, description="默认最大返回行数")
    hard_max_rows: int = Field(default=1000, ge=1, description="硬上限")
    query_timeout: int = Field(default=30, ge=1, description="查询超时秒数")
    allowed_functions: list[str] = Field(default_factory=list, description="函数白名单")
    sensitive_columns: list[str] = Field(
        default=["password", "secret", "token", "credential", "ssn", "credit_card"],
        description="敏感列名模式"
    )
    enable_result_validation: bool = Field(default=True)
    max_retry_attempts: int = Field(default=3, ge=1)
    validation_sample_rows: int = Field(default=20, ge=1)
    validation_sample_cols: int = Field(default=10, ge=1)


class RateLimitConfig(BaseModel):
    """限流配置"""
    llm_requests_per_minute: int = Field(default=60)
    db_queries_per_minute: int = Field(default=100)
    enable_circuit_breaker: bool = Field(default=True)
    circuit_breaker_threshold: int = Field(default=5, description="连续失败次数触发熔断")
    circuit_breaker_timeout: int = Field(default=60, description="熔断恢复时间秒数")


class CacheConfig(BaseModel):
    """缓存配置"""
    enable_disk_cache: bool = Field(default=True)
    cache_dir: Path = Field(default=Path(".pg_mcp_cache"))
    cache_ttl_hours: int = Field(default=24)
    auto_refresh_interval_hours: int = Field(default=0, description="0表示禁用自动刷新")


class Settings(BaseSettings):
    """应用主配置"""
    model_config = SettingsConfigDict(
        env_prefix="PG_MCP_",
        env_nested_delimiter="__",
        yaml_file="pg_mcp.yaml",
        yaml_file_encoding="utf-8",
    )

    databases: list[DatabaseConfig]
    llm: LLMConfig
    security: SecurityConfig = Field(default_factory=SecurityConfig)
    rate_limit: RateLimitConfig = Field(default_factory=RateLimitConfig)
    cache: CacheConfig = Field(default_factory=CacheConfig)
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
```

### 3.3 数据模型 (models/)

#### 3.3.1 Schema模型 (models/schema.py)

```python
from pydantic import BaseModel, Field
from typing import Literal
from enum import Enum


class ColumnInfo(BaseModel):
    """列信息"""
    name: str
    data_type: str
    nullable: bool = True
    default: str | None = None
    comment: str | None = None
    is_primary_key: bool = False
    is_foreign_key: bool = False
    references: str | None = None  # 格式: "schema.table.column"


class IndexInfo(BaseModel):
    """索引信息"""
    name: str
    columns: list[str]
    is_unique: bool = False
    is_primary: bool = False
    index_type: str = "btree"  # btree, hash, gin, gist, etc.


class ForeignKeyInfo(BaseModel):
    """外键信息"""
    name: str
    columns: list[str]
    references_schema: str
    references_table: str
    references_columns: list[str]
    on_delete: str = "NO ACTION"
    on_update: str = "NO ACTION"


class TableInfo(BaseModel):
    """表信息"""
    schema_name: str
    table_name: str
    columns: list[ColumnInfo]
    primary_key: list[str] = Field(default_factory=list)
    foreign_keys: list[ForeignKeyInfo] = Field(default_factory=list)
    indexes: list[IndexInfo] = Field(default_factory=list)
    comment: str | None = None
    row_estimate: int | None = None  # 估算行数


class ViewInfo(BaseModel):
    """视图信息"""
    schema_name: str
    view_name: str
    columns: list[ColumnInfo]
    definition: str | None = None
    comment: str | None = None


class EnumTypeInfo(BaseModel):
    """枚举类型信息"""
    schema_name: str
    type_name: str
    values: list[str]


class CompositeTypeInfo(BaseModel):
    """复合类型信息"""
    schema_name: str
    type_name: str
    attributes: list[ColumnInfo]


class SchemaInfo(BaseModel):
    """Schema信息"""
    name: str
    tables: dict[str, TableInfo] = Field(default_factory=dict)
    views: dict[str, ViewInfo] = Field(default_factory=dict)
    enum_types: dict[str, EnumTypeInfo] = Field(default_factory=dict)
    composite_types: dict[str, CompositeTypeInfo] = Field(default_factory=dict)


class DatabaseInfo(BaseModel):
    """数据库信息"""
    name: str
    schemas: dict[str, SchemaInfo] = Field(default_factory=dict)
    version: str | None = None
    loaded_at: str | None = None  # ISO格式时间戳
```

#### 3.3.2 查询模型 (models/query.py)

```python
from pydantic import BaseModel, Field
from typing import Literal, Any


class QueryRequest(BaseModel):
    """查询请求"""
    query: str = Field(..., description="自然语言查询描述")
    database: str | None = Field(default=None, description="目标数据库")
    schema: str = Field(default="public", description="目标schema")
    return_type: Literal["sql", "result"] = Field(default="result")
    max_rows: int | None = Field(default=None, ge=1)
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=100, ge=1, le=1000)


class SQLGenerationResult(BaseModel):
    """SQL生成结果"""
    sql: str
    explanation: str
    confidence: float = Field(ge=0, le=1)
    warnings: list[str] = Field(default_factory=list)


class QueryResultData(BaseModel):
    """查询结果数据"""
    sql: str
    columns: list[str]
    rows: list[dict[str, Any]]
    row_count: int
    total_count: int | None = None  # 总行数（如果可知）
    truncated: bool = False
    page: int = 1
    page_size: int = 100
    execution_time_ms: int
    explanation: str


class QueryResponse(BaseModel):
    """查询响应"""
    success: bool
    data: SQLGenerationResult | QueryResultData | None = None
    error: "ErrorDetail | None" = None


class ErrorDetail(BaseModel):
    """错误详情"""
    code: str
    type: str
    message: str
    details: dict[str, Any] = Field(default_factory=dict)
    retryable: bool = False
    suggestion: str | None = None
    retry_after_ms: int | None = None
```

#### 3.3.3 错误模型 (models/errors.py)

```python
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
```

---

## 4. 安全层设计

### 4.1 SQL校验器 (security/sql_validator.py)

```python
import sqlglot
from sqlglot import exp
from sqlglot.errors import ParseError
from typing import NamedTuple

from pg_mcp.models.errors import SecurityViolationError


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
        exp.Truncate,
        exp.Grant,
        exp.Revoke,
        exp.Commit,
        exp.Rollback,
    }

    # 禁止的表达式类型
    FORBIDDEN_EXPRESSION_TYPES: set[type] = {
        exp.Into,      # SELECT ... INTO
        exp.Command,   # COPY, EXECUTE, CALL, DO
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
        normalized = parsed[0].sql(dialect="postgres") if is_valid and parsed else None

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
                    violations.append(f"CTE中包含禁止的操作: {forbidden.__name__}")
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
            func_name = func.name.lower() if hasattr(func, 'name') else str(func.key).lower()

            # 检查黑名单
            if func_name in self.DANGEROUS_FUNCTIONS:
                violations.append(f"禁止调用危险函数: {func_name}")

            # 如果配置了白名单，则检查白名单
            if self.allowed_functions and func_name not in self.allowed_functions:
                # 允许常见的聚合和标准函数
                if not self._is_safe_builtin(func_name):
                    violations.append(f"函数不在白名单中: {func_name}")

        return violations

    def _is_safe_builtin(self, func_name: str) -> bool:
        """检查是否是安全的内置函数"""
        safe_builtins = {
            # 聚合函数
            "count", "sum", "avg", "min", "max", "array_agg", "string_agg",
            # 字符串函数
            "lower", "upper", "trim", "substring", "length", "concat", "replace",
            # 日期函数
            "now", "current_date", "current_timestamp", "date_trunc", "extract",
            "age", "date_part", "to_char", "to_date", "to_timestamp",
            # 数学函数
            "abs", "ceil", "floor", "round", "trunc", "mod", "power", "sqrt",
            # 条件函数
            "coalesce", "nullif", "greatest", "least", "case",
            # 类型转换
            "cast", "convert",
            # JSON函数
            "json_agg", "jsonb_agg", "json_build_object", "jsonb_build_object",
            "json_extract_path", "jsonb_extract_path",
            # 窗口函数
            "row_number", "rank", "dense_rank", "ntile", "lag", "lead",
            "first_value", "last_value",
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
```

### 4.2 敏感数据脱敏器 (security/sanitizer.py)

```python
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
```

---

## 5. 基础设施层设计

### 5.1 数据库连接池管理器 (infrastructure/db_pool.py)

```python
import asyncio
from contextlib import asynccontextmanager
from typing import AsyncIterator

import asyncpg
from asyncpg import Pool, Connection

from pg_mcp.config.settings import DatabaseConfig
from pg_mcp.models.errors import PgMcpError, ErrorCode


class DBPoolManager:
    """数据库连接池管理器"""

    def __init__(self):
        self._pools: dict[str, Pool] = {}
        self._configs: dict[str, DatabaseConfig] = {}
        self._lock = asyncio.Lock()

    async def initialize(self, configs: list[DatabaseConfig]) -> None:
        """初始化所有数据库连接池"""
        for config in configs:
            await self._create_pool(config)

    async def _create_pool(self, config: DatabaseConfig) -> Pool:
        """创建单个数据库连接池"""
        dsn = self._build_dsn(config)
        try:
            pool = await asyncpg.create_pool(
                dsn,
                min_size=config.min_pool_size,
                max_size=config.max_pool_size,
                command_timeout=60,
                server_settings={
                    "application_name": "pg_mcp",
                },
            )
            self._pools[config.name] = pool
            self._configs[config.name] = config
            return pool
        except Exception as e:
            raise PgMcpError(
                code=ErrorCode.DATABASE_CONNECTION_ERROR,
                message=f"无法连接到数据库 {config.name}: {e}",
                retryable=True,
            )

    def _build_dsn(self, config: DatabaseConfig) -> str:
        """构建数据库连接字符串"""
        password = config.password.get_secret_value()
        return (
            f"postgresql://{config.username}:{password}"
            f"@{config.host}:{config.port}/{config.database}"
            f"?sslmode={config.ssl_mode}"
        )

    def get_pool(self, db_name: str) -> Pool:
        """获取指定数据库的连接池"""
        if db_name not in self._pools:
            raise PgMcpError(
                code=ErrorCode.DATABASE_CONNECTION_ERROR,
                message=f"数据库 {db_name} 未配置",
            )
        return self._pools[db_name]

    @asynccontextmanager
    async def acquire_readonly(
        self, db_name: str, timeout: int = 30
    ) -> AsyncIterator[Connection]:
        """获取只读连接"""
        pool = self.get_pool(db_name)
        async with pool.acquire(timeout=timeout) as conn:
            # 设置只读事务
            await conn.execute("SET TRANSACTION READ ONLY")
            await conn.execute(f"SET statement_timeout = '{timeout}s'")
            yield conn

    async def close_all(self) -> None:
        """关闭所有连接池"""
        for pool in self._pools.values():
            await pool.close()
        self._pools.clear()

    def list_databases(self) -> list[str]:
        """列出所有已配置的数据库"""
        return list(self._pools.keys())
```

### 5.2 LLM客户端封装 (infrastructure/llm_client.py)

```python
import json
from typing import Any

from openai import AsyncOpenAI
from openai.types.chat import ChatCompletion

from pg_mcp.config.settings import LLMConfig
from pg_mcp.models.errors import PgMcpError, ErrorCode


class LLMClient:
    """LLM客户端（使用OpenAI兼容API对接DeepSeek）"""

    # NL2SQL系统提示词
    NL2SQL_SYSTEM_PROMPT = """你是一个PostgreSQL SQL专家。根据用户的自然语言描述和提供的数据库schema信息，生成精确的SQL查询语句。

要求：
1. 只生成SELECT语句
2. 使用标准PostgreSQL语法
3. 合理使用JOIN、WHERE、GROUP BY、ORDER BY等子句
4. 考虑性能优化，避免SELECT *
5. 根据schema信息选择正确的表和列
6. 对于模糊的需求，选择最合理的解释

输出格式（JSON）：
{
  "sql": "生成的SQL语句",
  "explanation": "SQL逻辑说明",
  "confidence": 0.0-1.0的置信度
}"""

    VALIDATION_SYSTEM_PROMPT = """你是一个SQL查询结果验证专家。根据用户的原始查询意图、生成的SQL和查询结果样本，评估结果是否满足用户需求。

输出格式（JSON）：
{
  "is_valid": true/false,
  "reason": "验证结论说明",
  "suggestions": ["改进建议列表"]
}"""

    def __init__(self, config: LLMConfig):
        self.config = config
        self.client = AsyncOpenAI(
            api_key=config.api_key.get_secret_value(),
            base_url=config.base_url,
            timeout=config.timeout,
        )

    async def generate_sql(
        self,
        user_query: str,
        schema_context: str,
    ) -> dict[str, Any]:
        """根据自然语言生成SQL"""
        messages = [
            {"role": "system", "content": self.NL2SQL_SYSTEM_PROMPT},
            {"role": "user", "content": f"""数据库Schema信息：
{schema_context}

用户查询：{user_query}

请生成SQL查询。"""},
        ]

        try:
            response = await self._chat_completion(messages)
            return self._parse_json_response(response)
        except Exception as e:
            raise PgMcpError(
                code=ErrorCode.LLM_ERROR,
                message=f"LLM调用失败: {e}",
                retryable=True,
            )

    async def validate_result(
        self,
        user_query: str,
        sql: str,
        result_summary: dict[str, Any],
    ) -> dict[str, Any]:
        """验证查询结果是否符合用户意图"""
        messages = [
            {"role": "system", "content": self.VALIDATION_SYSTEM_PROMPT},
            {"role": "user", "content": f"""用户原始查询：{user_query}

生成的SQL：{sql}

结果摘要：{json.dumps(result_summary, ensure_ascii=False, indent=2)}

请验证结果是否满足用户需求。"""},
        ]

        try:
            response = await self._chat_completion(messages)
            return self._parse_json_response(response)
        except Exception as e:
            # 验证失败时降级处理，不阻塞主流程
            return {"is_valid": True, "reason": f"验证跳过: {e}", "suggestions": []}

    async def _chat_completion(self, messages: list[dict]) -> ChatCompletion:
        """调用Chat Completion API"""
        return await self.client.chat.completions.create(
            model=self.config.model,
            messages=messages,
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens,
            response_format={"type": "json_object"},
        )

    def _parse_json_response(self, response: ChatCompletion) -> dict[str, Any]:
        """解析JSON响应"""
        content = response.choices[0].message.content
        if not content:
            raise ValueError("LLM返回空响应")
        return json.loads(content)
```

### 5.3 限流器 (infrastructure/rate_limiter.py)

```python
import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Callable, TypeVar, ParamSpec

from aiolimiter import AsyncLimiter

from pg_mcp.config.settings import RateLimitConfig
from pg_mcp.models.errors import PgMcpError, ErrorCode


P = ParamSpec("P")
T = TypeVar("T")


class CircuitState(Enum):
    CLOSED = "closed"      # 正常状态
    OPEN = "open"          # 熔断状态
    HALF_OPEN = "half_open"  # 半开状态


@dataclass
class CircuitBreaker:
    """熔断器"""
    threshold: int
    timeout: int
    state: CircuitState = CircuitState.CLOSED
    failure_count: int = 0
    last_failure_time: datetime | None = None

    def record_failure(self) -> None:
        self.failure_count += 1
        self.last_failure_time = datetime.now()
        if self.failure_count >= self.threshold:
            self.state = CircuitState.OPEN

    def record_success(self) -> None:
        self.failure_count = 0
        self.state = CircuitState.CLOSED

    def can_execute(self) -> bool:
        if self.state == CircuitState.CLOSED:
            return True
        if self.state == CircuitState.OPEN:
            if self.last_failure_time:
                elapsed = datetime.now() - self.last_failure_time
                if elapsed > timedelta(seconds=self.timeout):
                    self.state = CircuitState.HALF_OPEN
                    return True
            return False
        return True  # HALF_OPEN允许尝试


class RateLimiter:
    """限流管理器"""

    def __init__(self, config: RateLimitConfig):
        self.config = config
        self.llm_limiter = AsyncLimiter(
            config.llm_requests_per_minute, 60
        )
        self.db_limiter = AsyncLimiter(
            config.db_queries_per_minute, 60
        )
        self.llm_circuit = CircuitBreaker(
            threshold=config.circuit_breaker_threshold,
            timeout=config.circuit_breaker_timeout,
        )
        self.db_circuit = CircuitBreaker(
            threshold=config.circuit_breaker_threshold,
            timeout=config.circuit_breaker_timeout,
        )

    async def acquire_llm(self) -> None:
        """获取LLM调用许可"""
        if not self.llm_circuit.can_execute():
            raise PgMcpError(
                code=ErrorCode.CIRCUIT_BREAKER_OPEN,
                message="LLM服务熔断中",
                retryable=True,
                details={"retry_after_ms": self.config.circuit_breaker_timeout * 1000},
            )
        await self.llm_limiter.acquire()

    async def acquire_db(self) -> None:
        """获取数据库查询许可"""
        if not self.db_circuit.can_execute():
            raise PgMcpError(
                code=ErrorCode.CIRCUIT_BREAKER_OPEN,
                message="数据库服务熔断中",
                retryable=True,
                details={"retry_after_ms": self.config.circuit_breaker_timeout * 1000},
            )
        await self.db_limiter.acquire()

    def record_llm_success(self) -> None:
        self.llm_circuit.record_success()

    def record_llm_failure(self) -> None:
        self.llm_circuit.record_failure()

    def record_db_success(self) -> None:
        self.db_circuit.record_success()

    def record_db_failure(self) -> None:
        self.db_circuit.record_failure()
```

---

## 6. 服务层设计

### 6.1 Schema服务 (services/schema_service.py)

```python
import asyncio
import json
from datetime import datetime
from pathlib import Path
from typing import Any

from pg_mcp.config.settings import Settings, CacheConfig
from pg_mcp.infrastructure.db_pool import DBPoolManager
from pg_mcp.models.schema import (
    DatabaseInfo, SchemaInfo, TableInfo, ViewInfo,
    ColumnInfo, ForeignKeyInfo, IndexInfo, EnumTypeInfo,
)
from pg_mcp.models.errors import PgMcpError, ErrorCode


class SchemaService:
    """Schema管理服务"""

    # Schema加载SQL
    TABLES_QUERY = """
    SELECT
        t.table_schema,
        t.table_name,
        obj_description((t.table_schema || '.' || t.table_name)::regclass) as table_comment,
        (SELECT reltuples::bigint FROM pg_class WHERE oid = (t.table_schema || '.' || t.table_name)::regclass) as row_estimate
    FROM information_schema.tables t
    WHERE t.table_schema = $1 AND t.table_type = 'BASE TABLE'
    ORDER BY t.table_name
    """

    COLUMNS_QUERY = """
    SELECT
        c.column_name,
        c.data_type,
        c.is_nullable = 'YES' as nullable,
        c.column_default,
        col_description((c.table_schema || '.' || c.table_name)::regclass, c.ordinal_position) as comment
    FROM information_schema.columns c
    WHERE c.table_schema = $1 AND c.table_name = $2
    ORDER BY c.ordinal_position
    """

    PRIMARY_KEY_QUERY = """
    SELECT a.attname
    FROM pg_index i
    JOIN pg_attribute a ON a.attrelid = i.indrelid AND a.attnum = ANY(i.indkey)
    WHERE i.indrelid = ($1 || '.' || $2)::regclass AND i.indisprimary
    """

    FOREIGN_KEYS_QUERY = """
    SELECT
        tc.constraint_name,
        kcu.column_name,
        ccu.table_schema AS references_schema,
        ccu.table_name AS references_table,
        ccu.column_name AS references_column
    FROM information_schema.table_constraints tc
    JOIN information_schema.key_column_usage kcu
        ON tc.constraint_name = kcu.constraint_name
    JOIN information_schema.constraint_column_usage ccu
        ON ccu.constraint_name = tc.constraint_name
    WHERE tc.table_schema = $1 AND tc.table_name = $2 AND tc.constraint_type = 'FOREIGN KEY'
    """

    def __init__(
        self,
        db_pool: DBPoolManager,
        cache_config: CacheConfig,
    ):
        self.db_pool = db_pool
        self.cache_config = cache_config
        self._cache: dict[str, DatabaseInfo] = {}
        self._lock = asyncio.Lock()

    async def load_all(self, db_name: str, schemas: list[str]) -> DatabaseInfo:
        """加载数据库的所有schema信息"""
        async with self._lock:
            # 尝试从磁盘缓存加载
            if self.cache_config.enable_disk_cache:
                cached = self._load_from_disk(db_name)
                if cached:
                    self._cache[db_name] = cached
                    # 异步刷新
                    asyncio.create_task(self._refresh_in_background(db_name, schemas))
                    return cached

            # 从数据库加载
            db_info = await self._load_from_db(db_name, schemas)
            self._cache[db_name] = db_info

            # 持久化到磁盘
            if self.cache_config.enable_disk_cache:
                self._save_to_disk(db_name, db_info)

            return db_info

    async def _load_from_db(self, db_name: str, schemas: list[str]) -> DatabaseInfo:
        """从数据库加载schema信息"""
        db_info = DatabaseInfo(name=db_name, loaded_at=datetime.now().isoformat())

        async with self.db_pool.acquire_readonly(db_name) as conn:
            # 获取PG版本
            version = await conn.fetchval("SELECT version()")
            db_info.version = version

            for schema_name in schemas:
                schema_info = await self._load_schema(conn, schema_name)
                db_info.schemas[schema_name] = schema_info

        return db_info

    async def _load_schema(self, conn, schema_name: str) -> SchemaInfo:
        """加载单个schema"""
        schema_info = SchemaInfo(name=schema_name)

        # 加载表
        tables = await conn.fetch(self.TABLES_QUERY, schema_name)
        for table_row in tables:
            table_info = await self._load_table(conn, schema_name, table_row)
            schema_info.tables[table_info.table_name] = table_info

        return schema_info

    async def _load_table(self, conn, schema_name: str, table_row) -> TableInfo:
        """加载单个表的详细信息"""
        table_name = table_row["table_name"]

        # 加载列
        columns_rows = await conn.fetch(self.COLUMNS_QUERY, schema_name, table_name)
        columns = [
            ColumnInfo(
                name=row["column_name"],
                data_type=row["data_type"],
                nullable=row["nullable"],
                default=row["column_default"],
                comment=row["comment"],
            )
            for row in columns_rows
        ]

        # 加载主键
        pk_rows = await conn.fetch(self.PRIMARY_KEY_QUERY, schema_name, table_name)
        primary_key = [row["attname"] for row in pk_rows]

        # 标记主键列
        pk_set = set(primary_key)
        for col in columns:
            if col.name in pk_set:
                col.is_primary_key = True

        # 加载外键
        fk_rows = await conn.fetch(self.FOREIGN_KEYS_QUERY, schema_name, table_name)
        foreign_keys = self._group_foreign_keys(fk_rows)

        return TableInfo(
            schema_name=schema_name,
            table_name=table_name,
            columns=columns,
            primary_key=primary_key,
            foreign_keys=foreign_keys,
            comment=table_row["table_comment"],
            row_estimate=table_row["row_estimate"],
        )

    def _group_foreign_keys(self, fk_rows) -> list[ForeignKeyInfo]:
        """将外键行分组"""
        fk_map: dict[str, ForeignKeyInfo] = {}
        for row in fk_rows:
            name = row["constraint_name"]
            if name not in fk_map:
                fk_map[name] = ForeignKeyInfo(
                    name=name,
                    columns=[],
                    references_schema=row["references_schema"],
                    references_table=row["references_table"],
                    references_columns=[],
                )
            fk_map[name].columns.append(row["column_name"])
            fk_map[name].references_columns.append(row["references_column"])
        return list(fk_map.values())

    def get_cached(self, db_name: str) -> DatabaseInfo | None:
        """获取缓存的schema信息"""
        return self._cache.get(db_name)

    def format_for_llm(self, db_name: str, schema_name: str) -> str:
        """格式化schema信息供LLM使用"""
        db_info = self._cache.get(db_name)
        if not db_info:
            return ""

        schema_info = db_info.schemas.get(schema_name)
        if not schema_info:
            return ""

        lines = [f"Schema: {schema_name}\n"]
        for table_name, table in schema_info.tables.items():
            lines.append(f"\nTable: {table_name}")
            if table.comment:
                lines.append(f"  Comment: {table.comment}")
            lines.append("  Columns:")
            for col in table.columns:
                pk = " [PK]" if col.is_primary_key else ""
                nullable = " NULL" if col.nullable else " NOT NULL"
                comment = f" -- {col.comment}" if col.comment else ""
                lines.append(f"    - {col.name}: {col.data_type}{nullable}{pk}{comment}")
            if table.foreign_keys:
                lines.append("  Foreign Keys:")
                for fk in table.foreign_keys:
                    lines.append(
                        f"    - {fk.columns} -> {fk.references_schema}.{fk.references_table}({fk.references_columns})"
                    )
        return "\n".join(lines)

    def _load_from_disk(self, db_name: str) -> DatabaseInfo | None:
        """从磁盘加载缓存"""
        cache_file = self.cache_config.cache_dir / f"{db_name}.json"
        if not cache_file.exists():
            return None
        try:
            data = json.loads(cache_file.read_text())
            return DatabaseInfo.model_validate(data)
        except Exception:
            return None

    def _save_to_disk(self, db_name: str, db_info: DatabaseInfo) -> None:
        """保存缓存到磁盘"""
        self.cache_config.cache_dir.mkdir(parents=True, exist_ok=True)
        cache_file = self.cache_config.cache_dir / f"{db_name}.json"
        cache_file.write_text(db_info.model_dump_json(indent=2))

    async def _refresh_in_background(self, db_name: str, schemas: list[str]) -> None:
        """后台刷新缓存"""
        try:
            db_info = await self._load_from_db(db_name, schemas)
            self._cache[db_name] = db_info
            if self.cache_config.enable_disk_cache:
                self._save_to_disk(db_name, db_info)
        except Exception:
            pass  # 后台刷新失败不影响主流程
```

### 6.2 查询服务 (services/query_service.py)

```python
import time
from typing import Any

from pg_mcp.config.settings import Settings
from pg_mcp.infrastructure.db_pool import DBPoolManager
from pg_mcp.infrastructure.llm_client import LLMClient
from pg_mcp.infrastructure.rate_limiter import RateLimiter
from pg_mcp.models.query import (
    QueryRequest, QueryResponse, QueryResultData,
    SQLGenerationResult, ErrorDetail,
)
from pg_mcp.models.errors import PgMcpError, ErrorCode
from pg_mcp.security.sql_validator import SQLValidator
from pg_mcp.security.sanitizer import Sanitizer
from pg_mcp.services.schema_service import SchemaService


class QueryService:
    """查询服务 - 编排NL2SQL的完整流程"""

    def __init__(
        self,
        settings: Settings,
        db_pool: DBPoolManager,
        schema_service: SchemaService,
        llm_client: LLMClient,
        rate_limiter: RateLimiter,
    ):
        self.settings = settings
        self.db_pool = db_pool
        self.schema_service = schema_service
        self.llm_client = llm_client
        self.rate_limiter = rate_limiter
        self.sql_validator = SQLValidator(settings.security.allowed_functions)
        self.sanitizer = Sanitizer(settings.security.sensitive_columns)

    async def execute_query(self, request: QueryRequest) -> QueryResponse:
        """执行自然语言查询"""
        try:
            # 1. 确定目标数据库
            db_name = request.database or self.db_pool.list_databases()[0]

            # 2. 获取schema上下文
            schema_context = self.schema_service.format_for_llm(
                db_name, request.schema
            )
            if not schema_context:
                raise PgMcpError(
                    code=ErrorCode.SCHEMA_LOAD_ERROR,
                    message=f"Schema {request.schema} 未找到",
                )

            # 3. 调用LLM生成SQL
            await self.rate_limiter.acquire_llm()
            try:
                llm_result = await self.llm_client.generate_sql(
                    request.query, schema_context
                )
                self.rate_limiter.record_llm_success()
            except Exception as e:
                self.rate_limiter.record_llm_failure()
                raise

            sql = llm_result.get("sql", "")
            explanation = llm_result.get("explanation", "")
            confidence = llm_result.get("confidence", 0.5)

            # 4. SQL安全校验
            validated_sql = self.sql_validator.validate_or_raise(sql)

            # 5. 如果只需要SQL，直接返回
            if request.return_type == "sql":
                return QueryResponse(
                    success=True,
                    data=SQLGenerationResult(
                        sql=validated_sql,
                        explanation=explanation,
                        confidence=confidence,
                    ),
                )

            # 6. 执行SQL
            result_data = await self._execute_sql(
                db_name, validated_sql, request, explanation
            )

            # 7. 结果验证（可选）
            if self.settings.security.enable_result_validation:
                await self._validate_result(request.query, validated_sql, result_data)

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

    async def _execute_sql(
        self,
        db_name: str,
        sql: str,
        request: QueryRequest,
        explanation: str,
    ) -> QueryResultData:
        """执行SQL并返回结果"""
        await self.rate_limiter.acquire_db()

        # 计算分页
        max_rows = min(
            request.max_rows or self.settings.security.max_rows,
            self.settings.security.hard_max_rows,
        )
        offset = (request.page - 1) * request.page_size
        limit = min(request.page_size, max_rows)

        # 添加LIMIT/OFFSET（如果原SQL没有）
        paginated_sql = self._add_pagination(sql, limit + 1, offset)  # +1检测是否有更多

        start_time = time.monotonic()
        try:
            async with self.db_pool.acquire_readonly(
                db_name, self.settings.security.query_timeout
            ) as conn:
                rows = await conn.fetch(paginated_sql)
                self.rate_limiter.record_db_success()
        except Exception as e:
            self.rate_limiter.record_db_failure()
            raise PgMcpError(
                code=ErrorCode.SQL_EXECUTION_ERROR,
                message=f"SQL执行失败: {e}",
                details={"sql": sql},
                retryable=True,
            )

        execution_time_ms = int((time.monotonic() - start_time) * 1000)

        # 处理结果
        truncated = len(rows) > limit
        if truncated:
            rows = rows[:limit]

        columns = list(rows[0].keys()) if rows else []
        row_dicts = [dict(r) for r in rows]

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
        # 准备脱敏采样数据
        _, safe_rows = self.sanitizer.sanitize_for_llm(
            result.columns,
            result.rows,
            max_rows=self.settings.security.validation_sample_rows,
            max_cols=self.settings.security.validation_sample_cols,
        )

        summary = self.sanitizer.generate_summary(
            result.columns, result.rows, result.row_count
        )

        # 调用LLM验证
        validation = await self.llm_client.validate_result(
            user_query, sql, summary
        )

        if not validation.get("is_valid", True):
            # 可以记录日志或添加警告，但不阻塞返回
            result.explanation += f"\n[验证警告] {validation.get('reason', '')}"
```

---

## 7. MCP服务器层设计

### 7.1 FastMCP服务器 (server.py)

```python
from fastmcp import FastMCP
from pydantic import Field

from pg_mcp.config.settings import Settings
from pg_mcp.infrastructure.db_pool import DBPoolManager
from pg_mcp.infrastructure.llm_client import LLMClient
from pg_mcp.infrastructure.rate_limiter import RateLimiter
from pg_mcp.services.schema_service import SchemaService
from pg_mcp.services.query_service import QueryService
from pg_mcp.models.query import QueryRequest


# 创建FastMCP实例
mcp = FastMCP(
    name="pg-mcp",
    version="0.1.0",
    description="PostgreSQL MCP Server - 自然语言查询数据库",
)

# 全局服务实例（在lifespan中初始化）
settings: Settings
db_pool: DBPoolManager
schema_service: SchemaService
query_service: QueryService


@mcp.lifespan
async def lifespan():
    """应用生命周期管理"""
    global settings, db_pool, schema_service, query_service

    # 加载配置
    settings = Settings()

    # 初始化基础设施
    db_pool = DBPoolManager()
    await db_pool.initialize(settings.databases)

    llm_client = LLMClient(settings.llm)
    rate_limiter = RateLimiter(settings.rate_limit)

    # 初始化服务
    schema_service = SchemaService(db_pool, settings.cache)
    query_service = QueryService(
        settings, db_pool, schema_service, llm_client, rate_limiter
    )

    # 预加载schema
    for db_config in settings.databases:
        await schema_service.load_all(db_config.name, db_config.schemas)

    yield

    # 清理
    await db_pool.close_all()


# ========== Tools ==========

@mcp.tool()
async def query(
    query: str = Field(..., description="自然语言查询描述"),
    database: str | None = Field(default=None, description="目标数据库名称"),
    schema: str = Field(default="public", description="目标schema"),
    return_type: str = Field(default="result", description="返回类型: sql 或 result"),
    max_rows: int | None = Field(default=None, description="最大返回行数"),
) -> dict:
    """执行自然语言查询，返回SQL或查询结果"""
    request = QueryRequest(
        query=query,
        database=database,
        schema=schema,
        return_type=return_type,  # type: ignore
        max_rows=max_rows,
    )
    response = await query_service.execute_query(request)
    return response.model_dump()


@mcp.tool()
async def list_databases() -> list[str]:
    """列出所有可用的数据库"""
    return db_pool.list_databases()


@mcp.tool()
async def list_schemas(
    database: str = Field(..., description="数据库名称"),
) -> list[str]:
    """列出指定数据库的所有schema"""
    db_info = schema_service.get_cached(database)
    if not db_info:
        return []
    return list(db_info.schemas.keys())


@mcp.tool()
async def list_tables(
    database: str = Field(..., description="数据库名称"),
    schema: str = Field(default="public", description="schema名称"),
) -> list[dict]:
    """列出指定schema的所有表"""
    db_info = schema_service.get_cached(database)
    if not db_info:
        return []
    schema_info = db_info.schemas.get(schema)
    if not schema_info:
        return []
    return [
        {
            "name": t.table_name,
            "comment": t.comment,
            "row_estimate": t.row_estimate,
        }
        for t in schema_info.tables.values()
    ]


@mcp.tool()
async def describe_table(
    database: str = Field(..., description="数据库名称"),
    schema: str = Field(default="public", description="schema名称"),
    table: str = Field(..., description="表名"),
) -> dict | None:
    """获取表的详细结构"""
    db_info = schema_service.get_cached(database)
    if not db_info:
        return None
    schema_info = db_info.schemas.get(schema)
    if not schema_info:
        return None
    table_info = schema_info.tables.get(table)
    if not table_info:
        return None
    return table_info.model_dump()


@mcp.tool()
async def refresh_schema(
    database: str | None = Field(default=None, description="数据库名称，空则刷新全部"),
) -> dict:
    """刷新schema缓存"""
    refreshed = []
    for db_config in settings.databases:
        if database and db_config.name != database:
            continue
        await schema_service.load_all(db_config.name, db_config.schemas)
        refreshed.append(db_config.name)
    return {"refreshed": refreshed}


# ========== Resources ==========

@mcp.resource("schema://databases")
async def get_databases() -> str:
    """获取所有数据库列表"""
    dbs = db_pool.list_databases()
    return "\n".join(dbs)


@mcp.resource("schema://{database}/schemas")
async def get_schemas(database: str) -> str:
    """获取指定数据库的schema列表"""
    db_info = schema_service.get_cached(database)
    if not db_info:
        return f"Database {database} not found"
    return "\n".join(db_info.schemas.keys())


@mcp.resource("schema://{database}/{schema}/tables")
async def get_tables(database: str, schema: str) -> str:
    """获取表列表"""
    db_info = schema_service.get_cached(database)
    if not db_info:
        return f"Database {database} not found"
    schema_info = db_info.schemas.get(schema)
    if not schema_info:
        return f"Schema {schema} not found"
    return "\n".join(schema_info.tables.keys())


@mcp.resource("schema://{database}/{schema}/{table}")
async def get_table_detail(database: str, schema: str, table: str) -> str:
    """获取表详情"""
    return schema_service.format_for_llm(database, schema)
```

### 7.2 入口点 (__main__.py)

```python
import asyncio
import sys

from pg_mcp.server import mcp


def main():
    """主入口"""
    # FastMCP自动处理stdio/SSE传输
    mcp.run()


if __name__ == "__main__":
    main()
```

---

## 8. 配置文件示例

### 8.1 pg_mcp.yaml

```yaml
databases:
  - name: "main"
    host: "localhost"
    port: 5432
    database: "myapp"
    username: "${DB_USER}"
    password: "${DB_PASSWORD}"
    ssl_mode: "prefer"
    schemas:
      - "public"
      - "sales"
    exclude_tables:
      - "internal_logs"
    min_pool_size: 2
    max_pool_size: 10

llm:
  api_key: "${DEEPSEEK_API_KEY}"
  base_url: "https://api.deepseek.com/v1"
  model: "deepseek-chat"
  temperature: 0.1
  max_tokens: 2048
  timeout: 30

security:
  max_rows: 200
  hard_max_rows: 1000
  query_timeout: 30
  allowed_functions: []
  sensitive_columns:
    - "password"
    - "secret"
    - "token"
    - "credential"
    - "ssn"
    - "credit_card"
  enable_result_validation: true
  max_retry_attempts: 3

rate_limit:
  llm_requests_per_minute: 60
  db_queries_per_minute: 100
  enable_circuit_breaker: true
  circuit_breaker_threshold: 5
  circuit_breaker_timeout: 60

cache:
  enable_disk_cache: true
  cache_dir: ".pg_mcp_cache"
  cache_ttl_hours: 24
  auto_refresh_interval_hours: 0

log_level: "INFO"
```

### 8.2 pyproject.toml

```toml
[project]
name = "pg-mcp"
version = "0.1.0"
description = "PostgreSQL MCP Server - Natural Language to SQL"
requires-python = ">=3.10"
dependencies = [
    "fastmcp>=2.0",
    "asyncpg>=0.29",
    "sqlglot>=25.0",
    "pydantic>=2.0",
    "pydantic-settings>=2.0",
    "openai>=1.0",
    "aiolimiter>=1.1",
    "structlog>=24.0",
    "pyyaml>=6.0",
]

[project.scripts]
pg-mcp = "pg_mcp.__main__:main"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

---

## 9. 核心流程时序图

### 9.1 自然语言查询流程

```
┌──────┐     ┌─────────┐     ┌────────────┐     ┌───────────┐     ┌─────────┐     ┌────┐
│Client│     │MCP Layer│     │QueryService│     │SchemaServ │     │LLMClient│     │ DB │
└──┬───┘     └────┬────┘     └─────┬──────┘     └─────┬─────┘     └────┬────┘     └─┬──┘
   │              │                │                  │                │            │
   │ query(nl)    │                │                  │                │            │
   │─────────────>│                │                  │                │            │
   │              │ execute_query()│                  │                │            │
   │              │───────────────>│                  │                │            │
   │              │                │ format_for_llm() │                │            │
   │              │                │─────────────────>│                │            │
   │              │                │<─────────────────│                │            │
   │              │                │                  │                │            │
   │              │                │ generate_sql(nl, schema)          │            │
   │              │                │───────────────────────────────────>            │
   │              │                │<───────────────────────────────────            │
   │              │                │                  │                │            │
   │              │                │ validate_sql()   │                │            │
   │              │                │──────┐           │                │            │
   │              │                │<─────┘           │                │            │
   │              │                │                  │                │            │
   │              │                │ execute(sql)                                   │
   │              │                │────────────────────────────────────────────────>
   │              │                │<────────────────────────────────────────────────
   │              │                │                  │                │            │
   │              │                │ validate_result()(optional)       │            │
   │              │                │───────────────────────────────────>            │
   │              │                │<───────────────────────────────────            │
   │              │                │                  │                │            │
   │              │<───────────────│                  │                │            │
   │<─────────────│                │                  │                │            │
   │   result     │                │                  │                │            │
```

---

## 10. 安全设计总结

| 安全层面 | 实现方式 | 对应需求 |
|----------|----------|----------|
| **SQL注入防护** | SQLGlot AST解析，拒绝非SELECT语句 | F-018~F-026 |
| **只读保证** | `SET TRANSACTION READ ONLY` + 最小权限账户 | F-027, F-027a |
| **函数白名单** | FunctionGuard检查，默认拒绝未知函数 | F-024, F-024a, F-025 |
| **敏感数据脱敏** | Sanitizer过滤敏感列，限制发送给LLM的数据量 | F-034a, F-034b |
| **凭据安全** | Pydantic SecretStr + 环境变量 | NF-005, NF-006 |
| **限流熔断** | RateLimiter + CircuitBreaker | NF-017~NF-019 |
| **查询超时** | statement_timeout + asyncpg timeout | F-028, NF-003 |

---

## 11. 测试策略

| 测试类型 | 覆盖范围 | 工具 |
|----------|----------|------|
| 单元测试 | SQLValidator, Sanitizer, 数据模型 | pytest, pytest-asyncio |
| 集成测试 | SchemaService, QueryService与真实PG交互 | pytest, testcontainers |
| 安全测试 | SQL注入向量、危险函数调用 | 手工构造恶意输入 |
| 性能测试 | Schema加载时间、并发查询 | locust, pytest-benchmark |

---

## 12. 部署方式

### 12.1 MCP配置（Claude Desktop）

```json
{
  "mcpServers": {
    "pg-mcp": {
      "command": "python",
      "args": ["-m", "pg_mcp"],
      "env": {
        "DB_USER": "readonly_user",
        "DB_PASSWORD": "secret",
        "DEEPSEEK_API_KEY": "sk-xxx"
      }
    }
  }
}
```

### 12.2 Docker部署

```dockerfile
FROM python:3.12-slim

WORKDIR /app
COPY . .
RUN pip install --no-cache-dir .

ENTRYPOINT ["pg-mcp"]
```

---

## 修订历史

| 版本 | 日期 | 修改内容 | 作者 |
|------|------|----------|------|
| v0.1 | 2026-01-11 | 初稿 | AI Assistant |

