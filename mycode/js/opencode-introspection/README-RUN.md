# 如何在 mycode/js/opencode-introspection 目录下运行 opencode

## 方式 1: 全局安装 opencode（推荐）

如果你还没有全局安装 opencode，可以使用以下命令：

```bash
# 使用 npm
npm i -g opencode-ai@latest

# 或使用 bun
bun add -g opencode-ai@latest

# 或使用 pnpm
pnpm add -g opencode-ai@latest
```

安装后，在 `mycode/js/opencode-introspection` 目录下直接运行：

```bash
opencode
```

## 方式 2: 从源码运行（开发模式）

如果你想从本地源码运行 opencode：

### 步骤 1: 安装依赖

```bash
cd vendors/opencode
bun install
```

### 步骤 2: 运行 opencode

```bash
# 从 vendors/opencode 目录运行
cd vendors/opencode
bun run --cwd packages/opencode --conditions=browser src/index.ts

# 或者使用 dev 脚本
bun run dev
```

### 步骤 3: 在项目目录下运行

如果你想在 `mycode/js/opencode-introspection` 目录下运行，可以创建一个脚本或使用相对路径：

```bash
# 从 mycode/js/opencode-introspection 目录运行
cd vendors/opencode/packages/opencode
bun run --conditions=browser src/index.ts
```

## 方式 3: 使用 npx（临时运行）

如果你不想全局安装，可以使用 npx：

```bash
npx opencode-ai@latest
```

## 方式 4: 创建快捷脚本

在 `mycode/js/opencode-introspection` 目录下创建一个脚本文件：

### Windows (run-opencode.ps1)

```powershell
# run-opencode.ps1
Set-Location vendors/opencode/packages/opencode
bun run --conditions=browser src/index.ts
```

然后运行：
```powershell
.\run-opencode.ps1
```

### Linux/macOS (run-opencode.sh)

```bash
#!/bin/bash
# run-opencode.sh
cd vendors/opencode/packages/opencode
bun run --conditions=browser src/index.ts
```

然后运行：
```bash
chmod +x run-opencode.sh
./run-opencode.sh
```

## 注意事项

1. **确保 bun 已安装**: opencode 使用 bun 作为运行时，需要先安装 bun
   ```bash
   # 安装 bun
   curl -fsSL https://bun.sh/install | bash
   ```

2. **配置文件位置**: opencode 会在当前目录查找 `opencode.json` 配置文件
   - 你的配置文件位于: `mycode/js/opencode-introspection/opencode.json`
   - Plugin 路径: `plugins/log-conversation.ts`

3. **日志输出**: 日志文件会保存在 `logs/` 目录下
   - 格式: `session-{sessionID}-{conversationID}.jsonl`

## 验证安装

运行以下命令验证 opencode 是否可用：

```bash
opencode --version
```

如果显示版本号，说明安装成功。

