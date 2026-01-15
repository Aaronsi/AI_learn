# PostgreSQL MCP Server 产品需求文档 (PRD)

## 文档信息

| 项目 | 内容 |
|------|------|
| 文档版本 | v0.1 |
| 创建日期 | 2026-01-11 |
| 状态 | 草稿 - 待评审 |
| 作者 | AI Assistant |

---

## 1. 项目概述

### 1.1 项目背景

用户在日常工作中经常需要从 PostgreSQL 数据库中查询数据，但编写 SQL 语句对于非技术人员或不熟悉特定数据库 schema 的用户来说是一个障碍。本项目旨在创建一个 MCP (Model Context Protocol) 服务器，允许用户通过自然语言描述来获取所需的数据查询结果或 SQL 语句。

### 1.2 项目目标

构建一个基于 Python 的 PostgreSQL MCP 服务器，实现以下核心能力：

1. **自然语言转 SQL**：接收用户的自然语言查询描述，自动生成对应的 SQL 语句
2. **智能 Schema 感知**：自动发现和缓存数据库 schema 信息，为 SQL 生成提供上下文
3. **安全查询执行**：确保只执行安全的查询语句，防止数据修改或破坏
4. **结果验证**：验证生成的 SQL 和查询结果是否符合用户意图
5. **灵活输出**：支持返回生成的 SQL 语句或直接返回查询结果

### 1.3 目标用户

- 数据分析师：需要快速查询数据但不熟悉复杂 SQL 语法
- 产品经理：需要获取业务数据但不具备深厚的数据库技能
- 开发人员：希望加速 SQL 编写过程
- 业务人员：需要临时获取数据报表

---

## 2. 功能需求

### 2.1 核心功能

#### 2.1.1 数据库连接与 Schema 缓存

**描述**：MCP 服务器在启动时自动连接到配置的 PostgreSQL 数据库，读取并缓存完整的 schema 信息。

**详细需求**：

| 需求ID | 需求描述 | 优先级 |
|--------|----------|--------|
| F-001 | 支持配置多个 PostgreSQL 数据库连接 | P0 |
| F-002 | 启动时自动连接所有配置的数据库 | P0 |
| F-003 | 读取并缓存每个数据库的所有 schema | P0 |
| F-003a | 支持分批/流式加载 schema，避免大库阻塞启动 | P0 |
| F-003b | 缓存可落盘，冷启动优先加载本地缓存再异步刷新 | P1 |
| F-004 | 缓存每个 schema 下的所有 tables 信息（表名、列名、列类型、约束、注释） | P0 |
| F-005 | 缓存每个 schema 下的所有 views 信息（视图名、列信息、定义） | P0 |
| F-006 | 缓存每个 schema 下的所有自定义 types（枚举类型、复合类型等） | P1 |
| F-007 | 缓存每个 schema 下的所有 indexes 信息（索引名、关联表、索引列） | P1 |
| F-008 | 缓存表之间的外键关系 | P0 |
| F-009 | 支持手动触发 schema 刷新 | P1 |
| F-010 | 支持定时自动刷新 schema 缓存 | P2 |
| F-010a | 刷新需并发限流、失败重试、回退旧缓存，暴露刷新状态 | P1 |

**缓存的 Schema 信息结构**：

```
Database
├── Schema (e.g., public, sales, hr)
│   ├── Tables
│   │   ├── Table Name
│   │   ├── Columns (name, type, nullable, default, comment)
│   │   ├── Primary Key
│   │   ├── Foreign Keys
│   │   ├── Unique Constraints
│   │   └── Table Comment
│   ├── Views
│   │   ├── View Name
│   │   ├── Columns
│   │   └── View Definition (可选)
│   ├── Types
│   │   ├── Enum Types (name, values)
│   │   └── Composite Types (name, attributes)
│   └── Indexes
│       ├── Index Name
│       ├── Table
│       ├── Columns
│       └── Index Type (btree, hash, gin, etc.)
```

#### 2.1.2 自然语言查询处理

**描述**：接收用户的自然语言查询描述，调用 DeepSeek 大模型生成对应的 SQL 语句。

**详细需求**：

