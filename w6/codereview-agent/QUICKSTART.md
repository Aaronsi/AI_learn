# Quick Start Guide - Code Review Agent

## 1. 安装

```bash
cd w6/codereview-agent
npm install
npm run build
```

## 2. 配置 API Key

```bash
# Windows PowerShell
$env:DEEPSEEK_API_KEY="your-api-key"

# Linux/Mac
export DEEPSEEK_API_KEY="your-api-key"
```

## 3. 使用示例

### 审查未提交的改动
```bash
npm run cli "帮我 review 最近的改动"
```

### 审查当前 branch
```bash
npm run cli "帮我 review 当前 branch 相对于 main 的新代码"
```

### 审查特定 commit 之后的代码
```bash
npm run cli "帮我 review commit abc123 之后的代码"
```

### 审查特定文件
```bash
npm run cli "帮我 review src/index.ts 文件"
```

### 安全审查
```bash
npm run cli "检查 src/ 目录是否有安全漏洞"
```

### 性能审查
```bash
npm run cli "检查代码是否有性能问题"
```

## 4. 编程使用

```typescript
import { runCodeReview } from "./src/index";

const response = await runCodeReview("帮我 review 最近的改动");
console.log(response);
```

## 5. 常见问题

### Q: Agent 卡住不动？
A: 检查 API key 是否正确设置

### Q: 提示 "Failed to load system prompt"？
A: 确保在 `w6/codereview-agent` 目录下运行，或检查 `prompts/system.md` 是否存在

### Q: Git 命令被阻止？
A: Agent 只允许只读命令（diff, show, log 等），危险命令（push, reset 等）会被拦截

### Q: 如何审查 PR？
A: 需要先安装并认证 GitHub CLI：
```bash
# 安装 gh
# Windows: winget install GitHub.cli
# Mac: brew install gh

# 认证
gh auth login

# 审查 PR
npm run cli "帮我 review pull request 12"
```

## 6. 输出示例

```
🔍 Code Review Agent
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Request: 帮我 review 最近的改动

**Summary**
- [Bug] 空值检查缺失可能导致运行时错误
- [Warning] 可能的性能问题

**Details**

`src/auth.ts:42` — 空值检查缺失
用户 token 可能为 undefined，但代码直接访问了 token.userId。
建议添加空值检查：
```typescript
if (!token) {
  throw new AuthError("User not authenticated");
}
```

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ Review completed
```

## 7. 下一步

- 查看 [README.md](./README.md) 了解详细信息
- 查看 [TEST_RESULTS.md](./TEST_RESULTS.md) 了解测试结果
- 查看 [examples/](./examples/) 了解更多使用示例
- 查看 [IMPLEMENTATION_SUMMARY.md](./IMPLEMENTATION_SUMMARY.md) 了解实现细节

