# pg-mcp 项目总结

## 项目概述

PostgreSQL MCP Server - 自然语言转 SQL 查询引擎，基于 FastMCP、asyncpg、SQLGlot、Pydantic 和 OpenAI（DeepSeek 兼容）API 构建。

## 实现状态

### ✅ Phase 0: 项目初始化
- 项目目录结构
- pyproject.toml 配置
- 开发工具配置（ruff, mypy, pytest）
- 示例配置文件
- README.md

### ✅ Phase 1: 基础设施层
- 配置管理（Pydantic Settings，支持 YAML + 环境变量）
- 数据模型（Schema、Query、Error）
- 数据库连接池（asyncpg，只读事务，SET ROLE 降权）
- LLM 客户端（OpenAI 兼容 API，JSON 响应）

### ✅ Phase 2: 安全层
- SQL 校验器（SQLGlot AST 分析，禁止 DML/DDL）
- 函数守卫（白名单机制）
- 数据脱敏器（敏感列过滤，采样限制）

### ✅ Phase 3: 服务层
- Schema 服务（PostgreSQL 信息模式加载，磁盘缓存，定时刷新）
- 查询服务（NL2SQL 完整流程，分页，结果验证）
- 验证服务（LLM 结果验证）

### ✅ Phase 4: MCP 协议层
- FastMCP 服务器集成
- 生命周期管理
- 6 个 Tools（query, list_databases, list_schemas, list_tables, describe_table, refresh_schema）
- 4 个 Resources（schema://...）

### ✅ Phase 5: 限流/熔断/监控
- 限流器（LLM 和 DB 分别限流）
- 熔断器（CLOSED → OPEN → HALF_OPEN）
- 指标收集（查询耗时、成功率、缓存命中率等）
- Token 计量和成本控制
- 日志脱敏

### ✅ Phase 6: 集成测试与文档
- 端到端测试（7 个测试场景）
- 安全测试（SQL 注入、权限提升、敏感数据泄露）
- 完整文档（README、配置说明、故障排除指南）

## 项目结构

```
w5/pg-mcp/
├── pg_mcp/
│   ├── __init__.py
│   ├── __main__.py              # 入口点
│   ├── server.py                 # FastMCP 服务器
│   ├── config/
│   │   ├── __init__.py
│   │   └── settings.py          # 配置管理
│   ├── models/
│   │   ├── __init__.py
│   │   ├── schema.py            # Schema 模型
│   │   ├── query.py             # Query 模型
│   │   └── errors.py            # Error 模型
│   ├── security/
│   │   ├── __init__.py
│   │   ├── sql_validator.py     # SQL 校验器
│   │   ├── function_guard.py    # 函数守卫
│   │   └── sanitizer.py         # 数据脱敏器
│   ├── infrastructure/
│   │   ├── __init__.py
│   │   ├── db_pool.py           # 数据库连接池
│   │   ├── llm_client.py        # LLM 客户端
│   │   ├── rate_limiter.py      # 限流器和熔断器
│   │   ├── metrics.py           # 指标收集
│   │   ├── token_meter.py       # Token 计量
│   │   └── log_sanitizer.py     # 日志脱敏
│   ├── services/
│   │   ├── __init__.py
│   │   ├── schema_service.py    # Schema 服务
│   │   ├── query_service.py     # 查询服务
│   │   └── validation_service.py # 验证服务
│   └── tests/
│       ├── conftest.py
│       ├── unit/                # 单元测试
│       └── integration/         # 集成测试
├── pyproject.toml               # 项目配置
├── pg_mcp.yaml.example         # 配置示例
├── README.md                    # 项目文档
├── CONFIGURATION.md            # 配置说明
├── CONFIG_REFERENCE.md         # 配置参考
├── TROUBLESHOOTING.md          # 故障排除指南
└── PHASE*.md                   # 各阶段实现报告
```

## 核心功能

### 1. 自然语言转 SQL
- 使用 DeepSeek LLM 将自然语言查询转换为 PostgreSQL SQL
- 支持复杂查询（JOIN、聚合、子查询等）
- SQL 安全校验确保只执行只读查询