| 需求ID | 需求描述 | 优先级 |
|--------|----------|--------|
| F-011 | 接收用户自然语言查询描述 | P0 |
| F-012 | 支持用户指定目标数据库（如果配置了多个） | P0 |
| F-013 | 支持用户指定目标 schema（如果有多个） | P1 |
| F-014 | 将 schema 信息作为上下文提供给 DeepSeek 模型 | P0 |
| F-015 | 调用 DeepSeek-V3.2 模型生成 SQL | P0 |
| F-016 | 支持多轮对话优化查询（用户可以基于前次结果进行修正） | P2 |
| F-017 | 支持用户指定返回类型（SQL 语句 或 查询结果） | P0 |
| F-017a | 支持分页参数（page/page_size），并与 max_rows/硬上限协同 | P1 |

**输入参数**：

| 参数名 | 类型 | 必填 | 描述 |
|--------|------|------|------|
| query | string | 是 | 自然语言查询描述 |
| database | string | 否 | 目标数据库名称（默认使用第一个配置的数据库） |
| schema | string | 否 | 目标 schema（默认 public） |
| return_type | enum | 否 | 返回类型：`sql` 或 `result`（默认 `result`） |
| max_rows | integer | 否 | 最大返回行数（默认 200，且不高于安全配置上限） |

#### 2.1.3 SQL 安全校验

**描述**：对生成的 SQL 进行安全校验，确保只允许执行查询语句，防止数据修改或破坏。

**详细需求**：

| 需求ID | 需求描述 | 优先级 |
|--------|----------|--------|
| F-018 | 解析生成的 SQL 语句，识别语句类型 | P0 |
| F-018a | 使用 AST 级解析确保全链路只读（含 CTE/子查询） | P0 |
| F-018b | 拒绝 WITH 中的 DML/DDL、`SELECT ... INTO`、`COPY TO/FROM`、`CALL`/`DO`/`EXECUTE` | P0 |
| F-019 | 只允许 SELECT 语句执行 | P0 |
| F-020 | 拒绝 INSERT、UPDATE、DELETE 语句 | P0 |
| F-021 | 拒绝 DROP、TRUNCATE、ALTER 等 DDL 语句 | P0 |
| F-022 | 拒绝 GRANT、REVOKE 等权限管理语句 | P0 |
| F-023 | 检测并拒绝包含子查询中的危险操作 | P0 |
| F-024 | 拒绝调用可能产生副作用的函数 | P1 |
| F-024a | 仅允许函数/扩展白名单，默认拒绝未列出的可变函数 | P0 |
| F-025 | 支持配置白名单函数列表 | P2 |
| F-026 | 对 SQL 注入攻击进行防护 | P0 |

**禁止的 SQL 类型**：

- DML (除 SELECT)：INSERT, UPDATE, DELETE, MERGE，以及 WITH/CTE 中的 DML
- DDL：CREATE, ALTER, DROP, TRUNCATE, RENAME，`SELECT ... INTO`
- DCL：GRANT, REVOKE
- TCL：COMMIT, ROLLBACK, SAVEPOINT
- 其他：COPY TO/FROM，EXECUTE，CALL/DO（存储过程/匿名块），创建临时表、物化视图、索引
- 副作用函数与未在白名单中的扩展函数
- 禁止参数内插，必须使用参数化绑定

#### 2.1.4 SQL 执行与结果获取

**描述**：执行经过安全校验的 SQL 语句，获取查询结果。

**详细需求**：

| 需求ID | 需求描述 | 优先级 |
|--------|----------|--------|
| F-027 | 使用只读连接或只读事务执行查询 | P0 |
| F-027a | 每次查询前强制 `SET TRANSACTION READ ONLY`，必要时降权 `SET ROLE` 为最小权限 | P0 |
| F-028 | 支持设置查询超时时间 | P0 |
| F-029 | 支持限制最大返回行数 | P0 |
| F-030 | 捕获并处理 SQL 执行错误 | P0 |
| F-031 | SQL 执行失败时，尝试让 DeepSeek 修正 SQL | P1 |
| F-032 | 返回结构化的查询结果（包含列名和数据） | P0 |
| F-033 | 支持多种结果格式（JSON, 表格等） | P2 |

