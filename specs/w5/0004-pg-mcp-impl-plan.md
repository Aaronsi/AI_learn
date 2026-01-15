# PostgreSQL MCP Server 实现计划

## 文档信息

| 项目 | 内容 |
|------|------|
| 文档版本 | v0.1 |
| 创建日期 | 2026-01-11 |
| 关联设计文档 | 0002-pg-mcp-design.md |
| 关联PRD | 0001-pg-mcp-prd.md |

---

## 1. 实现概述

### 1.1 项目范围

基于设计文档实现 pg-mcp 服务器，包含以下核心能力：
- 自然语言转 SQL（NL2SQL）
- Schema 自动发现与缓存
- SQL 安全校验（AST级别）
- 只读查询执行
- 结果验证与脱敏
- MCP 协议集成

### 1.2 技术栈确认

| 组件 | 版本 | 用途 |
|------|------|------|
| Python | ≥3.10 | 运行时 |
| FastMCP | ≥2.0 | MCP 协议实现 |
| asyncpg | ≥0.29 | PostgreSQL 异步驱动 |
| SQLGlot | ≥25.0 | SQL 解析与安全校验 |
| Pydantic | ≥2.0 | 数据模型与配置 |
| openai | ≥1.0 | LLM 客户端 |
| aiolimiter | ≥1.1 | 异步限流 |
| structlog | ≥24.0 | 结构化日志 |

### 1.3 实现原则

1. **分层实现**：按 基础设施层 → 安全层 → 服务层 → MCP层 顺序构建
2. **测试驱动**：每个模块完成后立即编写单元测试
3. **增量交付**：每个阶段产出可运行、可测试的版本
4. **最小可行**：P0 需求优先，P1/P2 后续迭代

---

