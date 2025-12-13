# 故障排查指南

## 常见错误及解决方案

### 1. 枚举值大小写错误

**错误信息：**
```
sqlalchemy.exc.DBAPIError: 对于枚举ticket_status的输入值无效: "DONE"
或
sqlalchemy.exc.DBAPIError: 对于枚举ticket_status的输入值无效: "OPEN"
```

**原因：**
- 数据库枚举类型 `ticket_status` 只接受小写值：`"open"` 和 `"done"`
- 但代码或前端可能发送了大写的 `"DONE"`、`"OPEN"` 或其他大小写组合
- 问题可能出现在：
  1. **请求体**（POST/PATCH）：`{"status": "DONE"}`
  2. **查询参数**（GET）：`?status=OPEN`

**解决方案：**

已在两个地方添加了状态值规范化：

1. **请求体验证**（`app/schemas.py` 的 `TicketUpdate` 类）：
   ```python
   @field_validator("status", mode="before")
   @classmethod
   def normalize_status(cls, value: Optional[str | TicketStatus]) -> Optional[TicketStatus]:
       if value is None:
           return None
       if isinstance(value, str):
           normalized = value.strip().lower()
           if normalized == "open":
               return TicketStatus.OPEN
           elif normalized == "done":
               return TicketStatus.DONE
           else:
               raise ValueError(f"状态值无效: {value}，必须是 'open' 或 'done'")
       return value
   ```

2. **查询参数解析**（`app/routes/tickets.py` 的 `_parse_status` 函数）：
   ```python
   def _parse_status(raw: str | None) -> TicketStatus | None:
       """解析并规范化状态查询参数，支持大小写不敏感"""
       if raw is None:
           return None
       normalized = raw.strip().lower()
       if normalized == "open":
           return TicketStatus.OPEN
       elif normalized == "done":
           return TicketStatus.DONE
       else:
           raise ValueError(f"状态值无效: {raw}，必须是 'open' 或 'done'")
   ```

**验证修复：**

重启后端服务后，以下请求都应该正常工作：

**请求体（POST/PATCH）：**
```bash
# 小写（正确）
curl -X PATCH http://localhost:8000/tickets/{id} -H "Content-Type: application/json" -d '{"status": "done"}'

# 大写（现在也会被自动转换为小写）
curl -X PATCH http://localhost:8000/tickets/{id} -H "Content-Type: application/json" -d '{"status": "DONE"}'

# 混合大小写（也会被转换）
curl -X PATCH http://localhost:8000/tickets/{id} -H "Content-Type: application/json" -d '{"status": "DoNe"}'
```

**查询参数（GET）：**
```bash
# 小写
curl "http://localhost:8000/tickets?status=open"

# 大写（现在也会被自动转换）
curl "http://localhost:8000/tickets?status=OPEN"

# 混合大小写
curl "http://localhost:8000/tickets?status=OpEn"
```

**预防措施：**

1. **前端代码**：确保使用枚举的值而不是键名
   ```typescript
   // ✅ 正确：使用枚举值
   status: TicketStatus.DONE  // 发送 "done"

   // ❌ 错误：不要直接使用字符串
   status: "DONE"
   ```

2. **API 调用**：确保发送的是枚举的值
   ```typescript
   // ✅ 正确
   await ticketsApi.update(id, { status: TicketStatus.DONE })

   // ❌ 错误
   await ticketsApi.update(id, { status: "DONE" })
   ```

3. **测试代码**：使用枚举的值
   ```python
   # ✅ 正确
   TicketStatus.DONE.value  # "done"

   # ❌ 错误
   "DONE"
   ```

### 2. 数据库表不存在

**错误信息：**
```
关系 "tags" 不存在
```

**解决方案：**

运行数据库迁移：
```bash
cd backend
uv run alembic upgrade head
```

### 3. 编码错误

**错误信息：**
```
编码"GBK"的字符在编码"UTF8"没有相对应值
```

**解决方案：**

1. 确保 `seed.sql` 文件以 UTF-8 编码保存
2. 文件开头已包含 `SET client_encoding = 'UTF8';`
3. 使用环境变量设置编码：
   ```bash
   PGCLIENTENCODING=UTF8 psql -U postgres -d postgres -f seed.sql
   ```

### 4. CORS 错误

**错误信息：**
```
Access to fetch at 'http://localhost:8000/...' from origin 'http://localhost:3000' has been blocked by CORS policy
```

**解决方案：**

在 `backend/.env` 文件中添加：
```env
ALLOWED_ORIGINS=http://localhost:3000
```

### 5. 数据库连接错误

**错误信息：**
```
could not connect to server: Connection refused
```

**解决方案：**

1. 确保 PostgreSQL 服务正在运行
2. 检查 `DATABASE_URL` 环境变量是否正确
3. 验证数据库用户权限

## 调试技巧

### 查看后端日志

后端服务会输出详细的请求日志，包括：
- 请求路径和方法
- 请求参数
- 响应状态码
- 处理耗时

### 使用 Swagger UI

访问 `http://localhost:8000/docs` 查看交互式 API 文档，可以直接测试 API。

### 检查数据库

```bash
# 连接到数据库
psql -U postgres -d postgres

# 查看 tickets 表
SELECT * FROM tickets LIMIT 10;

# 查看枚举类型定义
SELECT enumlabel FROM pg_enum WHERE enumtypid = 'ticket_status'::regtype;
```

### 查看迁移历史

```bash
cd backend
uv run alembic history
uv run alembic current
```

## 联系支持

如果问题仍然存在，请提供：
1. 完整的错误信息
2. 相关代码片段
3. 数据库版本和配置
4. 后端日志输出
