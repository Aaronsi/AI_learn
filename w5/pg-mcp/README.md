# PostgreSQL MCP Server

PostgreSQL MCP Server - 自然语言转 SQL 查询引擎

## 功能特性

- **自然语言转 SQL**：使用 DeepSeek LLM 将自然语言查询转换为 PostgreSQL SQL
- **Schema 自动发现**：自动加载和缓存数据库 schema 信息
- **SQL 安全校验**：AST 级别的 SQL 安全检查，确保只执行只读查询
- **结果验证**：LLM 验证查询结果是否符合用户意图
- **敏感数据脱敏**：自动过滤敏感列，保护数据隐私

## 快速开始

### 安装

```bash
cd w5/pg/mcp
uv sync
```

### 配置

#### 1. 创建配置文件

复制示例配置文件：
```bash
cp pg_mcp.yaml.example pg_mcp.yaml
```

#### 2. 配置 PostgreSQL 和 DeepSeek API

编辑 `pg_mcp.yaml`，配置数据库连接和 LLM API Key：

**方式一：直接在 YAML 中配置（不推荐用于生产环境）**
```yaml
databases:
  - name: "main"
    host: "localhost"
    port: 5432
    database: "myapp"
    username: "your_db_user"
    password: "your_db_password"

llm:
  api_key: "sk-your-deepseek-api-key"
  base_url: "https://api.deepseek.com/v1"
  model: "deepseek-chat"
```

**方式二：使用环境变量（推荐）**
```yaml
databases:
  - name: "main"
    host: "localhost"
    port: 5432
    database: "myapp"
    username: "${DB_USER}"
    password: "${DB_PASSWORD}"

llm:
  api_key: "${DEEPSEEK_API_KEY}"
  base_url: "https://api.deepseek.com/v1"
  model: "deepseek-chat"
```

然后设置环境变量：

**Linux/macOS**:
```bash
export DB_USER=your_db_user
export DB_PASSWORD=your_db_password
export DEEPSEEK_API_KEY=sk-your-deepseek-key
```

**Windows PowerShell**:
```powershell
$env:DB_USER="your_db_user"
$env:DB_PASSWORD="your_db_password"
$env:DEEPSEEK_API_KEY="sk-your-deepseek-key"
```

**Windows CMD**:
```cmd
set DB_USER=your_db_user
set DB_PASSWORD=your_db_password
set DEEPSEEK_API_KEY=sk-your-deepseek-key
```

> 📖 **详细配置说明**：请查看 [CONFIGURATION.md](./CONFIGURATION.md)

### 运行

```bash
python -m pg_mcp
```

## 项目结构

```
pg_mcp/
├── __init__.py
├── __main__.py              # 入口点
├── server.py                # FastMCP服务器定义
├── config/
│   └── settings.py          # Pydantic Settings配置
├── models/
│   ├── schema.py            # Schema数据模型
│   ├── query.py             # 查询请求/响应模型
│   └── errors.py            # 错误模型
├── services/                # 服务层（Phase 3）
├── security/                # 安全层（Phase 2）
└── infrastructure/
    ├── db_pool.py           # 数据库连接池管理
    └── llm_client.py        # LLM客户端封装
```

## 开发

### 代码质量检查

```bash
# 格式化
ruff format .

# Lint
ruff check .

# 类型检查
mypy .

# 运行测试
pytest
```

### 测试覆盖率

```bash
pytest --cov=pg_mcp --cov-report=term-missing
```

## 技术栈

- **Python**: ≥3.10
- **FastMCP**: ≥2.0 - MCP 协议实现
- **asyncpg**: ≥0.29 - PostgreSQL 异步驱动
- **SQLGlot**: ≥25.0 - SQL 解析与安全校验
- **Pydantic**: ≥2.0 - 数据模型与配置
- **openai**: ≥1.0 - LLM 客户端（兼容 DeepSeek）

## 实现状态

- ✅ **Phase 0**: 项目初始化
- ✅ **Phase 1**: 基础设施层（配置、模型、连接池、LLM客户端）
- ✅ **Phase 2**: 安全层（SQL校验器、函数守卫、脱敏器）
- ✅ **Phase 3**: 服务层（Schema服务、查询服务、验证服务）
- ✅ **Phase 4**: MCP 协议层（FastMCP集成、Tools、Resources）
- ✅ **Phase 5**: 限流/熔断/监控
- ✅ **Phase 6**: 集成测试与文档

## MCP 客户端使用

### Claude Desktop 配置

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

### 可用 Tools

- `query` - 执行自然语言查询
- `list_databases` - 列出所有数据库
- `list_schemas` - 列出指定数据库的schema
- `list_tables` - 列出指定schema的表
- `describe_table` - 获取表详细结构
- `refresh_schema` - 刷新schema缓存

### 可用 Resources

- `schema://databases` - 所有数据库列表
- `schema://{database}/schemas` - Schema列表
- `schema://{database}/{schema}/tables` - 表列表
- `schema://{database}/{schema}/{table}` - 表详情

## 文档

- [配置说明](./CONFIGURATION.md) - 详细的配置指南
- [故障排除](./TROUBLESHOOTING.md) - 常见问题解决方案
- [实现报告](./PHASE0-1_COMPLETE.md) - Phase 0-1 实现详情
- [实现报告](./PHASE2-3_COMPLETE.md) - Phase 2-3 实现详情
- [实现报告](./PHASE4-5_COMPLETE.md) - Phase 4-5 实现详情

## 许可证

MIT

