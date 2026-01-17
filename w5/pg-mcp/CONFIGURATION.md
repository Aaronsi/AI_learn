# 配置说明

PostgreSQL 和 DeepSeek API 的配置通过 **YAML 配置文件** 和 **环境变量** 两种方式管理。

## 配置文件位置

配置文件：`pg_mcp.yaml`（项目根目录）

## 配置方式

### 方式一：YAML 配置文件（推荐）

1. **复制示例配置文件**：
```bash
cd w5/pg-mcp
cp pg_mcp.yaml.example pg_mcp.yaml
```

2. **编辑 `pg_mcp.yaml`**：

#### PostgreSQL 数据库配置

```yaml
databases:
  - name: "main"                    # 数据库别名（用于查询时指定）
    host: "localhost"              # PostgreSQL 主机地址
    port: 5432                      # PostgreSQL 端口
    database: "myapp"                # 数据库名
    username: "your_db_user"        # 数据库用户名
    password: "your_db_password"     # 数据库密码（或使用环境变量）
    role: "readonly_role"           # 可选：只读角色（用于降权）
    ssl_mode: "prefer"               # SSL模式：disable/prefer/require/verify-ca/verify-full
    schemas:                         # 要加载的schema列表
      - "public"
      - "sales"
    exclude_tables:                  # 排除的表（支持通配符）
      - "internal_logs"
      - "audit_*"
    min_pool_size: 2                 # 连接池最小连接数
    max_pool_size: 10                # 连接池最大连接数
```

#### DeepSeek API 配置

```yaml
llm:
  api_key: "sk-your-deepseek-api-key"  # DeepSeek API Key（或使用环境变量）
  base_url: "https://api.deepseek.com/v1"  # API 基础URL
  model: "deepseek-chat"              # 模型名称
  temperature: 0.1                    # 温度参数（0-2）
  max_tokens: 2048                    # 最大token数
  timeout: 30                         # 超时时间（秒）
```

### 方式二：环境变量（推荐用于敏感信息）

配置文件支持环境变量替换，格式：`${ENV_VAR_NAME}`

#### 在 YAML 中使用环境变量

```yaml
databases:
  - name: "main"
    host: "localhost"
    port: 5432
    database: "myapp"
    username: "${DB_USER}"           # 从环境变量读取
    password: "${DB_PASSWORD}"       # 从环境变量读取

llm:
  api_key: "${DEEPSEEK_API_KEY}"     # 从环境变量读取
  base_url: "https://api.deepseek.com/v1"
  model: "deepseek-chat"
```

#### 设置环境变量

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

### 方式三：完全使用环境变量

配置系统支持通过环境变量覆盖 YAML 配置，使用 `PG_MCP_` 前缀：

**环境变量命名规则**：
- 前缀：`PG_MCP_`
- 嵌套配置使用 `__` 分隔
- 列表使用索引（从0开始）

**示例**：

```bash
# 数据库配置
export PG_MCP_DATABASES__0__NAME="main"
export PG_MCP_DATABASES__0__HOST="localhost"
export PG_MCP_DATABASES__0__PORT=5432
export PG_MCP_DATABASES__0__DATABASE="myapp"
export PG_MCP_DATABASES__0__USERNAME="db_user"
export PG_MCP_DATABASES__0__PASSWORD="db_password"

# LLM配置
export PG_MCP_LLM__API_KEY="sk-your-deepseek-key"
export PG_MCP_LLM__BASE_URL="https://api.deepseek.com/v1"
export PG_MCP_LLM__MODEL="deepseek-chat"
```

## 完整配置示例

### 最小配置（必需项）

```yaml
databases:
  - name: "main"
    database: "myapp"
    username: "${DB_USER}"
    password: "${DB_PASSWORD}"

llm:
  api_key: "${DEEPSEEK_API_KEY}"
```

### 完整配置示例

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
  enable_result_validation: true
  enable_explain_check: false
  explain_max_cost: null
  explain_max_rows: null

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

## 配置优先级

1. **环境变量**（最高优先级）
2. **YAML 配置文件**
3. **默认值**

## 配置文件查找顺序

1. 当前工作目录的 `pg_mcp.yaml`
2. 用户主目录的 `pg_mcp.yaml`
3. 系统配置目录的 `pg_mcp.yaml`

## 安全建议

1. **敏感信息使用环境变量**：
   - 数据库密码
   - API Key
   - 其他敏感凭证

2. **不要提交配置文件到版本控制**：
   - `pg_mcp.yaml` 已在 `.gitignore` 中
   - 只提交 `pg_mcp.yaml.example` 作为模板

3. **使用只读角色**：
   - 配置 `role: "readonly_role"` 实现数据库权限降权
   - 确保数据库用户只有只读权限

## 验证配置

配置加载后，应用启动时会：
1. 验证数据库连接
2. 预加载 Schema 信息
3. 检查 LLM API 配置

如果配置有误，启动时会显示错误信息。

## 多数据库配置

支持配置多个数据库：

```yaml
databases:
  - name: "main"
    host: "localhost"
    database: "myapp"
    username: "${DB_USER_MAIN}"
    password: "${DB_PASSWORD_MAIN}"
    
  - name: "analytics"
    host: "analytics-db.example.com"
    database: "analytics_db"
    username: "${DB_USER_ANALYTICS}"
    password: "${DB_PASSWORD_ANALYTICS}"
```

查询时可以通过 `database` 参数指定使用哪个数据库。

## 常见问题

### Q: 配置文件找不到怎么办？
A: 确保 `pg_mcp.yaml` 在项目根目录（`w5/pg-mcp/`），或使用环境变量配置。

### Q: 环境变量不生效？
A: 检查环境变量名称是否正确，确保使用 `${VAR_NAME}` 格式，且变量已正确设置。

### Q: 如何测试配置？
A: 运行 `python -m pg_mcp`，如果配置正确，服务器会正常启动；如果有错误，会显示具体错误信息。

### Q: SSL 连接失败？
A: 根据你的 PostgreSQL 配置调整 `ssl_mode`：
- `disable` - 禁用 SSL
- `prefer` - 优先使用 SSL（默认）
- `require` - 必须使用 SSL
- `verify-ca` - 验证 CA 证书
- `verify-full` - 完整验证