#### 2.1.5 结果验证与质量保证

**描述**：验证生成的 SQL 和查询结果是否符合用户的原始意图。

**详细需求**：

| 需求ID | 需求描述 | 优先级 |
|--------|----------|--------|
| F-034 | 将用户查询、生成的 SQL、部分结果发送给 DeepSeek 进行验证 | P1 |
| F-034a | 发送给 DeepSeek 的结果需脱敏+采样：≤20行、≤10列，过滤敏感列（可配置） | P0 |
| F-034b | 优先发送摘要/聚合（行数、列名、统计值）而非全量样本 | P1 |
| F-035 | DeepSeek 评估结果是否满足用户需求 | P1 |
| F-036 | 如果验证失败，尝试重新生成 SQL（最多 N 次） | P1 |
| F-037 | 返回验证结果说明（解释为什么认为结果是正确的） | P2 |
| F-038 | 对空结果进行特殊处理（区分"没有数据"和"查询错误"） | P1 |

**验证流程**：

```
用户输入 → 生成 SQL → 执行 SQL → 获取结果样本 → 
→ DeepSeek 验证 → [通过] → 返回结果
                 → [失败] → 重新生成 SQL (循环)
```

### 2.2 MCP 协议接口

#### 2.2.1 暴露的 Tools

| Tool 名称 | 描述 | 参数 |
|-----------|------|------|
| `query` | 执行自然语言查询 | query, database, schema, return_type, max_rows |
| `list_databases` | 列出所有可用数据库 | - |
| `list_schemas` | 列出指定数据库的所有 schema | database |
| `list_tables` | 列出指定 schema 的所有表 | database, schema |
| `describe_table` | 获取表的详细结构 | database, schema, table |
| `refresh_schema` | 刷新 schema 缓存 | database (可选) |

#### 2.2.2 暴露的 Resources

| Resource 名称 | 描述 |
|---------------|------|
| `schema://databases` | 所有数据库列表 |
| `schema://{database}/schemas` | 指定数据库的 schema 列表 |
| `schema://{database}/{schema}/tables` | 表列表 |
| `schema://{database}/{schema}/{table}` | 表结构详情 |

---

## 3. 非功能需求

### 3.1 性能需求

| 需求ID | 需求描述 | 指标 |
|--------|----------|------|
| NF-001 | Schema 缓存加载时间 | 单个数据库 < 10秒 |
| NF-002 | 自然语言转 SQL 响应时间 | < 5秒（不含 DeepSeek API 延迟） |
| NF-003 | SQL 执行超时时间 | 可配置，默认 30秒 |
| NF-004 | 并发查询支持 | 支持至少 10 个并发查询 |

> 说明：NF-001 依赖 F-003a/F-003b 的分批加载与缓存落盘；冷启动可先提供部分 schema，后台继续补全。

### 3.2 安全需求

| 需求ID | 需求描述 | 优先级 |
|--------|----------|--------|
| NF-005 | 数据库连接凭据安全存储（支持环境变量、密钥管理） | P0 |
| NF-006 | DeepSeek API Key 安全存储 | P0 |
| NF-007 | 所有数据库操作使用只读权限账户 | P0 |
| NF-008 | 敏感数据不应出现在日志中 | P0 |
| NF-009 | 支持 SSL/TLS 数据库连接 | P1 |

### 3.3 可靠性需求

| 需求ID | 需求描述 | 优先级 |
|--------|----------|--------|
| NF-010 | 数据库连接断开后自动重连 | P0 |
| NF-011 | DeepSeek API 调用失败后重试机制 | P0 |
| NF-012 | 优雅处理所有错误，返回有意义的错误信息 | P0 |
| NF-013 | 服务健康检查端点 | P1 |

### 3.4 可维护性需求

| 需求ID | 需求描述 | 优先级 |
|--------|----------|--------|
| NF-014 | 完整的日志记录（查询、SQL、结果摘要） | P0 |
| NF-015 | 配置文件支持（YAML/JSON） | P0 |
| NF-016 | 支持热重载配置 | P2 |

### 3.5 限流与成本控制

