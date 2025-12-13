# PowerShell 脚本：重置并重新创建 M1 迁移步骤

Write-Host "=== 重置 M1 迁移步骤 ===" -ForegroundColor Cyan

# 步骤 1: 检查当前迁移状态
Write-Host ""
Write-Host "1. 检查当前迁移状态..." -ForegroundColor Yellow
cd $PSScriptRoot
uv run alembic current 2>&1 | Out-Null
if ($LASTEXITCODE -ne 0) {
    Write-Host "没有当前迁移版本" -ForegroundColor Gray
}

# 步骤 2: 降级到基础版本（如果存在）
Write-Host ""
Write-Host "2. 降级所有迁移..." -ForegroundColor Yellow
uv run alembic downgrade base 2>&1 | Out-Null
if ($LASTEXITCODE -ne 0) {
    Write-Host "没有需要降级的迁移" -ForegroundColor Gray
}

# 步骤 3: 删除数据库中的表（可选）
Write-Host ""
$confirm = Read-Host "是否删除数据库中的所有表？这将删除所有数据！(y/N)"
if ($confirm -eq "y" -or $confirm -eq "Y") {
    Write-Host "删除数据库表..." -ForegroundColor Yellow
    psql -U postgres -d postgres -c "DROP SCHEMA IF EXISTS public CASCADE; CREATE SCHEMA public; GRANT ALL ON SCHEMA public TO postgres; GRANT ALL ON SCHEMA public TO public;"
    Write-Host "数据库表已删除" -ForegroundColor Green
} else {
    Write-Host "跳过删除数据库表" -ForegroundColor Gray
}

# 步骤 4: 删除迁移版本记录
Write-Host ""
Write-Host "3. 清理迁移版本记录..." -ForegroundColor Yellow
psql -U postgres -d postgres -c "DROP TABLE IF EXISTS alembic_version;" 2>&1 | Out-Null
if ($LASTEXITCODE -ne 0) {
    Write-Host "alembic_version 表不存在" -ForegroundColor Gray
}

# 步骤 5: 删除旧的枚举类型（如果存在）
Write-Host ""
Write-Host "4. 清理旧的枚举类型..." -ForegroundColor Yellow
psql -U postgres -d postgres -c "DROP TYPE IF EXISTS ticket_status CASCADE;" 2>&1 | Out-Null
if ($LASTEXITCODE -ne 0) {
    Write-Host "ticket_status 枚举类型不存在" -ForegroundColor Gray
}

# 步骤 6: 运行初始迁移
Write-Host ""
Write-Host "5. 运行初始迁移..." -ForegroundColor Yellow
uv run alembic upgrade head

# 步骤 7: 验证
Write-Host ""
Write-Host "6. 验证迁移结果..." -ForegroundColor Yellow
uv run alembic current

Write-Host ""
Write-Host "=== 迁移重置完成 ===" -ForegroundColor Green
Write-Host ""
Write-Host "验证数据库结构：" -ForegroundColor Cyan
psql -U postgres -d postgres -c "SELECT enumlabel FROM pg_enum WHERE enumtypid = 'ticket_status'::regtype;"
psql -U postgres -d postgres -c "\dt"
