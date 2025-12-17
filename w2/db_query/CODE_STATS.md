# 代码统计工具

## 安装 tokei（代码统计工具）

### 方法 1：使用 Scoop（推荐）

```powershell
# 安装 Scoop（如果还没有）
Set-ExecutionPolicy RemoteSigned -Scope CurrentUser
irm get.scoop.sh | iex

# 安装 tokei
scoop install tokei
```

### 方法 2：使用 Chocolatey

```powershell
# 安装 Chocolatey（如果还没有）
Set-ExecutionPolicy Bypass -Scope Process -Force; [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))

# 安装 tokei
choco install tokei
```

### 方法 3：使用 winget

```powershell
winget install XAMPPRocky.tokei
```

### 方法 4：手动安装

1. 访问 https://github.com/XAMPPRocky/tokei/releases
2. 下载 Windows 版本（tokei-x86_64-pc-windows-msvc.zip）
3. 解压并将 `tokei.exe` 添加到 PATH 环境变量

## 使用 tokei

```bash
# 统计当前目录代码
tokei .

# 统计特定目录
tokei backend/

# 排除某些文件/目录
tokei . --exclude '*.pyc' --exclude '__pycache__'

# 按文件类型统计
tokei --type Python
```

## PowerShell 替代方案

如果不想安装 tokei，可以使用 PowerShell 命令统计代码：

### 统计 Python 代码行数

```powershell
# 统计所有 .py 文件的行数
Get-ChildItem -Recurse -Filter *.py | Get-Content | Measure-Object -Line

# 统计特定目录
Get-ChildItem -Path backend -Recurse -Filter *.py | Get-Content | Measure-Object -Line

# 排除 __pycache__ 目录
Get-ChildItem -Recurse -Filter *.py -Exclude __pycache__ | Get-Content | Measure-Object -Line
```

### 统计所有代码文件

```powershell
# 统计多种文件类型
$extensions = @('*.py', '*.ts', '*.tsx', '*.js', '*.jsx', '*.json', '*.md')
$totalLines = 0
foreach ($ext in $extensions) {
    $files = Get-ChildItem -Recurse -Filter $ext -Exclude node_modules,__pycache__,.venv
    $lines = $files | Get-Content | Measure-Object -Line
    Write-Host "$ext : $($lines.Lines) lines"
    $totalLines += $lines.Lines
}
Write-Host "Total: $totalLines lines"
```

## 快速统计脚本

创建一个 PowerShell 脚本 `count-lines.ps1`：

```powershell
# 统计代码行数
$extensions = @('*.py', '*.ts', '*.tsx', '*.js', '*.jsx')
$excludeDirs = @('node_modules', '__pycache__', '.venv', '.git')

$totalLines = 0
$fileCount = 0

foreach ($ext in $extensions) {
    $files = Get-ChildItem -Recurse -Filter $ext | Where-Object {
        $exclude = $false
        foreach ($dir in $excludeDirs) {
            if ($_.FullName -like "*\$dir\*") {
                $exclude = $true
                break
            }
        }
        return -not $exclude
    }
    
    foreach ($file in $files) {
        $lines = (Get-Content $file.FullName | Measure-Object -Line).Lines
        $totalLines += $lines
        $fileCount++
    }
}

Write-Host "Files: $fileCount"
Write-Host "Total Lines: $totalLines"
```

运行：
```powershell
.\count-lines.ps1
```


