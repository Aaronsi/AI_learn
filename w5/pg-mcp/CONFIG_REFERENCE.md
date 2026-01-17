# 配置参考文档

本文档详细说明 `pg_mcp.yaml` 配置文件中的所有配置项。

## 配置文件结构

```yaml
databases:          # 数据库配置列表（必需）
llm:               # LLM配置（必需）
security:          # 安全配置（可选，有默认值）
rate_limit:        # 限流配置（可选，有默认值）
cache:             # 缓存配置（可选，有默认值）
log_level:         # 日志级别（可选，默认INFO）
```

## 配置项详解

### databases（必需）

数据库连接配置列表。支持配置多个数据库。

#### 单个数据库配置项

| 配置项 | 类型 | 必需 | 默认值 | 说明 |
|--------|------|------|--------|------|
| `name` | string | ✅ | - | 数据库别名，用于查询时指定数据库 |
| `host` | string | ❌ | `localhost` | PostgreSQL 主机地址 |
| `port` | integer | ❌ | `5432` | PostgreSQL 端口 |
| `database` | string | ✅ | - | 数据库名 |
| `username` | string | ✅ | - | 数据库用户名 |
| `password` | string | ✅ | - | 数据库密码（建议使用环境变量） |
| `role` | string | ❌ | `null` | 可选的只读角色，用于权限降权 |
| `ssl_mode` | string | ❌ | `prefer` | SSL模式：`disable`/`prefer`/`require`/`verify-ca`/`verify-full` |
| `schemas` | list[string] | ❌ | `["public"]` | 要加载的schema列表 |
| `exclude_tables` | list[string] | ❌ | `[]` | 排除的表名（支持通配符，如 `audit_*`） |
| `min_pool_size` | integer | ❌ | `2` | 连接池最小连接数（≥1） |
| `max_pool_size` | integer | ❌ | `10` | 连接池最大连接数（≥1） |

**示例**：
```yaml
databases:
  - name: "main"
    host: "localhost"
    port: 5432
    database: "myapp"
    username: "${DB_USER}"
    password: "${DB_PASSWORD}"
    role: "readonly_role"
    ssl_mode: "prefer"
    schemas:
      - "public"
      - "sales"
    exclude_tables:
      - "internal_logs"
      - "audit_*"
    min_pool_size: 2
    max_pool_size: 10
```

### llm（必需）

LLM（DeepSeek）API 配置。

| 配置项 | 类型 | 必需 | 默认值 | 说明 |
|--------|------|------|--------|------|
| `api_key` | string | ✅ | - | DeepSeek API Key（建议使用环境变量） |
| `base_url` | string | ❌ | `https://api.deepseek.com/v1` | API 基础URL |
| `model` | string | ❌ | `deepseek-chat` | 模型名称 |
| `temperature` | float | ❌ | `0.1` | 温度参数（0-2），控制输出随机性 |
| `max_tokens` | integer | ❌ | `2048` | 最大token数（≥1） |
| `timeout` | integer | ❌ | `30` | 请求超时时间（秒，≥1） |

**示例**：
```yaml
llm:
  api_key: "${DEEPSEEK_API_KEY}"
  base_url: "https://api.deepseek.com/v1"
  model: "deepseek-chat"
  temperature: 0.1
  max_tokens: 2048
  timeout: 30
```

### security（可选）

安全配置。

| 配置项 | 类型 | 必需 | 默认值 | 说明 |
|--------|------|------|--------|------|
| `max_rows` | integer | ❌ | `200` | 默认最大返回行数（≥1） |
| `hard_max_rows` | integer | ❌ | `1000` | 硬上限，无论如何不超过此值（≥1） |
| `query_timeout` | integer | ❌ | `30` | 查询超时秒数（≥1） |
| `allowed_functions` | list[string] | ❌ | `[]` | 函数白名单（空列表表示使用默认白名单） |
| `sensitive_columns` | list[string] | ❌ | `["password", "secret", "token", "credential", "ssn", "credit_card"]` | 敏感列名模式 |
| `enable_result_validation` | boolean | ❌ | `true` | 是否启用结果验证 |
| `max_retry_attempts` | integer | ❌ | `3` | 最大重试次数（≥1） |
| `validation_sample_rows` | integer | ❌ | `20` | 验证时采样行数（≥1） |
| `validation_sample_cols` | integer | ❌ | `10` | 验证时采样列数（≥1） |
| `enable_explain_check` | boolean | ❌ | `false` | 是否在执行前进行 EXPLAIN 检查 |
| `explain_max_cost` | float | ❌ | `null` | EXPLAIN 允许的最大成本（≥0） |
| `explain_max_rows` | integer | ❌ | `null` | EXPLAIN 允许的最大行数（≥1） |

**示例**：
```yaml
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
  validation_sample_rows: 20
  validation_sample_cols: 10
  enable_explain_check: false
  explain_max_cost: null
  explain_max_rows: null
```

### rate_limit（可选）

限流和熔断配置。

| 配置项 | 类型 | 必需 | 默认值 | 说明 |
|--------|------|------|--------|------|
| `llm_requests_per_minute` | integer | ❌ | `60` | LLM 每分钟请求数限制 |
| `db_queries_per_minute` | integer | ❌ | `100` | 数据库每分钟查询数限制 |
| `enable_circuit_breaker` | boolean | ❌ | `true` | 是否启用熔断器 |
| `circuit_breaker_threshold` | integer | ❌ | `5` | 连续失败次数触发熔断 |
| `circuit_breaker_timeout` | integer | ❌ | `60` | 熔断恢复时间（秒） |

**示例**：
```yaml
rate_limit:
  llm_requests_per_minute: 60
  db_queries_per_minute: 100
  enable_circuit_breaker: true
  circuit_breaker_threshold: 5
  circuit_breaker_timeout: 60
```

