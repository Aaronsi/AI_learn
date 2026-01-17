# pg-mcp 代码评审报告

范围：评审 `w5/pg-mcp` 代码与 `specs/w5/0002-pg-mcp-design.md`、`specs/w5/0004-pg-mcp-impl-plan.md` 一致性，关注 Python best practices、SOLID/DRY、代码质量、测试质量、性能与安全。

结论摘要：
- 结构分层与主要模块基本符合设计与实现计划。
- 存在多处与需求不符或会导致功能不可用/误报的问题，尤其是 SQL 文字常量处理与只读事务设置。
- 测试以 Mock 为主，缺少关键集成/性能/监控类测试，覆盖面与真实性不足。

## 主要问题（按严重程度）

### 高
1) **禁止所有字符串字面量会导致大量正常查询失败**  
`QueryService` 在通过 SQL 校验后直接拒绝任何字符串字面量，意味着例如 “name = 'Alice'” 这类最常见的条件查询都会被拦截；同时也会拦截双引号标识符。此行为与设计文档的 “文字常量检查” 不一致（要求是长度/转义检查，而非全禁），会导致 NL2SQL 功能严重不可用。  

```158:189:w5/pg-mcp/pg_mcp/services/query_service.py
    def _check_literal_constants(self, sql: str) -> None:
        """检查SQL中的文字常量（长度限制、特殊字符告警）"""
        # 匹配字符串字面量（单引号或双引号）
        string_pattern = r"['\"]([^'\"]*)['\"]"
        matches = re.finditer(string_pattern, sql)
        ...

    def _reject_string_literals(self, sql: str) -> None:
        """禁止直接使用字符串字面量，要求参数化"""
        string_pattern = r"'[^']*'|\"[^\"]*\""
        if re.search(string_pattern, sql):
            raise SecurityViolationError(
                message="SQL中包含直接字符串字面量，需改为参数化查询",
                sql=sql,
                violation="检测到字符串字面量",
            )
```

2) **只读事务设置可能无效，无法保证 F-027 要求**  
`SET TRANSACTION READ ONLY` 在 PostgreSQL 中需要位于事务块内（或使用 `SET default_transaction_read_only` / `BEGIN READ ONLY`）。当前实现未显式开启事务，可能导致只读保护失效或抛错，违背安全要求。  

```68:82:w5/pg-mcp/pg_mcp/infrastructure/db_pool.py
    async def acquire_readonly(
        self, db_name: str, timeout: int = 30
    ) -> AsyncIterator[Connection]:
        """获取只读连接并按需降权"""
        pool = self.get_pool(db_name)
        config = self._configs[db_name]
        async with pool.acquire(timeout=timeout) as conn:
            # 可选降权角色
            if config.role:
                await conn.execute(f"SET ROLE {config.role}")
            # 设置只读事务与超时
            await conn.execute("SET TRANSACTION READ ONLY")
            await conn.execute(f"SET statement_timeout = '{timeout}s'")
            yield conn
```

### 中
3) **Schema 加载缺少视图/枚举/复合类型/索引信息**  
设计文档包含 View/Enum/Composite/Index 的模型与输出，但 `SchemaService` 仅加载表/列/PK/FK，未加载视图与类型信息，`schema://` 资源输出不完整，偏离设计与实现计划。  

```138:206:w5/pg-mcp/pg_mcp/services/schema_service.py
    async def _load_schema(
        self,
        conn,
        schema_name: str,
        exclude_tables: list[str],
    ) -> SchemaInfo:
        """加载单个schema"""
        schema_info = SchemaInfo(name=schema_name)

        # 加载表
        tables = await conn.fetch(self.TABLES_QUERY, schema_name)
        for table_row in tables:
            ...
            table_info = await self._load_table(conn, schema_name, table_row)
            schema_info.tables[table_info.table_name] = table_info

        return schema_info
```

4) **验证服务丢弃采样行，LLM 验证信息不足**  
`ValidationService` 调用 `sanitize_for_llm` 后未使用返回的 `safe_rows`，实际仅发送摘要统计，导致验证对实际数据感知不足，弱化结果验证能力。  

```23:36:w5/pg-mcp/pg_mcp/services/validation_service.py
    async def validate(
        self, user_query: str, sql: str, result: QueryResultData
    ) -> dict:
        """返回验证结果和说明，不阻断主流程"""
        _, safe_rows = self.sanitizer.sanitize_for_llm(
            result.columns,
            result.rows,
            max_rows=self.sample_rows,
            max_cols=self.sample_cols,
        )
        summary = self.sanitizer.generate_summary(
            result.columns, result.rows, result.row_count
        )
        return await self.llm_client.validate_result(user_query, sql, summary)
```

5) **健康检查未真正验证 DB 可用性**  
健康检查只获取连接池对象，不执行简单查询或连接探测，存在 “配置正常但 DB 实际不可用” 时误报健康。  

