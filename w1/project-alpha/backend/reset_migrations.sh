#!/bin/bash
# 重置并重新创建 M1 迁移步骤

set -e

echo "=== 重置 M1 迁移步骤 ==="

# 步骤 1: 检查当前迁移状态
echo ""
echo "1. 检查当前迁移状态..."
cd "$(dirname "$0")"
uv run alembic current || echo "没有当前迁移版本"

# 步骤 2: 降级到基础版本（如果存在）
echo ""
echo "2. 降级所有迁移..."
uv run alembic downgrade base 2>/dev/null || echo "没有需要降级的迁移"

# 步骤 3: 删除数据库中的表（可选，谨慎使用）
echo ""
read -p "是否删除数据库中的所有表？这将删除所有数据！(y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "删除数据库表..."
    psql -U postgres -d postgres <<EOF
DROP SCHEMA IF EXISTS public CASCADE;
CREATE SCHEMA public;
GRANT ALL ON SCHEMA public TO postgres;
GRANT ALL ON SCHEMA public TO public;
EOF
    echo "数据库表已删除"
else
    echo "跳过删除数据库表"
fi

# 步骤 4: 删除迁移版本记录
echo ""
echo "3. 清理迁移版本记录..."
psql -U postgres -d postgres -c "DROP TABLE IF EXISTS alembic_version;" 2>/dev/null || echo "alembic_version 表不存在"

# 步骤 5: 删除旧的枚举类型（如果存在）
echo ""
echo "4. 清理旧的枚举类型..."
psql -U postgres -d postgres -c "DROP TYPE IF EXISTS ticket_status CASCADE;" 2>/dev/null || echo "ticket_status 枚举类型不存在"

# 步骤 6: 运行初始迁移
echo ""
echo "5. 运行初始迁移..."
uv run alembic upgrade head

# 步骤 7: 验证
echo ""
echo "6. 验证迁移结果..."
uv run alembic current

echo ""
echo "=== 迁移重置完成 ==="
echo ""
echo "验证数据库结构："
psql -U postgres -d postgres -c "SELECT enumlabel FROM pg_enum WHERE enumtypid = 'ticket_status'::regtype;"
psql -U postgres -d postgres -c "\dt"
