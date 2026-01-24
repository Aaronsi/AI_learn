# pg-mcp 增加 MySQL 支持代码评审

评审范围：`./w5/pg-mcp`  
对照文档：`./specs/w5/0002-pg-mcp-design.md`、`./specs/w5/0004-pg-mcp-impl-plan.md`  
关注点：功能完整性、设计一致性、Python best practice / idiomatic Python、SOLID/DRY、代码质量、测试质量、性能

## 结论摘要
当前 MySQL 支持处于**“接口已接入但实现未闭环”**状态，核心执行与 Schema 读取路径仍依赖 `asyncpg` 的 `fetch/fetchval` 协议，导致 MySQL 实际不可用。设计文档中的多数据库能力目标尚未完整达成。代码质量总体可读性不错，但在可维护性、协议抽象与测试覆盖上仍有明显缺口。

---

## 高优先级问题（功能性/安全性）

### 1. MySQL 执行路径不可用（连接对象不具备 `fetch/fetchval`）
**影响**：MySQL 实际无法执行查询或加载 schema，违反实现计划中的“多数据库支持”。  
**原因**：`aiomysql` 连接对象并不提供 `fetch/fetchval` 方法，当前设计把 MySQL 连接当成 asyncpg 使用。  
相关代码：

```192:238:pg_mcp/infrastructure/db_pool.py
    async def acquire_readonly(
        self, db_name: str, timeout: int = 30
    ) -> AsyncIterator[DBConnection]:
        """获取只读连接并按需降权"""
        pool = self.get_pool(db_name)
        config = self._configs[db_name]

        if config.db_type == "postgresql":
            ...
        elif config.db_type == "mysql":
            async with pool.acquire(timeout=timeout) as conn:
                ...
                yield conn
```

```192:225:pg_mcp/services/query_service.py
            async with self.db_pool.acquire_readonly(
                db_name, self.settings.security.query_timeout
            ) as conn:
                ...
                rows = await conn.fetch(paginated_sql)
```

```196:218:pg_mcp/services/schema_service.py
        async with ctx as conn:
            # 获取数据库版本
            version = await conn.fetchval("SELECT version()")
            db_info.version = version
```

**建议**：
- 抽象统一的数据库访问层（例如 `DBAdapter`），为 MySQL 实现 `fetch/fetchval` 适配（通过 cursor + DictCursor），避免直接暴露连接对象。
- 或把 `QueryService/SchemaService` 改为在 MySQL 路径使用 cursor API。

### 2. MySQL 只读事务策略无效
**影响**：读写隔离与安全策略未生效（设计要求只读执行）。  
**原因**：MySQL 中 `SET SESSION TRANSACTION READ ONLY` 仅影响**后续事务**，但这里先 `begin()` 再设置只读，因此不会生效。  
相关代码：

```212:223:pg_mcp/infrastructure/db_pool.py
        elif config.db_type == "mysql":
            async with pool.acquire(timeout=timeout) as conn:
                # MySQL 设置只读模式（在事务中）
                await conn.begin()
                try:
                    await conn.execute("SET SESSION TRANSACTION READ ONLY")
                    ...
                    yield conn
```

**建议**：改用 `START TRANSACTION READ ONLY` 或 `SET TRANSACTION READ ONLY` 并保证在事务开始前设置。

### 3. LLM Prompt 仍固定为 PostgreSQL，破坏 MySQL 生成质量
**影响**：自然语言转 SQL 仍按 PostgreSQL 语法生成，MySQL 会出错。  
**原因**：LLM Prompt 写死“PostgreSQL SQL 专家”。  
相关代码：

```19:38:pg_mcp/infrastructure/llm_client.py
    # NL2SQL系统提示词
    NL2SQL_SYSTEM_PROMPT = """你是一个PostgreSQL SQL专家。根据用户的自然语言描述和提供的数据库schema信息，生成精确的SQL查询语句。
...
2. 使用标准PostgreSQL语法
```

**建议**：根据 `db_type` 动态切换 prompt 或提示方言。

### 4. 函数白名单对 MySQL 不友好，导致合法 SQL 被拒绝
**影响**：MySQL 的常用函数如 `group_concat` 会被 FunctionGuard 拒绝，即使 SQLValidator 已允许。  
**原因**：`FunctionGuard.DEFAULT_SAFE_FUNCS` 包含大量 PostgreSQL 函数，未区分方言。  
相关代码：

```6:72:pg_mcp/security/function_guard.py
    DEFAULT_SAFE_FUNCS = {
        "count",
        ...
        "array_agg",
        "string_agg",
        ...
        "json_agg",
        "jsonb_agg",
        ...
    }
```

**建议**：按方言区分安全函数集合，或让 `FunctionGuard` 接收 `db_type`。

---

## 中优先级问题（设计一致性/可维护性）

### 5. DBPool 抽象未真正 SOLID/DRY
**影响**：MySQL 和 PostgreSQL 逻辑混杂在同一类中，增加维护成本。  
**原因**：DBPoolManager 同时承担多数据库协议差异与连接生命周期控制。  
**建议**：引入适配器或策略模式，把每种数据库的执行逻辑隔离。

### 6. SchemaService 仍是 PG 假设主导
**影响**：MySQL 分支散落多处，逻辑复杂且易错。  
**原因**：SchemaService 使用 PostgreSQL 查询作为默认，MySQL 分支在多个方法内条件判断。  
**建议**：将 SchemaLoader 抽象为每个数据库单独实现。

### 7. MySQL 查询超时依赖 `max_execution_time`
**影响**：并非所有 MySQL 版本都支持该变量，存在兼容性风险。  
**建议**：允许配置开关，或在执行失败时降级处理。

---

## 低优先级问题（风格/细节）

### 8. 命名冲突与可读性
**影响**：`MySQLPool` 既是类型别名又是类名，可读性差。  
**建议**：避免与导入类型同名，例如 `MySQLPoolWrapper`。

### 9. 未使用的 import
`db_pool.py` 中存在 `ABC`、`abstractmethod` 未使用，违背简洁原则。

---

## 测试质量
- 当前测试未覆盖 MySQL 相关路径（连接池创建、schema 加载、执行、SQL 验证）。  
- 建议补充 MySQL integration tests（可使用 docker/mysql），并模拟 DictCursor 行为。

---

## 性能评估
功能框架本身性能合理，但 MySQL 适配不正确导致实际不可用，性能评价暂无意义。  
Schema 读取的多次查询可能在 MySQL 上产生额外开销，建议后续加入批量查询或缓存优化。

---

## 结论
MySQL 功能尚未达到设计文档和实现计划中“多数据库支持”的目标。  
主要问题集中在数据库适配层与 SQL 生成的方言意识，属于**功能性阻断级别**。  
建议优先补齐数据库执行/Schema读取适配层，之后再补充 MySQL 相关测试和文档。