### 2. Schema 自动发现
- 从 PostgreSQL 信息模式自动加载 Schema
- 磁盘缓存和内存缓存
- 定时自动刷新
- 支持多数据库、多 Schema

### 3. 安全保护
- AST 级别的 SQL 安全校验
- 禁止所有 DML/DDL 语句
- 函数白名单机制
- 敏感数据脱敏
- 只读事务和权限降权

### 4. 结果验证
- LLM 验证查询结果是否符合用户意图
- 降级处理，不阻塞主流程

### 5. 限流和熔断
- LLM 和 DB 分别限流
- 熔断器保护
- 健康检查和指标收集

## 技术栈

- **Python**: ≥3.10
- **FastMCP**: ≥2.0 - MCP 协议实现
- **asyncpg**: ≥0.29 - PostgreSQL 异步驱动
- **SQLGlot**: ≥25.0 - SQL 解析与安全校验
- **Pydantic**: ≥2.0 - 数据模型与配置
- **openai**: ≥1.0 - LLM 客户端（兼容 DeepSeek）
- **aiolimiter**: ≥1.1 - 异步限流
- **structlog**: ≥24.0 - 结构化日志

## 快速开始

### 1. 安装依赖

```bash
cd w5/pg-mcp
uv sync
```

### 2. 配置

```bash
cp pg_mcp.yaml.example pg_mcp.yaml
# 编辑 pg_mcp.yaml，配置数据库和 API Key
```

### 3. 运行

```bash
python -m pg_mcp
```

详细配置说明请查看 [CONFIGURATION.md](./CONFIGURATION.md)

## 测试

### 运行测试

```bash
# 单元测试
pytest tests/unit -v

# 集成测试
pytest tests/integration -v

# 所有测试
pytest -v

# 测试覆盖率
pytest --cov=pg_mcp --cov-report=term-missing
```

## 文档

- [README.md](./README.md) - 项目主文档
- [CONFIGURATION.md](./CONFIGURATION.md) - 配置说明
- [CONFIG_REFERENCE.md](./CONFIG_REFERENCE.md) - 配置参考
- [TROUBLESHOOTING.md](./TROUBLESHOOTING.md) - 故障排除指南

## MCP 客户端配置

### Claude Desktop

在 Claude Desktop 配置文件中添加：

```json
{
  "mcpServers": {
    "pg-mcp": {
      "command": "python",
      "args": ["-m", "pg_mcp"],
      "env": {
        "DB_USER": "your_db_user",
        "DB_PASSWORD": "your_db_password",
        "DEEPSEEK_API_KEY": "sk-your-deepseek-key"
      }
    }
  }
}
```

## 代码质量

- ✅ 所有代码通过 ruff lint 检查
- ✅ 完整的类型注解（mypy strict 模式）
- ✅ 遵循 Python 最佳实践
- ✅ 模块化设计，职责清晰
- ✅ 完整的测试覆盖

## 安全特性

1. **SQL 安全校验**：
   - AST 级别分析
   - 禁止 DML/DDL
   - 危险函数黑名单
   - CTE 安全检查

2. **数据保护**：
   - 敏感列过滤
   - 采样限制
   - 日志脱敏

3. **权限控制**：
   - 只读事务
   - SET ROLE 降权
   - 连接池隔离

## 性能特性

1. **缓存机制**：
   - 磁盘缓存
   - 内存缓存
   - TTL 过期检测
   - 后台异步刷新

2. **限流保护**：
   - LLM 限流
   - DB 限流
   - 熔断器

3. **指标监控**：
   - 查询耗时（P50/P95）
   - 成功率统计
   - 缓存命中率
   - Token 使用量

## 已知限制

1. **依赖安装**：需要运行 `uv sync` 安装依赖
2. **真实环境测试**：部分测试使用 Mock，需要真实环境验证
3. **性能测试**：需要专门的基准测试

## 后续改进建议

1. **性能优化**：
   - Schema 加载优化
   - 查询缓存
   - 连接池调优

2. **功能增强**：
   - 支持更多数据库类型
   - 查询历史记录
   - 查询性能分析

3. **监控和可观测性**：
   - Prometheus 指标导出
   - 分布式追踪
   - 告警集成

## 许可证

MIT

## 贡献

欢迎提交 Issue 和 Pull Request。

