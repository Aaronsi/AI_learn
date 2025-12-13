# 重新创建 M1 迁移步骤

## 步骤 1: 检查当前状态

首先检查数据库和迁移的当前状态：

```bash
cd w1/project-alpha/backend

# 查看当前迁移版本
uv run alembic current

# 查看迁移历史
uv run alembic history
```

## 步骤 2: 清理现有迁移（如果需要）

如果数据库中有数据需要保留，请先备份！

### 选项 A: 保留数据，只重置迁移历史

```bash
# 1. 删除所有迁移文件（保留 __init__.py）
# 手动删除 migrations/versions/ 下的所有 .py 文件

# 2. 清理 alembic_version 表
psql -U postgres -d postgres -c "DROP TABLE IF EXISTS alembic_version;"

# 3. 删除枚举类型（如果存在且需要重建）
psql -U postgres -d postgres -c "DROP TYPE IF EXISTS ticket_status CASCADE;"
```

### 选项 B: 完全重置（删除所有表和数据）

```bash
# 1. 删除所有表
psql -U postgres -d postgres -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"

# 2. 删除迁移文件
# 手动删除 migrations/versions/ 下的所有迁移文件（保留 __init__.py）
```

## 步骤 3: 重新创建初始迁移

```bash
# 创建新的初始迁移
uv run alembic revision --autogenerate -m "initial"

# 检查生成的迁移文件，确保：
# - 枚举类型使用小写值：("open", "done")
# - 包含所有必要的索引
# - 包含 CheckConstraint
```

## 步骤 4: 运行迁移

```bash
# 运行迁移
uv run alembic upgrade head

# 验证
uv run alembic current
```

## 步骤 5: 验证数据库结构

```sql
-- 连接到数据库
psql -U postgres -d postgres

-- 检查表是否存在
\dt

-- 检查枚举类型值（应该是小写）
SELECT enumlabel FROM pg_enum WHERE enumtypid = 'ticket_status'::regtype;

-- 检查索引
\di

-- 检查约束
SELECT conname, contype FROM pg_constraint WHERE conrelid = 'tickets'::regclass;
```

## 步骤 6: 导入测试数据（可选）

```bash
# 如果 seed.sql 存在，可以导入测试数据
psql -U postgres -d postgres -f seed.sql
```