```183:193:w5/pg-mcp/pg_mcp/infrastructure/metrics.py
    async def _check_db(self) -> dict[str, Any]:
        """检查数据库连接"""
        try:
            databases = self.db_pool.list_databases()
            if not databases:
                return {"status": "error", "message": "No databases configured"}
            # 尝试获取一个连接池
            pool = self.db_pool.get_pool(databases[0])
            return {"status": "ok", "databases": len(databases)}
        except Exception as e:
            return {"status": "error", "message": str(e)}
```

6) **缓存命中率指标不可用**  
`Metrics` 预留了缓存命中/未命中统计，但 `SchemaService` 逻辑中未记录命中/未命中，`metrics_summary` 中的缓存指标不可用/误导。  

```57:63:w5/pg-mcp/pg_mcp/infrastructure/metrics.py
    def record_cache_hit(self, hit: bool) -> None:
        """记录缓存命中"""
        if hit:
            self.cache_hits += 1
        else:
            self.cache_misses += 1
```

### 低
7) **日志与脱敏体系未落地，structlog 未接入**  
实现计划要求结构化日志与脱敏输出，但当前没有 structlog 配置/使用，`LogSanitizer` 仅在 SQL 错误摘要中使用，LLM 请求/响应未脱敏记录。  

8) **Token 成本控制缺少成本计算与日志集成**  
`TokenMeter` 仅记录 token 数量，成本始终为 0，报警采用 `print`，不适合生产日志体系。  

```41:49:w5/pg-mcp/pg_mcp/infrastructure/token_meter.py
    def _trigger_alert(self, alert_type: str, details: dict) -> None:
        """触发告警"""
        message = f"Token meter alert: {alert_type}"
        if self.alert_callback:
            self.alert_callback(message, details)
        else:
            # 默认日志输出
            print(f"WARNING: {message} - {details}")
```

9) **分页拼接判断过于粗糙**  
`_add_pagination` 仅以 `limit/offset` 关键字判断，若 SQL 中包含字符串或注释出现 `limit`，可能导致不加分页或重复分页。  

```259:266:w5/pg-mcp/pg_mcp/services/query_service.py
    def _add_pagination(self, sql: str, limit: int, offset: int) -> str:
        """为SQL添加分页"""
        sql_lower = sql.lower().strip()
        if "limit" not in sql_lower:
            sql = f"{sql.rstrip(';')} LIMIT {limit}"
        if offset > 0 and "offset" not in sql_lower:
            sql = f"{sql} OFFSET {offset}"
        return sql
```

10) **测试深度不足，集成测试真实性有限**  
多数 “集成测试” 实际为 Mock；真实 PostgreSQL 连接测试被 skip，缺少 testcontainers 与性能测试，覆盖度与真实场景差距较大。  

```9:16:w5/pg-mcp/pg_mcp/tests/integration/test_db_pool.py
@pytest.mark.asyncio
@pytest.mark.integration
async def test_db_pool_connection():
    """Test database pool connection (requires real PostgreSQL)"""
    # This test requires a real PostgreSQL instance
    # Skip if not available
    pytest.skip("Requires real PostgreSQL instance")
```

## 设计/实现计划一致性检查（摘要）
- **符合**：基础模块与分层结构、FastMCP 生命周期、SQL AST 校验、限流/熔断、Schema 缓存、工具/资源接口总体对齐。
- **不符合或缺失**：
  - Schema 视图/枚举/复合类型/索引加载缺失（影响 F-004/F-008 与 schema 资源完整性）。
  - 只读事务保证存在风险（F-027）。
  - 文字常量检查过度（与 P3-2l 目标不一致）。
  - 监控/日志/健康检查与 token 成本控制未达到 P5 要求。
  - 测试与性能验证不足（P6 要求未充分满足）。

## SOLID / DRY / Python Best Practices
- **SRP/SOLID**：`QueryService` 同时负责流程编排、安全检查、限流、指标、token 成本、日志脱敏，职责过多，建议拆分为专用协作组件以便测试与替换。
- **DRY**：函数白名单逻辑在 `SQLValidator` 与 `FunctionGuard` 重叠，维护成本与行为一致性风险较高。
- **Python idiomatic**：整体类型标注与 Pydantic 使用符合规范；但存在明显逻辑过度限制（字符串字面量全禁）与事务语义问题。

## 测试与性能
- 单元测试覆盖核心安全组件，质量尚可。
- 缺少：真实 PG 集成测试、性能/负载测试、健康检查/监控/TokenMeter/LogSanitizer 的测试。
- 指标采集未闭环（缓存命中率、成本计算），性能/稳定性可观测性不足。

## 建议优先级（可执行）
1) 移除“禁止字符串字面量”的硬拦截，仅保留长度/转义检查；双引号识别为标识符而非字面量。
2) 在 `acquire_readonly` 中使用事务块或 `SET default_transaction_read_only = on` 以保证只读。
3) 补齐 Schema 视图/类型/索引加载与资源输出。
4) 健康检查增加最小 DB 查询探测（`SELECT 1`）并处理超时。
5) 接入 structlog；LLM 请求/响应/SQL 错误统一脱敏记录。
6) 引入 testcontainers 或可选的真实 PG 集成测试；补充性能与监控类测试。
## pg-mcp Implementation Code Review