## 2. 阶段划分

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Phase 0: 项目初始化                                                         │
│  ├── 项目结构搭建                                                            │
│  ├── 依赖管理配置                                                            │
│  └── 开发环境准备                                                            │
├─────────────────────────────────────────────────────────────────────────────┤
│  Phase 1: 基础设施层                                                         │
│  ├── 配置管理 (Settings)                                                     │
│  ├── 数据模型 (Schema, Query, Error)                                         │
│  ├── 数据库连接池 (DBPoolManager)                                            │
│  └── LLM 客户端 (LLMClient)                                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│  Phase 2: 安全层                                                             │
│  ├── SQL 校验器 (SQLValidator)                                               │
│  ├── 函数守卫 (FunctionGuard)                                                │
│  └── 数据脱敏器 (Sanitizer)                                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│  Phase 3: 服务层                                                             │
│  ├── Schema 服务 (SchemaService)                                             │
│  ├── 查询服务 (QueryService)                                                 │
│  └── 验证服务 (ValidationService)                                            │
├─────────────────────────────────────────────────────────────────────────────┤
│  Phase 4: MCP 协议层                                                         │
│  ├── FastMCP 服务器集成                                                      │
│  ├── Tools 实现 (query, list_*, describe_*, refresh_schema)                  │
│  └── Resources 实现 (schema://)                                              │
├─────────────────────────────────────────────────────────────────────────────┤
│  Phase 5: 限流/熔断/监控                                                      │
│  ├── 限流器 (RateLimiter)                                                    │
│  ├── 熔断器 (CircuitBreaker)                                                 │
│  └── 健康检查与指标                                                          │
├─────────────────────────────────────────────────────────────────────────────┤
│  Phase 6: 集成测试与文档                                                      │
│  ├── 端到端测试                                                              │
│  ├── 安全测试                                                                │
│  └── 用户文档                                                                │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. 详细任务分解

### Phase 0: 项目初始化 (0.5天)

#### 任务清单

| 任务ID | 任务描述 | 产出物 | 依赖 |
|--------|----------|--------|------|
| P0-1 | 创建项目目录结构 | `pg_mcp/` 完整目录树 | - |
| P0-2 | 配置 pyproject.toml | 依赖声明、入口点配置 | P0-1 |
| P0-3 | 配置开发工具 | ruff.toml, mypy.ini, pytest.ini | P0-2 |
| P0-4 | 创建示例配置文件 | pg_mcp.yaml.example | P0-1 |
| P0-5 | 编写 README.md | 项目说明、快速开始指南 | P0-4 |

#### 目录结构

```
pg_mcp/
├── __init__.py
├── __main__.py
├── py.typed                 # PEP 561 类型标记
├── server.py
├── config/
│   ├── __init__.py
│   └── settings.py
├── models/
│   ├── __init__.py
│   ├── schema.py
│   ├── query.py
│   └── errors.py
├── services/
│   ├── __init__.py
│   ├── query_service.py
│   ├── schema_service.py
│   └── validation_service.py
├── security/
│   ├── __init__.py
│   ├── sql_validator.py
│   ├── function_guard.py
│   └── sanitizer.py
├── infrastructure/
│   ├── __init__.py
│   ├── db_pool.py
│   ├── llm_client.py
│   └── rate_limiter.py
└── tests/
    ├── __init__.py
    ├── conftest.py
    ├── unit/
    │   ├── test_sql_validator.py
    │   ├── test_sanitizer.py
    │   └── test_models.py
    └── integration/
        ├── test_schema_service.py
        └── test_query_service.py
```

#### 验收标准

- [ ] `uv sync` 成功安装所有依赖
- [ ] `python -m pg_mcp --help` 正常输出
- [ ] `pytest` 空测试通过
- [ ] `ruff check .` 无错误
- [ ] `mypy .` 无错误

---

### Phase 1: 基础设施层 (1.5天)

#### 1.1 配置管理 (config/settings.py)

| 任务ID | 任务描述 | 复杂度 |
|--------|----------|--------|
| P1-1a | 实现 DatabaseConfig 模型 | 低 |
| P1-1b | 实现 LLMConfig 模型 | 低 |
| P1-1c | 实现 SecurityConfig 模型 | 低 |
| P1-1d | 实现 RateLimitConfig 模型 | 低 |
| P1-1e | 实现 CacheConfig 模型 | 低 |
| P1-1f | 实现 Settings 主配置类（支持YAML+环境变量） | 中 |
| P1-1g | 编写配置加载单元测试 | 低 |

**关键实现点**：
- 使用 `pydantic-settings` 的 `SettingsConfigDict` 配置 YAML 加载
- `SecretStr` 保护敏感字段
- 环境变量覆盖机制（`PG_MCP_` 前缀）

#### 1.2 数据模型 (models/)

| 任务ID | 任务描述 | 复杂度 |
|--------|----------|--------|
| P1-2a | 实现 Schema 相关模型 (ColumnInfo, TableInfo, SchemaInfo, DatabaseInfo) | 中 |
| P1-2b | 实现 Query 相关模型 (QueryRequest, QueryResponse, QueryResultData) | 中 |
| P1-2c | 实现 Error 模型 (ErrorCode, PgMcpError, 派生异常类) | 低 |
| P1-2d | 编写模型序列化/反序列化测试 | 低 |

**关键实现点**：
- 所有模型继承 `pydantic.BaseModel`
- `ErrorCode` 使用 `str, Enum` 便于 JSON 序列化
- `QueryResponse` 使用联合类型区分成功/失败

#### 1.3 数据库连接池 (infrastructure/db_pool.py)

| 任务ID | 任务描述 | 复杂度 |
|--------|----------|--------|
| P1-3a | 实现 DBPoolManager 初始化与连接池创建 | 中 |
| P1-3b | 实现 DSN 构建（含 SSL 模式） | 低 |
| P1-3c | 实现 `acquire_readonly` 上下文管理器 | 高 |
| P1-3d | 实现可选 `SET ROLE` 降权 | 中 |
| P1-3e | 实现连接池关闭与清理 | 低 |
| P1-3f | 编写连接池集成测试（需 PostgreSQL） | 中 |

**关键实现点**：
```python
@asynccontextmanager
async def acquire_readonly(self, db_name: str, timeout: int = 30):
    pool = self.get_pool(db_name)
    config = self._configs[db_name]
    async with pool.acquire(timeout=timeout) as conn:
        if config.role:
            await conn.execute(f"SET ROLE {config.role}")
        await conn.execute("SET TRANSACTION READ ONLY")
        await conn.execute(f"SET statement_timeout = '{timeout}s'")
        yield conn
```

#### 1.4 LLM 客户端 (infrastructure/llm_client.py)

| 任务ID | 任务描述 | 复杂度 |
|--------|----------|--------|
| P1-4a | 实现 LLMClient 初始化（AsyncOpenAI） | 低 |
| P1-4b | 实现 NL2SQL 系统提示词 | 中 |
| P1-4c | 实现 `generate_sql` 方法 | 中 |
| P1-4d | 实现 Validation 系统提示词 | 中 |
| P1-4e | 实现 `validate_result` 方法（含降级处理） | 中 |
| P1-4f | 实现 JSON 响应解析与错误处理 | 低 |
| P1-4g | 编写 LLM 客户端 Mock 测试 | 中 |

**关键实现点**：
- 使用 `response_format={"type": "json_object"}` 强制 JSON 输出
- 验证失败时返回降级结果，不阻塞主流程

#### Phase 1 验收标准

- [ ] 配置从 YAML 和环境变量正确加载
- [ ] 数据模型可正确序列化/反序列化
- [ ] 连接池可连接真实 PostgreSQL 并执行只读查询
- [ ] LLM 客户端可调用 DeepSeek API（或 Mock）
- [ ] 所有单元测试通过

---

### Phase 2: 安全层 (1天)

#### 2.1 SQL 校验器 (security/sql_validator.py)

| 任务ID | 任务描述 | 复杂度 | PRD需求 |
|--------|----------|--------|---------|
| P2-1a | 实现 SQLGlot 解析封装 | 低 | F-018 |
| P2-1b | 实现禁止语句类型检查 (INSERT/UPDATE/DELETE/DDL) | 中 | F-019~F-023 |
| P2-1c | 实现 CTE 安全检查 | 高 | F-018a |
| P2-1d | 实现禁止表达式检查 (INTO, COPY, CALL) | 中 | F-018b |
| P2-1e | 实现危险函数黑名单检查 | 中 | F-024 |
| P2-1f | 实现 `validate_or_raise` 方法 | 低 | - |
| P2-1g | 编写安全校验单元测试（含恶意SQL样本） | 高 | - |

**测试用例矩阵**：

| 用例 | SQL | 预期结果 |
|------|-----|----------|
| 正常SELECT | `SELECT * FROM users` | 通过 |
| INSERT | `INSERT INTO users VALUES (1)` | 拒绝 |
| CTE中DELETE | `WITH d AS (DELETE FROM users RETURNING *) SELECT * FROM d` | 拒绝 |
| SELECT INTO | `SELECT * INTO new_table FROM users` | 拒绝 |
| pg_sleep | `SELECT pg_sleep(100)` | 拒绝 |
| 嵌套子查询DELETE | `SELECT * FROM (DELETE FROM users RETURNING *)` | 拒绝 |

#### 2.2 函数守卫 (security/function_guard.py)

| 任务ID | 任务描述 | 复杂度 | PRD需求 |
|--------|----------|--------|---------|
| P2-2a | 定义默认安全函数白名单 | 低 | F-024a |
| P2-2b | 实现 `validate_functions` 方法 | 中 | F-024a |
| P2-2c | 支持配置扩展白名单 | 低 | F-025 |
| P2-2d | 编写函数守卫测试 | 中 | - |

**默认白名单分类**：
- 聚合函数：count, sum, avg, min, max, array_agg, string_agg
- 字符串函数：lower, upper, trim, substring, length, concat
- 日期函数：now, current_date, date_trunc, extract, to_char
- 数学函数：abs, ceil, floor, round, mod, power
- 窗口函数：row_number, rank, dense_rank, lag, lead

#### 2.3 数据脱敏器 (security/sanitizer.py)

| 任务ID | 任务描述 | 复杂度 | PRD需求 |
|--------|----------|--------|---------|
| P2-3a | 实现敏感列名模式匹配 | 低 | F-034a |
| P2-3b | 实现 `sanitize_for_llm` 方法（行列限制） | 中 | F-034a |
| P2-3c | 实现 `generate_summary` 方法（统计摘要） | 中 | F-034b |
| P2-3d | 编写脱敏器测试 | 低 | - |

**脱敏规则**：
- 列名匹配：password, secret, token, credential, ssn, credit_card
- 采样限制：≤20行、≤10列
- 统计摘要：行数、列名、数值列min/max/avg、字符串列unique_count

#### Phase 2 验收标准

- [ ] SQL 校验器拦截所有 DML/DDL 语句
- [ ] CTE 中的危险操作被正确检测
- [ ] 危险函数调用被拒绝
- [ ] 敏感列在发送给 LLM 前被过滤
- [ ] 采样数据符合配置的行列限制
- [ ] 安全测试用例 100% 通过

---

### Phase 3: 服务层 (2天)

#### 3.1 Schema 服务 (services/schema_service.py)

| 任务ID | 任务描述 | 复杂度 | PRD需求 |
|--------|----------|--------|---------|
| P3-1a | 实现表加载 SQL 查询 | 中 | F-004 |
| P3-1b | 实现列加载 SQL 查询（含注释） | 中 | F-004 |
| P3-1c | 实现主键加载 | 低 | F-004 |
| P3-1d | 实现外键加载与分组 | 中 | F-008 |
| P3-1e | 实现 `_load_table` 完整流程 | 高 | F-004 |
| P3-1f | 实现 `_load_schema` 批量加载表 | 中 | F-003 |
| P3-1g | 实现 exclude_tables 通配符过滤 | 低 | - |
| P3-1h | 实现 `load_all` 入口（含锁） | 中 | F-002 |
| P3-1i | 实现磁盘缓存读写 | 中 | F-003b |
| P3-1j | 实现缓存 TTL 校验 | 低 | F-003b |
| P3-1k | 实现后台异步刷新 | 中 | F-003a |
| P3-1l | 实现定时自动刷新调度（auto_refresh_interval_hours>0时启动循环任务） | 中 | F-010 |
| P3-1m | 实现刷新状态暴露（last_refresh_time, refresh_status） | 低 | F-010a |
| P3-1n | 实现刷新失败回退（保留旧缓存、记录错误） | 中 | F-010a |
| P3-1o | 实现 `format_for_llm` 格式化输出 | 中 | F-014 |
| P3-1p | 编写 Schema 服务集成测试 | 高 | - |

**Schema 加载 SQL**：

```sql
-- 表信息
SELECT t.table_schema, t.table_name,
       obj_description((t.table_schema || '.' || t.table_name)::regclass) as table_comment,
       (SELECT reltuples::bigint FROM pg_class WHERE oid = ...) as row_estimate
FROM information_schema.tables t
WHERE t.table_schema = $1 AND t.table_type = 'BASE TABLE';

-- 列信息
SELECT c.column_name, c.data_type, c.is_nullable = 'YES' as nullable,
       c.column_default,
       col_description(..., c.ordinal_position) as comment
FROM information_schema.columns c
WHERE c.table_schema = $1 AND c.table_name = $2;
```

#### 3.2 查询服务 (services/query_service.py)

| 任务ID | 任务描述 | 复杂度 | PRD需求 |
|--------|----------|--------|---------|
| P3-2a | 实现 `execute_query` 主流程编排 | 高 | F-011~F-017 |
| P3-2b | 实现数据库选择逻辑 | 低 | F-012 |
| P3-2c | 实现 Schema 上下文获取 | 低 | F-014 |
| P3-2d | 实现 LLM 调用与限流集成 | 中 | F-015 |
| P3-2e | 实现 SQL 安全校验调用 | 低 | F-018 |
| P3-2f | 实现 SQL 执行（只读事务） | 中 | F-027 |
| P3-2g | 实现分页逻辑 (LIMIT/OFFSET) | 中 | F-017a |
| P3-2h | 实现结果格式化 | 低 | F-032 |
| P3-2i | 实现结果验证调用 | 中 | F-034~F-038 |
| P3-2j | 实现错误处理与响应构造 | 中 | - |
| P3-2k | 实现SQL执行安全：禁止额外拼接、使用conn.fetch直接执行 | 低 | F-026 |
| P3-2l | 实现文字常量检查（长度限制、特殊字符告警） | 中 | F-026 |
| P3-2m | 编写查询服务集成测试 | 高 | - |

**SQL执行安全说明**：
- LLM生成的SQL是完整语句，不做参数绑定（无外部用户输入需绑定）
- 执行层直接使用`conn.fetch(sql)`，禁止任何字符串拼接
- 对SQL中的文字常量进行合理性检查：字符串长度≤1000，无异常转义序列

**核心流程**：

```
1. 确定目标数据库 → 2. 获取 Schema 上下文 → 3. LLM 生成 SQL
→ 4. SQL 安全校验 → 5. 只读执行 → 6. 结果验证 → 7. 返回响应
```

#### 3.3 验证服务 (services/validation_service.py)

| 任务ID | 任务描述 | 复杂度 | PRD需求 |
|--------|----------|--------|---------|
| P3-3a | 实现 ValidationService 初始化 | 低 | - |
| P3-3b | 实现 `validate` 方法（脱敏+摘要+LLM调用） | 中 | F-034~F-035 |
| P3-3c | 编写验证服务测试 | 中 | - |

#### Phase 3 验收标准

- [ ] Schema 从 PostgreSQL 正确加载
- [ ] Schema 缓存到磁盘并可恢复
- [ ] 缓存 TTL 过期后触发后台刷新
- [ ] 定时刷新任务按配置间隔执行（auto_refresh_interval_hours>0时）
- [ ] 刷新状态可通过接口/日志查看
- [ ] 刷新失败时保留旧缓存，不影响服务
- [ ] 自然语言查询端到端执行成功
- [ ] SQL执行层无额外字符串拼接
- [ ] 分页参数正确应用
- [ ] 结果验证正常工作（或优雅降级）
- [ ] 所有服务层测试通过

---

### Phase 4: MCP 协议层 (1天)

#### 4.1 FastMCP 服务器集成

| 任务ID | 任务描述 | 复杂度 |
|--------|----------|--------|
| P4-1a | 创建 FastMCP 实例 | 低 |
| P4-1b | 实现 `lifespan` 生命周期管理 | 高 |
| P4-1c | 初始化所有服务依赖 | 中 |
| P4-1d | 实现优雅关闭 | 低 |

**Lifespan 流程**：

```python
@mcp.lifespan
async def lifespan():
    # 1. 加载配置
    settings = Settings()
    
    # 2. 初始化基础设施
    db_pool = DBPoolManager()
    await db_pool.initialize(settings.databases)
    llm_client = LLMClient(settings.llm)
    rate_limiter = RateLimiter(settings.rate_limit)
    
    # 3. 初始化服务
    schema_service = SchemaService(db_pool, settings.cache)
    query_service = QueryService(...)
    
    # 4. 预加载 Schema
    for db_config in settings.databases:
        await schema_service.load_all(...)
    
    yield  # 服务运行
    
    # 5. 清理
    await db_pool.close_all()
```

#### 4.2 Tools 实现

| 任务ID | 任务描述 | 参数 | PRD需求 |
|--------|----------|------|---------|
| P4-2a | 实现 `query` 工具 | query, database, schema, return_type, max_rows | F-011~F-017 |
| P4-2b | 实现 `list_databases` 工具 | - | - |
| P4-2c | 实现 `list_schemas` 工具 | database | - |
| P4-2d | 实现 `list_tables` 工具 | database, schema | - |
| P4-2e | 实现 `describe_table` 工具 | database, schema, table | - |
| P4-2f | 实现 `refresh_schema` 工具 | database (可选) | F-009 |
| P4-2g | 编写 Tools 集成测试 | - | - |

#### 4.3 Resources 实现

| 任务ID | 任务描述 | URI 模式 |
|--------|----------|----------|
| P4-3a | 实现 `schema://databases` | 列出所有数据库 |
| P4-3b | 实现 `schema://{database}/schemas` | 列出 Schema |
| P4-3c | 实现 `schema://{database}/{schema}/tables` | 列出表 |
| P4-3d | 实现 `schema://{database}/{schema}/{table}` | 表详情 |

#### 4.4 入口点

| 任务ID | 任务描述 |
|--------|----------|
| P4-4a | 实现 `__main__.py` 入口 |
| P4-4b | 验证 `python -m pg_mcp` 正常启动 |

#### Phase 4 验收标准

- [ ] MCP 服务器可通过 stdio 启动
- [ ] 所有 Tools 可被 MCP 客户端调用
- [ ] 所有 Resources 可被 MCP 客户端读取
- [ ] 生命周期管理正确（启动/关闭）
- [ ] 可在 Claude Desktop 中配置并使用

---

### Phase 5: 限流/熔断/监控 (1天)

#### 5.1 限流器

| 任务ID | 任务描述 | 复杂度 | PRD需求 |
|--------|----------|--------|---------|
| P5-1a | 实现 `RateLimiter` 类 | 中 | NF-017 |
| P5-1b | 实现 LLM 限流 (`acquire_llm`) | 低 | NF-017 |
| P5-1c | 实现 DB 限流 (`acquire_db`) | 低 | NF-017 |
| P5-1d | 编写限流器测试 | 中 | - |

#### 5.2 熔断器

| 任务ID | 任务描述 | 复杂度 | PRD需求 |
|--------|----------|--------|---------|
| P5-2a | 实现 `CircuitBreaker` 数据类 | 中 | NF-017 |
| P5-2b | 实现状态转换 (CLOSED → OPEN → HALF_OPEN) | 中 | NF-017 |
| P5-2c | 实现成功/失败记录 | 低 | NF-017 |
| P5-2d | 集成到 RateLimiter | 低 | NF-017 |
| P5-2e | 编写熔断器测试 | 中 | - |

**状态机**：

```
         失败次数 >= 阈值
CLOSED ─────────────────────> OPEN
   ↑                            │
   │ 成功                       │ 超时后
   │                            ▼
   └──────────────────────── HALF_OPEN
              成功
```

#### 5.3 健康检查与指标

| 任务ID | 任务描述 | 复杂度 | PRD需求 |
|--------|----------|--------|---------|
| P5-3a | 添加 structlog 配置 | 低 | NF-014 |
| P5-3b | 记录关键操作日志（查询、SQL、结果摘要） | 中 | NF-014 |
| P5-3c | 实现健康探针（DB连接、LLM可用性、缓存状态） | 中 | NF-013 |
| P5-3d | 实现核心指标收集（查询耗时P50/P95、LLM成功率、缓存命中率、截断比例） | 高 | NF-013 |
| P5-3e | 实现指标暴露接口（stdout/structlog，可扩展Prometheus） | 中 | NF-013 |

#### 5.4 Token计量与成本控制

| 任务ID | 任务描述 | 复杂度 | PRD需求 |
|--------|----------|--------|---------|
| P5-4a | 实现LLM调用token计量（解析响应中的usage字段） | 中 | NF-018 |
| P5-4b | 实现累计token/费用统计 | 低 | NF-018 |
| P5-4c | 实现阈值告警（日志输出或回调） | 中 | NF-018 |
| P5-4d | 实现超阈值降级策略（跳过验证/仅返回SQL） | 中 | NF-019 |

#### 5.5 日志脱敏

| 任务ID | 任务描述 | 复杂度 | PRD需求 |
|--------|----------|--------|---------|
| P5-5a | 实现日志脱敏过滤器（禁止记录敏感列名/样本值） | 中 | NF-008 |
| P5-5b | 实现LLM请求/响应脱敏后记录 | 中 | NF-008 |
| P5-5c | SQL执行错误时仅打印摘要，不泄露完整数据 | 低 | NF-008 |

#### Phase 5 验收标准

- [ ] 超过限流阈值时请求被拒绝
- [ ] 连续失败触发熔断
- [ ] 熔断超时后自动恢复
- [ ] 结构化日志正确输出
- [ ] 熔断状态可查询
- [ ] 健康探针可被外部探测（返回DB/LLM/缓存状态）
- [ ] 核心指标可通过日志或接口获取
- [ ] Token计量正确累加
- [ ] 达到token阈值时触发降级并告警
- [ ] 敏感列名、行样本不出现在日志中
- [ ] LLM请求体中敏感数据已脱敏

---

### Phase 6: 集成测试与文档 (1天)

#### 6.1 端到端测试

| 任务ID | 任务描述 | 测试场景 |
|--------|----------|----------|
| P6-1a | 简单查询测试 | "查询所有活跃用户" |
| P6-1b | 复杂聚合查询测试 | "统计每个部门的员工数量" |
| P6-1c | 安全拦截测试 | "删除所有过期订单" |
| P6-1d | 分页测试 | 大结果集分页返回，验证page/page_size参数 |
| P6-1e | 多数据库测试 | 指定不同数据库查询 |
| P6-1f | 硬上限截断测试 | 结果超过hard_max_rows时正确截断并标记truncated=true |
| P6-1g | max_rows参数测试 | 验证max_rows与hard_max_rows协同，取较小值 |

#### 6.2 安全测试

| 任务ID | 任务描述 | 攻击向量 |
|--------|----------|----------|
| P6-2a | SQL 注入测试 | 恶意输入尝试绕过校验 |
| P6-2b | 权限提升测试 | 尝试执行 DDL/DML |
| P6-2c | 敏感数据泄露测试 | 验证敏感列不发送给 LLM |

#### 6.3 文档

| 任务ID | 任务描述 | 产出物 |
|--------|----------|--------|
| P6-3a | 更新 README.md | 完整使用说明 |
| P6-3b | 编写配置参考文档 | 所有配置项说明 |
| P6-3c | 编写故障排除指南 | 常见问题与解决方案 |

#### Phase 6 验收标准

- [ ] 端到端测试覆盖主要使用场景
- [ ] 分页/硬上限行为符合预期（max_rows=200默认，hard_max_rows=1000上限）
- [ ] 超过硬上限时truncated=true且行数不超过限制
- [ ] 安全测试无漏洞
- [ ] 文档完整可用
- [ ] 可在真实环境部署

---

## 4. 依赖关系图

```
Phase 0 ─────┐
             │
             ▼
Phase 1 ─────┬───────────────────────────────────┐
             │                                   │
             ▼                                   ▼
Phase 2 ────────────────┐               (LLMClient ready)
             │          │                        │
             ▼          ▼                        │
Phase 3 ←───────────────────────────────────────┘
             │
             ▼
Phase 4 ─────┐
             │
             ▼
Phase 5 ─────┐
             │
             ▼
Phase 6
```

**关键路径**：P0 → P1 → P2 → P3 → P4 → P6

**可并行**：
- P2 (安全层) 与 P1-4 (LLM客户端) 可并行
- P5 (限流/熔断) 可在 P4 完成后补充

---

## 5. 里程碑与交付物

| 里程碑 | 目标日期 | 交付物 | 验收标准 |
|--------|----------|--------|----------|
| M0 | Day 1 | 项目骨架 | 开发环境可用 |
| M1 | Day 2 | 基础设施层 | 可连接 DB 和 LLM |
| M2 | Day 3 | 安全层 | SQL 校验通过测试 |
| M3 | Day 5 | 服务层 | 端到端查询可用 |
| M4 | Day 6 | MCP 集成 | Claude Desktop 可调用 |
| M5 | Day 7 | 限流/熔断 | 生产级可靠性 |
| M6 | Day 8 | 完整交付 | 文档与测试完备 |

---

## 6. 风险与应对

| 风险 | 概率 | 影响 | 应对策略 |
|------|------|------|----------|
| SQLGlot 不支持某些 PG 语法 | 中 | 中 | 保守校验：解析失败则拒绝 |
| DeepSeek API 响应不稳定 | 中 | 高 | 重试机制 + 熔断降级 |
| Schema 加载大库超时 | 低 | 中 | 分批加载 + 磁盘缓存 |
| FastMCP API 变更 | 低 | 高 | 锁定版本，关注更新日志 |
| 多并发下连接池耗尽 | 低 | 高 | 合理配置池大小 + 限流 |

---

## 7. 测试策略

### 7.1 单元测试覆盖

| 模块 | 最低覆盖率 | 关键测试点 |
|------|------------|------------|
| sql_validator.py | 90% | 所有禁止语句类型、CTE检查、文字常量检查 |
| function_guard.py | 85% | 白名单校验、黑名单拦截 |
| sanitizer.py | 85% | 敏感列过滤、采样限制、日志脱敏 |
| rate_limiter.py | 85% | 限流阈值、熔断状态转换 |
| llm_client.py | 80% | Token计量、降级处理 |
| schema_service.py | 80% | 缓存TTL、刷新状态、失败回退 |
| models/*.py | 80% | 序列化/反序列化 |

### 7.2 集成测试环境

- **PostgreSQL**：使用 testcontainers 启动临时实例
- **LLM**：使用 Mock 或真实 API（需配置）
- **MCP**：使用 FastMCP 测试工具

### 7.3 测试命令

```bash
# 单元测试
pytest tests/unit -v --cov=pg_mcp --cov-report=term-missing

# 集成测试（需要 PostgreSQL）
pytest tests/integration -v --tb=short

# 安全测试
pytest tests/security -v

# 全量测试
pytest --tb=short
```

---

## 8. 开发规范

### 8.1 代码风格

- **格式化**：ruff format
- **Lint**：ruff check
- **类型检查**：mypy --strict
- **Docstring**：Google 风格

### 8.2 提交规范

```
<type>(<scope>): <subject>

类型：feat, fix, docs, style, refactor, test, chore
范围：config, models, security, services, mcp, infra
```

### 8.3 分支策略

- `main`：稳定版本
- `dev`：开发分支
- `feature/<name>`：功能分支

---

## 修订历史

| 版本 | 日期 | 修改内容 | 作者 |
|------|------|----------|------|
| v0.1 | 2026-01-11 | 初稿 | AI Assistant |
| v0.2 | 2026-01-11 | 根据Review补充：定时刷新调度、SQL执行安全、健康检查与指标、Token计量、日志脱敏、分页/硬上限测试 | AI Assistant |

