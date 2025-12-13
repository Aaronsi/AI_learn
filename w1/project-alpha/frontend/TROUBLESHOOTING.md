# 前端故障排除指南

## 'vite' 不是内部或外部命令

### 问题描述

运行 `npm run dev` 或直接运行 `vite` 时，出现以下错误：

```
'vite' 不是内部或外部命令，也不是可运行的程序或批处理文件。
```

### 原因

这通常意味着：
1. **依赖未安装**：`node_modules` 目录不存在
2. **直接运行 vite**：应该使用 `npm run dev` 而不是直接运行 `vite`

### 解决方案

#### 1. 安装依赖（如果未安装）

```bash
npm install
```

**Windows PowerShell 用户**：如果遇到执行策略错误，使用 CMD：

```cmd
cmd
npm install
```

#### 2. 使用 npm 脚本运行

**不要直接运行 `vite`**，应该使用：

```bash
npm run dev
```

或者使用 CMD（如果 PowerShell 有问题）：

```cmd
cmd
npm run dev
```

#### 3. 验证安装

检查 `node_modules` 目录是否存在：

```bash
# PowerShell
Test-Path node_modules

# CMD/Bash
dir node_modules
```

如果不存在，运行 `npm install`。

## PowerShell 执行策略错误

### 问题描述

在 Windows PowerShell 中运行 `npm` 命令时，可能遇到以下错误：

```
npm : 无法加载文件 F:\Program Files\nodejs\npm.ps1，因为在此系统上禁止运行脚本。
有关详细信息，请参阅 https:/go.microsoft.com/fwlink/?LinkID=135170 中的 about_Execution_Policies。
```

### 原因

这是 Windows PowerShell 的安全策略，默认禁止运行未签名的脚本。

### 解决方案

#### 方案 1：使用 CMD（推荐）

最简单的方法是使用 Windows CMD 而不是 PowerShell：

```cmd
# 打开 CMD（不是 PowerShell）
cd frontend
npm install
npm run dev
```

#### 方案 2：临时绕过执行策略

仅对当前 PowerShell 会话生效：

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process
npm run dev
```

#### 方案 3：修改当前用户的执行策略

永久修改（推荐，仅影响当前用户）：

```powershell
# 以管理员身份运行 PowerShell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

然后重新打开 PowerShell 窗口。

#### 方案 4：直接使用 node

绕过 npm 脚本，直接调用：

```powershell
node node_modules/.bin/vite
```

#### 方案 5：使用 npx

```powershell
npx vite
```

### 验证执行策略

查看当前执行策略：

```powershell
Get-ExecutionPolicy
```

常见值：
- `Restricted`：禁止所有脚本（默认）
- `RemoteSigned`：允许本地脚本，远程脚本需要签名（推荐）
- `Unrestricted`：允许所有脚本（不推荐）

## 其他常见问题

### 端口已被占用

如果 `5173` 端口已被占用，Vite 会自动尝试下一个端口（如 `5174`）。查看终端输出确认实际端口。

### 依赖安装失败

```bash
# 清除缓存并重新安装
rm -rf node_modules package-lock.json
npm install
```

### 构建失败

```bash
# 清除构建缓存
rm -rf dist .vite
npm run build
```

### CORS 错误

确保后端 `ALLOWED_ORIGINS` 环境变量包含前端地址（例如：`http://localhost:5173`）。

### 环境变量不生效

- 确保 `.env` 文件在 `frontend/` 目录下
- 环境变量必须以 `VITE_` 开头
- 修改 `.env` 后需要重启开发服务器