| 需求ID | 需求描述 | 优先级 |
|--------|----------|--------|
| NF-017 | DeepSeek 与数据库访问需有并发/速率限流与熔断 | P0 |
| NF-018 | 记录并监控 token/费用，超过阈值报警并可降级为本地校验 | P1 |
| NF-019 | DeepSeek 调用失败或熔断时的降级策略（跳过验证或仅返回 SQL） | P1 |

---

## 4. 技术约束

### 4.1 技术栈要求

| 组件 | 要求 |
|------|------|
| 编程语言 | Python 3.10+ |
| 数据库 | PostgreSQL 12+ |
| LLM | DeepSeek-V3.2 |
| MCP SDK | 使用官方 Python MCP SDK |

### 4.2 外部依赖

| 依赖 | 用途 |
|------|------|
| DeepSeek API | 自然语言理解和 SQL 生成 |
| PostgreSQL | 目标数据库 |

---

## 5. 配置项

### 5.1 数据库配置

```yaml
databases:
  - name: "main_db"
    host: "localhost"
    port: 5432
    database: "mydb"
    username: "${DB_USER}"
    password: "${DB_PASSWORD}"
    ssl_mode: "prefer"
    schemas:
      - "public"
      - "sales"
    # 可选：排除某些表
    exclude_tables:
      - "internal_logs"
      - "audit_*"
```

### 5.2 DeepSeek 配置

```yaml
deepseek:
  api_key: "${DEEPSEEK_API_KEY}"
  model: "deepseek-v3.2"
  temperature: 0.1
  max_tokens: 2048
  timeout: 30
```

### 5.3 安全配置

```yaml
security:
  max_rows: 200           # 默认最大返回行数，与输入参数一致
  hard_max_rows: 1000     # 服务器硬上限，超过即截断并标记 truncated=true
  query_timeout: 30
  allowed_functions: []  # 白名单函数
  enable_result_validation: true
  max_retry_attempts: 3
```

---

## 6. 错误处理

### 6.1 错误类型

| 错误码 | 错误类型 | 描述 |
|--------|----------|------|
| E001 | DatabaseConnectionError | 无法连接到数据库 |
| E002 | SchemaLoadError | 无法加载 schema 信息 |
| E003 | LLMError | DeepSeek API 调用失败 |
| E004 | SQLGenerationError | 无法生成有效 SQL |
| E005 | SecurityViolation | SQL 包含不允许的操作 |
| E006 | SQLExecutionError | SQL 执行失败 |
| E007 | ValidationError | 结果验证失败 |
| E008 | TimeoutError | 操作超时 |
| E009 | ConfigurationError | 配置错误 |

### 6.2 错误响应格式

```json
{
  "success": false,
  "error": {
    "code": "E005",
    "type": "SecurityViolation",
    "message": "生成的 SQL 包含不允许的 DELETE 操作",
    "details": {
      "sql": "DELETE FROM users WHERE id = 1",
      "violation": "DELETE statement not allowed"
    }
  }
}
```

### 6.3 MCP 工具错误映射

- 所有 MCP tool 响应需携带 `error.code` 与 `retryable`（布尔）字段，便于客户端重试。
- 多步骤或多数据库操作需指明 `partial=true` 及已完成/失败的子任务列表。
- 限流/熔断返回应使用专门错误码（如 `E010:RateLimited`），并附带 `retry_after_ms`。
- 对可修复错误（如 SQLGenerationError）可提供 `suggestion` 字段指示下一步行动。

---

## 7. 成功响应格式

### 7.1 返回 SQL（return_type = "sql"）

```json
{
  "success": true,
  "data": {
    "sql": "SELECT u.name, COUNT(o.id) as order_count FROM users u LEFT JOIN orders o ON u.id = o.user_id GROUP BY u.id, u.name ORDER BY order_count DESC LIMIT 10",
    "explanation": "该查询统计每个用户的订单数量，并按订单数降序排列，返回前10名用户"
  }
}
```

### 7.2 返回查询结果（return_type = "result"）

```json
{
  "success": true,
  "data": {
    "sql": "SELECT ...",
    "columns": ["name", "order_count"],
    "rows": [
      {"name": "Alice", "order_count": 150},
      {"name": "Bob", "order_count": 120}
    ],
    "row_count": 2,
    "truncated": false,
    "execution_time_ms": 45,
    "explanation": "查询返回了订单数量最多的10名用户"
  }
}
```