### cache（可选）

Schema 缓存配置。

| 配置项 | 类型 | 必需 | 默认值 | 说明 |
|--------|------|------|--------|------|
| `enable_disk_cache` | boolean | ❌ | `true` | 是否启用磁盘缓存 |
| `cache_dir` | string | ❌ | `.pg_mcp_cache` | 缓存目录路径 |
| `cache_ttl_hours` | integer | ❌ | `24` | 缓存TTL（小时） |
| `auto_refresh_interval_hours` | integer | ❌ | `0` | 自动刷新间隔（小时，0表示禁用） |

**示例**：
```yaml
cache:
  enable_disk_cache: true
  cache_dir: ".pg_mcp_cache"
  cache_ttl_hours: 24
  auto_refresh_interval_hours: 0  # 0表示禁用自动刷新
```

### log_level（可选）

日志级别配置。

| 值 | 说明 |
|----|------|
| `DEBUG` | 详细调试信息 |
| `INFO` | 一般信息（默认） |
| `WARNING` | 警告信息 |
| `ERROR` | 错误信息 |

**示例**：
```yaml
log_level: "INFO"
```

## 环境变量配置

所有配置项都可以通过环境变量覆盖，使用 `PG_MCP_` 前缀。

### 环境变量命名规则

- 前缀：`PG_MCP_`
- 嵌套配置使用 `__` 分隔
- 列表使用索引（从0开始）

### 示例

```bash
# 数据库配置
export PG_MCP_DATABASES__0__NAME="main"
export PG_MCP_DATABASES__0__HOST="localhost"
export PG_MCP_DATABASES__0__PORT=5432
export PG_MCP_DATABASES__0__DATABASE="myapp"
export PG_MCP_DATABASES__0__USERNAME="db_user"
export PG_MCP_DATABASES__0__PASSWORD="db_password"

# LLM配置
export PG_MCP_LLM__API_KEY="sk-your-key"
export PG_MCP_LLM__BASE_URL="https://api.deepseek.com/v1"
export PG_MCP_LLM__MODEL="deepseek-chat"

# 安全配置
export PG_MCP_SECURITY__MAX_ROWS=200
export PG_MCP_SECURITY__HARD_MAX_ROWS=1000

# 日志级别
export PG_MCP_LOG_LEVEL="INFO"
```

## 配置验证

应用启动时会自动验证配置：

1. **必需字段检查**：确保所有必需字段都已填写
2. **类型验证**：确保字段类型正确（数字、字符串、布尔值）
3. **范围验证**：确保数值在有效范围内（如端口、超时时间）
4. **连接测试**：尝试连接数据库（如果配置了）

## 配置优先级

1. **环境变量**（最高优先级）
2. **YAML 配置文件**
3. **默认值**（最低优先级）

## 最佳实践

### 1. 敏感信息使用环境变量

```yaml
# ✅ 推荐
databases:
  - name: "main"
    username: "${DB_USER}"
    password: "${DB_PASSWORD}"

llm:
  api_key: "${DEEPSEEK_API_KEY}"

# ❌ 不推荐（生产环境）
databases:
  - name: "main"
    username: "myuser"
    password: "mypassword"
```

### 2. 使用只读角色

```yaml
databases:
  - name: "main"
    role: "readonly_role"  # 权限降权
```

### 3. 合理配置连接池

```yaml
databases:
  - name: "main"
    min_pool_size: 2   # 根据并发需求调整
    max_pool_size: 10  # 不超过数据库最大连接数
```

### 4. 启用磁盘缓存

```yaml
cache:
  enable_disk_cache: true
  cache_ttl_hours: 24
```

### 5. 配置自动刷新（可选）

```yaml
cache:
  auto_refresh_interval_hours: 24  # 每24小时自动刷新
```

## 多环境配置

### 开发环境

```yaml
databases:
  - name: "dev"
    host: "localhost"
    database: "dev_db"

log_level: "DEBUG"
```

### 生产环境

```yaml
databases:
  - name: "prod"
    host: "prod-db.example.com"
    database: "prod_db"
    role: "readonly_role"
    ssl_mode: "require"

log_level: "INFO"
cache:
  auto_refresh_interval_hours: 6  # 更频繁的刷新
```

## 配置示例

### 最小配置

```yaml
databases:
  - name: "main"
    database: "myapp"
    username: "${DB_USER}"
    password: "${DB_PASSWORD}"

llm:
  api_key: "${DEEPSEEK_API_KEY}"
```

### 完整配置

参考 `pg_mcp.yaml.example` 文件。

## 常见配置错误

### 错误1：缺少必需字段

```yaml
# ❌ 错误
databases:
  - name: "main"
    # 缺少 database, username, password

# ✅ 正确
databases:
  - name: "main"
    database: "myapp"
    username: "${DB_USER}"
    password: "${DB_PASSWORD}"
```

### 错误2：类型错误

```yaml
# ❌ 错误
databases:
  - name: "main"
    port: "5432"  # 应该是数字

# ✅ 正确
databases:
  - name: "main"
    port: 5432
```

### 错误3：无效值

```yaml
# ❌ 错误
security:
  max_rows: -1  # 不能为负数

# ✅ 正确
security:
  max_rows: 200
```

## 配置检查清单

在部署前，检查以下配置：

- [ ] 所有必需字段已填写
- [ ] 敏感信息使用环境变量
- [ ] 数据库连接参数正确
- [ ] LLM API Key 有效
- [ ] SSL 配置正确（生产环境）
- [ ] 连接池大小合理
- [ ] 缓存配置合理
- [ ] 日志级别适当
- [ ] 安全限制合理（max_rows, hard_max_rows）

