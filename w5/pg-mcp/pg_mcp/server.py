"""FastMCP server definition"""

from fastmcp import FastMCP
from pydantic import Field

from pg_mcp.config.settings import Settings
from pg_mcp.infrastructure.db_pool import DBPoolManager
from pg_mcp.infrastructure.llm_client import LLMClient
from pg_mcp.infrastructure.rate_limiter import RateLimiter
from pg_mcp.infrastructure.metrics import Metrics, HealthChecker
from pg_mcp.infrastructure.token_meter import TokenMeter
from pg_mcp.infrastructure.log_sanitizer import LogSanitizer
from pg_mcp.services.schema_service import SchemaService
from pg_mcp.services.query_service import QueryService
from pg_mcp.models.query import QueryRequest
from pg_mcp.security.sanitizer import Sanitizer
from pg_mcp.services.validation_service import ValidationService


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
rate_limiter: RateLimiter
metrics: Metrics
token_meter: TokenMeter
log_sanitizer: LogSanitizer
health_checker: HealthChecker


@mcp.lifespan
async def lifespan():
    """应用生命周期管理"""
    global settings, db_pool, schema_service, query_service, rate_limiter, metrics, token_meter, log_sanitizer, health_checker

    # 加载配置
    settings = Settings()

    # 初始化基础设施
    db_pool = DBPoolManager()
    await db_pool.initialize(settings.databases)

    llm_client = LLMClient(settings.llm)
    rate_limiter = RateLimiter(settings.rate_limit)
    sanitizer = Sanitizer(settings.security.sensitive_columns)
    log_sanitizer = LogSanitizer(settings.security.sensitive_columns)
    metrics = Metrics()
    token_meter = TokenMeter(metrics)
    validation_service = ValidationService(
        sanitizer,
        llm_client,
        settings.security.validation_sample_rows,
        settings.security.validation_sample_cols,
    )
    health_checker = HealthChecker(db_pool, llm_client, None, rate_limiter)

    # 初始化服务
    schema_service = SchemaService(db_pool, settings.cache)
    query_service = QueryService(
        settings,
        db_pool,
        schema_service,
        llm_client,
        rate_limiter,
        metrics,
        token_meter,
        log_sanitizer,
        validation_service,
    )
    # health_checker 需要 schema_service 引用
    health_checker.schema_service = schema_service

    # 预加载schema
    for db_config in settings.databases:
        await schema_service.load_all(
            db_config.name,
            db_config.schemas,
            db_config.exclude_tables,
        )
        # 启动定时自动刷新（如果配置）
        if settings.cache.auto_refresh_interval_hours > 0:
            schema_service.start_auto_refresh(
                db_config.name,
                db_config.schemas,
                db_config.exclude_tables,
            )

    yield

    # 清理
    schema_service.stop_auto_refresh()
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
        await schema_service.load_all(
            db_config.name,
            db_config.schemas,
            db_config.exclude_tables,
        )
        refreshed.append(db_config.name)
    return {"refreshed": refreshed}


@mcp.tool()
async def health() -> dict:
    """健康检查"""
    return await health_checker.check_health()


@mcp.tool()
async def metrics_summary() -> dict:
    """核心指标摘要"""
    summary = metrics.get_summary()
    summary["circuit_breaker"] = rate_limiter.get_circuit_status()
    return summary


@mcp.tool()
async def refresh_status(
    database: str = Field(..., description="数据库名称"),
) -> dict | None:
    """获取指定数据库的schema刷新状态"""
    return schema_service.get_refresh_status(database)


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