---

## 8. 使用场景示例

### 场景 1：简单查询

**用户输入**：
> "查询所有状态为活跃的用户"

**系统处理**：
1. 从缓存获取 users 表结构
2. 调用 DeepSeek 生成 SQL：`SELECT * FROM users WHERE status = 'active' LIMIT 100`
3. 安全校验通过
4. 执行查询并返回结果

### 场景 2：复杂聚合查询

**用户输入**：
> "统计每个部门的员工数量和平均工资，按员工数量从高到低排序"

**系统处理**：
1. 从缓存获取 employees 和 departments 表结构及外键关系
2. 调用 DeepSeek 生成 SQL
3. 安全校验通过
4. 执行查询
5. 调用 DeepSeek 验证结果是否符合需求
6. 返回验证后的结果

### 场景 3：安全拦截

**用户输入**：
> "删除所有过期的订单"

**系统处理**：
1. 调用 DeepSeek 生成 SQL：`DELETE FROM orders WHERE expire_date < NOW()`
2. 安全校验检测到 DELETE 语句
3. 返回错误：不允许执行删除操作

---

## 9. 待确认问题

以下问题需要在评审时确认：

1. **多数据库支持**：是否需要支持同时查询多个数据库？还是每次查询只针对一个数据库？

2. **Schema 缓存策略**：
   - 缓存落盘的存储位置、保留策略及加密要求？
   - 自动/手动刷新频率、并发上限、失败回退策略？

3. **DeepSeek 调用策略**：
   - 结果验证是否默认启用？哪些场景可跳过？
   - SQL 生成/验证失败后的重试与熔断阈值？

4. **分页与上限**：分页参数上限（page_size）、硬上限 1000 是否满足？是否需要可配置？

5. **敏感数据处理**：
   - 默认列黑名单来源？是否需要列级访问控制/角色映射？
   - 脱敏规则（掩码/置空）是否需要按列类型定制？

6. **日志与审计**：
   - 是否需要记录所有查询历史？保留与脱敏策略？
   - 是否需要审计 DeepSeek 请求体（在脱敏前后分别记录？）

7. **费用与预算**：
   - token/费用阈值与报警渠道？
   - 达到阈值后的默认降级策略（停用验证/仅返回 SQL/拒绝请求）？

---

## 10. 验收标准与测试范围

- 功能：覆盖 `query/list_*`/`describe_table/refresh_schema` 工具的主流程；分页与 max_rows 截断行为；多数据库/多 schema 选择。
- 安全：AST 只读校验（含 CTE）、拒绝副作用函数、只读事务、参数化执行、敏感列脱敏与 DeepSeek 采样上限（≤20行、≤10列、列黑名单）。
- 性能：冷启动 schema 加载 <10s（使用分批/缓存落盘），单查询响应（不含 LLM）<5s，默认 max_rows=200、硬上限=1000。
- 可靠性：DeepSeek 调用重试与熔断后降级策略；数据库重连；错误码与 retryable 标记可用。
- 兼容性：PostgreSQL 12+，在开启/关闭 SSL、存在常见扩展（但未在白名单则拒绝）情况下的行为。
- 费用与监控：token/费用计量、阈值报警流程验证。

## 11. 附录

### 11.1 术语表

| 术语 | 定义 |
|------|------|
| MCP | Model Context Protocol，一种让 AI 模型与外部工具交互的协议 |
| Schema | PostgreSQL 中的命名空间，用于组织数据库对象 |
| DDL | Data Definition Language，数据定义语言 |
| DML | Data Manipulation Language，数据操作语言 |
| DCL | Data Control Language，数据控制语言 |

### 11.2 参考资料

- [MCP 协议规范](https://modelcontextprotocol.io/)
- [PostgreSQL 系统目录](https://www.postgresql.org/docs/current/catalogs.html)
- [DeepSeek API 文档](https://platform.deepseek.com/docs)

---

## 修订历史

| 版本 | 日期 | 修改内容 | 作者 |
|------|------|----------|------|
| v0.1 | 2026-01-11 | 初稿 | AI Assistant |

