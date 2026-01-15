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

