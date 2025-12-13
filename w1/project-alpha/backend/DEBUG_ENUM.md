# 调试枚举值问题

## 问题描述

数据库中的枚举值已经是小写的 `open` 和 `done`，但 SQLAlchemy 仍然报错说可能的值是 `OPEN, DONE`（大写）。

## 可能的原因

1. **SQLAlchemy 连接池缓存**：连接池可能缓存了旧的枚举类型定义
2. **SQLAlchemy Enum 配置**：可能需要明确指定使用枚举的值而不是键名
3. **数据库连接问题**：可能需要重新建立连接

## 解决方案

### 方案 1: 重启后端服务（最简单）

完全停止并重启后端服务，清除连接池缓存：

```bash
# 完全停止服务（确保进程已终止）
# 然后重新启动
cd w1/project-alpha/backend
uv run uvicorn app.main:app --reload --port 8000
```

### 方案 2: 验证数据库中的枚举值

```sql
-- 连接到数据库
psql -U postgres -d postgres

-- 检查枚举值（应该显示小写）
SELECT enumlabel FROM pg_enum WHERE enumtypid = 'ticket_status'::regtype;

-- 检查表中的实际值
SELECT DISTINCT status FROM tickets LIMIT 10;
```

### 方案 3: 检查 SQLAlchemy 配置

已更新 `models.py` 中的枚举配置，明确指定使用枚举的值：

```python
SqlEnum(TicketStatus, name="ticket_status", values_callable=lambda x: [e.value for e in x])
```

### 方案 4: 清除连接池（如果使用连接池）

如果问题仍然存在，可能需要清除数据库连接：

```python
# 在 db.py 中添加连接池清理
from app.db import engine
await engine.dispose()
```

## 验证步骤

1. **重启后端服务**
2. **测试创建 ticket**：
   ```bash
   curl -X POST http://localhost:8000/tickets \
     -H "Content-Type: application/json" \
     -d '{"title": "测试", "description": "测试描述"}'
   ```
3. **检查日志**：查看是否有枚举相关的错误

## 如果问题仍然存在

检查数据库中的实际枚举类型定义：

```sql
-- 查看枚举类型的完整定义
SELECT
    t.typname as enum_name,
    e.enumlabel as enum_value,
    e.enumsortorder
FROM pg_type t
JOIN pg_enum e ON t.oid = e.enumtypid
WHERE t.typname = 'ticket_status'
ORDER BY e.enumsortorder;
```

如果看到大写的值，说明数据库中的枚举类型仍然是大写的，需要执行修复脚本。
