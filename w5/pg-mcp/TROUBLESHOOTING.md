# 故障排除指南

本文档提供常见问题的诊断和解决方案。

## 目录

- [配置问题](#配置问题)
- [数据库连接问题](#数据库连接问题)
- [LLM API 问题](#llm-api-问题)
- [SQL 执行问题](#sql-执行问题)
- [性能问题](#性能问题)
- [安全相关问题](#安全相关问题)

## 配置问题

### 问题：配置文件找不到

**症状**：
```
FileNotFoundError: pg_mcp.yaml not found
```

**解决方案**：
1. 确保 `pg_mcp.yaml` 文件在项目根目录（`w5/pg-mcp/`）
2. 或者使用环境变量配置（见 [CONFIGURATION.md](./CONFIGURATION.md)）
3. 检查当前工作目录：`pwd`（Linux/macOS）或 `Get-Location`（PowerShell）

### 问题：环境变量不生效

**症状**：
- 配置文件中使用 `${VAR_NAME}` 但变量值未加载

**解决方案**：
1. 检查环境变量是否设置：
   ```bash
   # Linux/macOS
   echo $DB_USER
   
   # Windows PowerShell
   $env:DB_USER
   ```

2. 确保变量名拼写正确（区分大小写）
3. 重启终端/IDE 以确保环境变量生效
4. 检查配置文件中的变量名格式：`${VAR_NAME}`（注意大括号）

### 问题：配置验证失败

**症状**：
```
ValidationError: ...
```

**解决方案**：
1. 检查 YAML 语法是否正确（缩进、引号等）
2. 验证必需字段是否都已填写：
   - `databases[].name`
   - `databases[].database`
   - `databases[].username`
   - `databases[].password`
   - `llm.api_key`
3. 检查字段类型是否正确（数字、字符串、布尔值）

## 数据库连接问题

### 问题：无法连接到 PostgreSQL

**症状**：
```
ErrorCode.DATABASE_CONNECTION_ERROR: 无法连接到数据库
```

**解决方案**：

1. **检查 PostgreSQL 是否运行**：
   ```bash
   # Linux/macOS
   pg_isready -h localhost -p 5432
   
   # Windows
   # 检查服务状态
   ```

2. **验证连接参数**：
   - `host`: 数据库主机地址
   - `port`: PostgreSQL 端口（默认 5432）
   - `database`: 数据库名（不是用户名）
   - `username`: 数据库用户名
   - `password`: 数据库密码

3. **检查网络连接**：
   ```bash
   # 测试端口是否可达
   telnet localhost 5432
   # 或
   nc -zv localhost 5432
   ```

4. **检查 SSL 配置**：
   - 如果 PostgreSQL 要求 SSL，设置 `ssl_mode: "require"`
   - 如果不需要 SSL，设置 `ssl_mode: "disable"`

5. **检查防火墙规则**：
   - 确保端口 5432 未被防火墙阻止

6. **验证用户权限**：
   - 确保数据库用户有连接权限
   - 检查 `pg_hba.conf` 配置

### 问题：连接池耗尽

**症状**：
```
asyncpg.exceptions.PoolAcquireTimeoutError
```

**解决方案**：
1. 增加连接池大小：
   ```yaml
   databases:
     - name: "main"
       min_pool_size: 5
       max_pool_size: 20
   ```

2. 检查是否有连接泄漏（未正确关闭的连接）
3. 检查数据库最大连接数限制：
   ```sql
   SHOW max_connections;
   ```

### 问题：只读事务错误

**症状**：
```
cannot execute INSERT/DELETE/UPDATE in a read-only transaction
```

**解决方案**：
- 这是正常的安全保护机制
- 确保只执行 SELECT 查询
- 检查 SQL 校验器是否正确拦截了 DML 语句

## LLM API 问题

### 问题：DeepSeek API 调用失败

**症状**：
```
ErrorCode.LLM_ERROR: LLM调用失败
```

**解决方案**：

1. **验证 API Key**：
   - 检查 API Key 是否正确
   - 确保 API Key 未过期
   - 验证 API Key 格式：`sk-...`

2. **检查网络连接**：
   ```bash
   curl https://api.deepseek.com/v1/models \
     -H "Authorization: Bearer YOUR_API_KEY"
   ```

3. **验证 API 端点**：
   - 默认：`https://api.deepseek.com/v1`
   - 如果使用代理，检查代理配置

4. **检查配额和限流**：
   - 查看 API 使用量是否超限
   - 检查限流配置：`rate_limit.llm_requests_per_minute`

5. **查看详细错误**：
   - 启用调试日志：`log_level: "DEBUG"`
   - 检查错误详情中的具体错误信息

### 问题：Token 使用量过高

**症状**：
- 收到 Token 阈值告警
- 服务进入降级模式

**解决方案**：
1. 检查 Token 使用统计：
   ```python
   from pg_mcp.infrastructure.metrics import Metrics
   # 查看 metrics.get_summary() 中的 tokens 统计
   ```

2. 优化 Schema 上下文：
   - 减少加载的 schema 数量
   - 排除不必要的表：`exclude_tables`

3. 调整 LLM 配置：
   ```yaml
   llm:
     max_tokens: 1024  # 减少最大 token 数
   ```

4. 启用降级策略：
   - 跳过结果验证
   - 仅返回 SQL（不执行）

### 问题：LLM 返回格式错误

**症状**：
```
ValueError: LLM返回空响应
JSONDecodeError: ...
```

**解决方案**：
1. 检查 LLM 响应格式：
   - 确保使用 `response_format={"type": "json_object"}`
   - 验证返回的 JSON 格式是否正确

2. 增加重试机制：
   ```yaml
   security:
     max_retry_attempts: 5
   ```

3. 调整 temperature 参数：
   ```yaml
   llm:
     temperature: 0.1  # 降低随机性
   ```

## SQL 执行问题

### 问题：SQL 安全校验失败

**症状**：
```
SecurityViolationError: SQL安全校验失败
```

**解决方案**：
1. **检查 SQL 内容**：
   - 确保只包含 SELECT 语句
   - 移除任何 DML/DDL 语句

2. **检查函数白名单**：
   ```yaml
   security:
     allowed_functions:
       - "custom_function_name"
   ```

3. **查看具体违规信息**：
   - 错误详情中包含具体的违规原因
   - 根据提示修改 SQL

### 问题：SQL 执行超时

**症状**：
```
ErrorCode.TIMEOUT_ERROR
```

**解决方案**：
1. 增加查询超时时间：
   ```yaml
   security:
     query_timeout: 60  # 秒
   ```

2. 优化 SQL 查询：
   - 添加适当的索引
   - 限制结果集大小
   - 使用 LIMIT 子句

3. 检查数据库性能：
   ```sql
   EXPLAIN ANALYZE your_query;
   ```

### 问题：结果被截断

**症状**：
- `truncated: true` 在响应中
- 结果行数少于预期

**解决方案**：
1. **这是正常的安全限制**：
   - 默认 `max_rows: 200`
   - 硬上限 `hard_max_rows: 1000`

2. **调整限制**（谨慎）：
   ```yaml
   security:
     max_rows: 500
     hard_max_rows: 2000
   ```

3. **使用分页**：
   - 通过 `page` 和 `page_size` 参数分页获取数据

## 性能问题

### 问题：Schema 加载缓慢

**症状**：
- 启动时 Schema 加载耗时过长
- 首次查询响应慢

**解决方案**：
1. **启用磁盘缓存**：
   ```yaml
   cache:
     enable_disk_cache: true
     cache_dir: ".pg_mcp_cache"
   ```

2. **减少加载的 Schema**：
   ```yaml
   databases:
     - name: "main"
       schemas:
         - "public"  # 只加载必要的 schema
   ```

3. **排除大表**：
   ```yaml
   databases:
     - name: "main"
       exclude_tables:
         - "large_log_table"
         - "audit_*"
   ```

4. **启用后台刷新**：
   ```yaml
   cache:
     auto_refresh_interval_hours: 24  # 后台自动刷新
   ```

### 问题：查询响应慢

**症状**：
- 查询执行时间过长
- P95 延迟高

**解决方案**：
1. **检查数据库性能**：
   - 查看慢查询日志
   - 分析查询计划

2. **优化 Schema 上下文**：
   - 减少发送给 LLM 的 Schema 信息量
   - 只包含相关表的 Schema

3. **启用结果验证跳过**（谨慎）：
   ```yaml
   security:
     enable_result_validation: false
   ```

4. **检查限流配置**：
   - 确保限流不会导致请求排队

## 安全相关问题

### 问题：敏感数据出现在日志中

**症状**：
- 日志中包含密码、API Key 等敏感信息

**解决方案**：
1. **检查日志脱敏配置**：
   - 确保 `sensitive_columns` 配置正确
   - 验证 `LogSanitizer` 正常工作

2. **检查日志级别**：
   ```yaml
   log_level: "INFO"  # 避免 DEBUG 级别泄露详细信息
   ```

3. **验证敏感列过滤**：
   - 确保敏感列名在配置中
   - 检查脱敏器是否正确过滤

### 问题：SQL 注入尝试

**症状**：
- 收到安全违规错误
- SQL 包含恶意代码

**解决方案**：
1. **这是正常的安全保护**：
   - SQL 校验器正确拦截了恶意 SQL
   - 检查错误信息了解具体违规

2. **验证 SQL 校验器**：
   - 运行安全测试：`pytest tests/integration/test_security.py`

3. **检查 LLM 生成质量**：
   - 如果 LLM 频繁生成不安全 SQL，考虑调整提示词
   - 增加 `confidence` 阈值要求

## 调试技巧

### 启用调试日志

```yaml
log_level: "DEBUG"
```

### 查看健康状态

```python
from pg_mcp.infrastructure.metrics import HealthChecker
# 调用 health_checker.check_health()
```

### 查看指标统计

```python
from pg_mcp.infrastructure.metrics import Metrics
# 调用 metrics.get_summary()
```

### 测试数据库连接

```python
from pg_mcp.infrastructure.db_pool import DBPoolManager
from pg_mcp.config.settings import Settings

settings = Settings()
db_pool = DBPoolManager()
await db_pool.initialize(settings.databases)
```

### 测试 LLM 连接

```python
from pg_mcp.infrastructure.llm_client import LLMClient
from pg_mcp.config.settings import Settings

settings = Settings()
llm_client = LLMClient(settings.llm)
# 尝试生成一个简单的 SQL
```

## 获取帮助

如果以上方案无法解决问题：

1. **查看日志**：
   - 检查应用日志输出
   - 查看错误堆栈信息

2. **运行测试**：
   ```bash
   pytest tests/unit -v
   pytest tests/integration -v
   ```

3. **检查配置**：
   - 验证配置文件格式
   - 确认所有必需字段已填写

4. **查看文档**：
   - [README.md](./README.md)
   - [CONFIGURATION.md](./CONFIGURATION.md)

## 常见错误代码

| 错误码 | 含义 | 解决方案 |
|--------|------|----------|
| E001 | 数据库连接错误 | 检查数据库配置和网络连接 |
| E002 | Schema 加载错误 | 检查数据库权限和 Schema 名称 |
| E003 | LLM 错误 | 检查 API Key 和网络连接 |
| E004 | SQL 生成错误 | 检查 LLM 配置和提示词 |
| E005 | 安全违规 | 检查 SQL 内容，确保只包含 SELECT |
| E006 | SQL 执行错误 | 检查 SQL 语法和数据库状态 |
| E007 | 验证错误 | 检查结果验证配置 |
| E008 | 超时错误 | 增加超时时间或优化查询 |
| E009 | 配置错误 | 检查配置文件格式和内容 |
| E010 | 限流 | 等待或调整限流配置 |
| E011 | 熔断器打开 | 等待熔断器恢复或检查服务状态 |