Scope: `./w5/pg-mcp` vs `0002-pg-mcp-design.md` and `0004-pg-mcp-impl-plan.md`. Focus on correctness, security, observability, Pythonic quality, SOLID/DRY, and tests.

### Key Findings

- **Critical – Missing health/metrics exposure & wiring**: No MCP tools/resources or endpoints expose health checks or metrics as required in Phases 5.3/4. Server only registers query/schema tools; `Metrics`/`HealthChecker` are never instantiated. This blocks operability/monitoring acceptance.
- **High – Token metering/cost control unused**: `TokenMeter` exists but is never constructed or consulted; no LLM usage stats or degradation paths (skip validation/return-sql-only) are enforced. Plan Phase 5.4 not met.
- **High – Log sanitization unused**: `LogSanitizer` is implemented but not integrated into LLM calls, DB errors, or logging. Plan Phase 5.5 requires sanitizing LLM requests/responses and SQL errors before logging.
- **High – No parameter binding for executed SQL**: Queries returned by LLM are executed directly via `conn.fetch(paginated_sql)` without bound parameters or parameterization layer. This violates plan feedback (all execution must use parameter binding) and leaves risk if validation misses literal injection.

```155:185:pg_mcp/services/query_service.py
        try:
            async with self.db_pool.acquire_readonly(
                db_name, self.settings.security.query_timeout
            ) as conn:
                # 直接使用 conn.fetch，禁止任何字符串拼接
                rows = await conn.fetch(paginated_sql)
```

- **Medium – Circuit breaker & rate-limit metrics not recorded**: `RateLimiter` does not feed `Metrics`; success/failure is tracked only inside limiter, leaving observability gaps for DB/LLM latency and breaker status required by Phase 5.3.
- **Medium – Auto-refresh task handling is single-instance**: `SchemaService.start_auto_refresh` stores a single `_refresh_task`; starting refresh for multiple databases will overwrite the previous task, so only the last DB gets periodic refresh. Plan requires per-DB scheduled refresh and status.

```315:334:pg_mcp/services/schema_service.py
    def start_auto_refresh(...):
        ...
        self._refresh_task = asyncio.create_task(refresh_loop())
```

- **Medium – Validation/metrics not linked**: Query execution/LLM calls do not record metrics (`Metrics.record_query_time`, `record_llm_call`, `record_tokens`) and do not attach token usage from LLM responses; truncation is not recorded via `Metrics.record_truncation`. This misses success criteria for monitoring.
- **Medium – Health check is defined but unused**: `HealthChecker` is implemented yet never created or exposed as a tool/resource. No readiness/liveness hooks for MCP clients.
- **Low – Resource detail uses broad schema**: `get_table_detail` returns `format_for_llm` for the whole schema, not the specific table, increasing payload and reducing clarity.

### Testing & Tooling

- Unit tests and security integration tests pass under `uv run pytest` for exercised modules, but full suite fails when run via system `pytest` due to `ModuleNotFoundError: openai`. Ensure tests run through the managed environment (`uv run pytest`) or make tests resilient to optional LLM dependency (e.g., mock `LLMClient` in integration tests). Integration tests that require a real DB are skipped; acceptance for DB/LLM integration remains unverified.
- `.venv` lacks `pip`, so invoking `python -m pip` inside venv fails; rely on `uv` for installs or add `pip` if direct installs are needed.

### Design/Plan Alignment Gaps

- Phase 5.3/5.4/5.5 observability, token metering, and log sanitization are not wired into runtime.
- Phase 3 feedback on parameter binding is not implemented; still executing raw SQL strings.
- Health/metrics MCP interfaces are missing; acceptance criteria for operability not met.
- Auto-refresh scheduling/status exposure partially implemented (single task, no per-DB status surface).

### Recommendations (prio order)

1) Wire observability: instantiate `Metrics`, `TokenMeter`, `LogSanitizer`, `HealthChecker` in server lifespan; pass them into services; add MCP tools/resources for health/metrics/status. Record metrics in QueryService (LLM/db latency, truncations, cache hit/miss) and RateLimiter.
2) Enforce parameterized execution: normalize LLM SQL into prepared statements with bound params or refuse literals; add a parameter binding layer and tests. At minimum, reject queries with literals unless explicitly allowed.
3) Integrate token metering: consume LLM `usage` to record tokens/cost; apply degradation rules (`should_skip_validation`, `should_return_sql_only`).
4) Apply log sanitization: sanitize LLM requests/responses and SQL errors before logging; add structured logging (`structlog`) with redaction.
5) Fix auto-refresh per DB: track tasks per database and expose refresh status via MCP resource/tool.
6) Stabilize tests: ensure `uv run pytest` is the documented path; mock LLM in integration tests to avoid external deps; add health/metrics/token-meter tests per plan Phase 5/6.

