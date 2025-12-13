# M1 迁移步骤 - 重新创建指南

## 概述

根据实现计划 M1，需要创建以下数据库结构：
- `tags` 表
- `tickets` 表（包含枚举类型 `ticket_status`）
- `ticket_tags` 关联表
- 必要的索引和约束

## 快速重置步骤

### 方法 1: 使用 PowerShell 脚本（Windows）

```powershell
cd w1/project-alpha/backend
.\reset_migrations.ps1
```

### 方法 2: 手动执行步骤

#### 步骤 1: 检查当前状态

```bash
cd w1/project-alpha/backend

# 查看当前迁移版本
uv run alembic current

# 查看迁移历史
uv run alembic history
```

#### 步骤 2: 降级所有迁移

```bash
# 降级到基础版本（删除所有表）
uv run alembic downgrade base
```

#### 步骤 3: 清理数据库（如果需要）

```sql
-- 连接到数据库
psql -U postgres -d postgres

-- 删除所有表（谨慎！会删除所有数据）
DROP SCHEMA IF EXISTS public CASCADE;
CREATE SCHEMA public;
GRANT ALL ON SCHEMA public TO postgres;
GRANT ALL ON SCHEMA public TO public;

-- 删除迁移版本表
DROP TABLE IF EXISTS alembic_version;

-- 删除枚举类型（如果存在）
DROP TYPE IF EXISTS ticket_status CASCADE;
```

#### 步骤 4: 运行初始迁移

```bash
# 运行迁移
uv run alembic upgrade head
```

#### 步骤 5: 验证迁移结果

```bash
# 检查迁移版本
uv run alembic current

# 应该显示：0001_initial (head)
```

#### 步骤 6: 验证数据库结构

```sql
-- 检查表是否存在
\dt

-- 应该看到：
-- - tags
-- - tickets
-- - ticket_tags

-- 检查枚举类型值（必须是小写）
SELECT enumlabel FROM pg_enum WHERE enumtypid = 'ticket_status'::regtype;

-- 应该显示：
--  enumlabel
-- ----------
--  open
--  done

-- 检查索引
\di

-- 应该看到：
-- - ix_tickets_status
-- - ix_tickets_title_lower
-- - ix_ticket_tags_tag_id
-- - ux_tags_name_lower

-- 检查约束
SELECT conname, contype FROM pg_constraint WHERE conrelid = 'tickets'::regclass;

-- 应该看到：
-- - ck_tickets_status (check constraint)
```

## 迁移文件检查清单

确保 `0001_initial.py` 包含：

- ✅ `tags` 表
  - id (UUID, PK)
  - name (VARCHAR(50), NOT NULL, UNIQUE)
  - created_at (TIMESTAMPTZ, NOT NULL, default now())
  - 索引：ux_tags_name_lower (lower(name), unique)

- ✅ `tickets` 表
  - id (UUID, PK)
  - title (VARCHAR(200), NOT NULL)
  - description (TEXT, NULL)
  - status (ticket_status enum, NOT NULL, default 'open')
  - created_at (TIMESTAMPTZ, NOT NULL, default now())
  - updated_at (TIMESTAMPTZ, NOT NULL, default now())
  - 约束：ck_tickets_status (status IN ('open', 'done'))
  - 索引：ix_tickets_status, ix_tickets_title_lower

- ✅ `ticket_tags` 表
  - ticket_id (UUID, FK -> tickets.id, CASCADE DELETE)
  - tag_id (UUID, FK -> tags.id, CASCADE DELETE)
  - 复合主键 (ticket_id, tag_id)
  - 索引：ix_ticket_tags_tag_id

- ✅ `ticket_status` 枚举类型
  - 值：'open', 'done'（小写！）

## 常见问题

### Q: 迁移失败，提示枚举类型已存在

**A:** 先删除旧的枚举类型：
```sql
DROP TYPE IF EXISTS ticket_status CASCADE;
```

### Q: 迁移失败，提示表已存在

**A:** 先删除所有表：
```sql
DROP SCHEMA IF EXISTS public CASCADE;
CREATE SCHEMA public;
```

### Q: 枚举值是大写的 OPEN/DONE

**A:** 确保迁移文件中使用小写：
```python
ticket_status = sa.Enum("open", "done", name="ticket_status")
```

### Q: 迁移后验证枚举值

**A:** 运行：
```sql
SELECT enumlabel FROM pg_enum WHERE enumtypid = 'ticket_status'::regtype;
```
应该看到 `open` 和 `done`（小写）。

## 导入测试数据（可选）

迁移完成后，可以导入 seed 数据：

```bash
psql -U postgres -d postgres -f seed.sql
```

## 验证 API

迁移完成后，启动后端服务并测试：

```bash
uv run uvicorn app.main:app --reload --port 8000
```

测试健康检查：
```bash
curl http://localhost:8000/health
```

应该返回：
```json
{"status": "ok"}
```
