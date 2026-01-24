# run-opencode.ps1
# 在 mycode/js/opencode-introspection 目录下运行 opencode

# 检查是否全局安装了 opencode
$opencodeCmd = Get-Command opencode -ErrorAction SilentlyContinue

if ($opencodeCmd) {
    Write-Host "使用全局安装的 opencode..." -ForegroundColor Green
    opencode $args
} else {
    Write-Host "未找到全局安装的 opencode，尝试从源码运行..." -ForegroundColor Yellow
    
    # 检查 bun 是否安装
    $bunCmd = Get-Command bun -ErrorAction SilentlyContinue
    if (-not $bunCmd) {
        Write-Host "错误: 未找到 bun。请先安装 bun:" -ForegroundColor Red
        Write-Host "  curl -fsSL https://bun.sh/install | bash" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "或者全局安装 opencode:" -ForegroundColor Yellow
        Write-Host "  npm i -g opencode-ai@latest" -ForegroundColor Yellow
        exit 1
    }
    
    # 检查依赖是否安装
    $nodeModulesPath = Join-Path $PSScriptRoot "vendors\opencode\node_modules"
    if (-not (Test-Path $nodeModulesPath)) {
        Write-Host "正在安装依赖..." -ForegroundColor Yellow
        Set-Location (Join-Path $PSScriptRoot "vendors\opencode")
        bun install
        if ($LASTEXITCODE -ne 0) {
            Write-Host "依赖安装失败！" -ForegroundColor Red
            exit 1
        }
        Set-Location $PSScriptRoot
    }
    
    # 从源码运行
    Write-Host "从源码运行 opencode..." -ForegroundColor Green
    Set-Location (Join-Path $PSScriptRoot "vendors\opencode\packages\opencode")
    bun run --conditions=browser src/index.ts $args
    Set-Location $PSScriptRoot
}

