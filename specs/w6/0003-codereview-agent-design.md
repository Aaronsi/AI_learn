# Code Review Agent 设计文档

## 1. 概述

### 1.1 项目目标

构建一个专注于代码审查的 AI Agent，基于 `simple-agent` 框架。该 Agent 能够：

- 自动获取代码变更（通过 git/gh 命令）
- 阅读并理解完整文件上下文
- 提供专业、可操作的代码审查反馈
- 输出结构化的审查报告

### 1.4 设计原则（Thin Wrapper）

Code Review Agent 是 **thin wrapper**：仅提供工具调用与安全校验，不包含任何业务逻辑。

- **仅做工具层**：read/write/git/gh 工具注册与安全检查
- **业务逻辑全由 LLM 负责**：理解用户意图、选择工具、分析代码、生成审查输出
- **system prompt 是核心**：所有“如何 review”的流程与规则都写在提示词里

### 1.2 核心特性（由 LLM 在系统提示词中实现）

| 特性 | 描述 |
|------|------|
| 多种审查场景 | 支持 branch diff、commit diff、PR diff 等多种审查模式 |
| 上下文感知 | 不仅看 diff，还会阅读完整文件以理解上下文 |
| 精准反馈 | 仅标记确定的问题，避免误报 |
| 清晰分级 | 问题分为 Critical / Bug / Warning / Suggestion |

### 1.3 典型使用场景

```
用户: 帮我 review 当前 branch 新代码
用户: 帮我 review commit 13bad5 之后的代码
用户: 帮我 review pull request 12 的代码
用户: 帮我 review 最近 3 个 commits
用户: 帮我 review main 分支到当前分支的变更
```

---

## 2. 系统架构

### 2.1 基于 Simple-Agent 的架构

```
┌─────────────────────────────────────────────────────────────────┐
│                      Code Review Agent                          │
├─────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │ System       │  │ Tool         │  │ Session              │  │
│  │ Prompt       │  │ Registry     │  │ Manager              │  │
│  │ (prompts/)   │  │ (4 tools)    │  │                      │  │
│  └──────────────┘  └──────────────┘  └──────────────────────┘  │
├─────────────────────────────────────────────────────────────────┤
│                      Simple-Agent Core                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │ Agent Loop   │  │ LLM Client   │  │ Tool Executor        │  │
│  └──────────────┘  └──────────────┘  └──────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 工具集（Agent 仅提供工具注册与安全校验）

Code Review Agent 配备 4 个专用工具：

| 工具名称 | 用途 | 典型调用 |
|----------|------|----------|
| `read_file` | 读取文件内容 | 理解代码上下文、检查约定文件 |
| `write_file` | 写入文件内容 | 输出审查报告（可选） |
| `git_command` | 执行 git 命令 | 获取 diff、查看 commit、比较分支 |
| `gh_command` | 执行 gh 命令 | 查看 PR 详情、获取 PR diff |

---

## 3. 工具定义（仅实现工具与安全校验）

### 3.1 read_file

读取工作目录下指定文件的内容。LLM 决定何时调用与读取哪些文件。

```typescript
const readFileTool: Tool = {
  name: "read_file",
  description: "Read the contents of a file in the current working directory",
  parameters: {
    type: "object",
    properties: {
      path: {
        type: "string",
        description: "Relative path to the file to read"
      }
    },
    required: ["path"]
  },
  execute: async (args) => {
    const { path } = args as { path: string };
    try {
      const content = await fs.readFile(path, "utf-8");
      return { output: content };
    } catch (error) {
      return { output: "", error: `Failed to read file: ${error}` };
    }
  }
};
```

**使用示例：**
```json
{
  "name": "read_file",
  "arguments": { "path": "src/utils/auth.ts" }
}
```

### 3.2 write_file

写入内容到工作目录下的指定文件。LLM 决定是否输出报告文件以及写入内容。

```typescript
const writeFileTool: Tool = {
  name: "write_file",
  description: "Write content to a file in the current working directory",
  parameters: {
    type: "object",
    properties: {
      path: {
        type: "string",
        description: "Relative path to the file to write"
      },
      content: {
        type: "string",
        description: "Content to write to the file"
      }
    },
    required: ["path", "content"]
  },
  execute: async (args) => {
    const { path, content } = args as { path: string; content: string };
    try {
      await fs.writeFile(path, content, "utf-8");
      return { output: `Successfully wrote to ${path}` };
    } catch (error) {
      return { output: "", error: `Failed to write file: ${error}` };
    }
  }
};
```

**使用示例：**
```json
{
  "name": "write_file",
  "arguments": {
    "path": "review-report.md",
    "content": "# Code Review Report\n\n..."
  }
}
```

### 3.3 git_command

执行 git 命令，用于获取代码变更信息。LLM 决定使用哪些 git 命令与参数。

```typescript
const gitCommandTool: Tool = {
  name: "git_command",
  description: "Execute a git command. Supports: diff, show, log, status, branch, etc.",
  parameters: {
    type: "object",
    properties: {
      args: {
        type: "array",
        items: { type: "string" },
        description: "Arguments to pass to git command"
      }
    },
    required: ["args"]
  },
  execute: async (args) => {
    const { args: gitArgs } = args as { args: string[] };
    
    // 安全检查：禁止危险命令
    const dangerous = ["reset", "checkout", "clean", "revert", "push", "force"];
    const firstArg = gitArgs[0]?.toLowerCase();
    if (dangerous.some(d => firstArg?.includes(d))) {
      return { 
        output: "", 
        error: `Dangerous git command blocked: ${firstArg}` 
      };
    }
    
    try {
      const result = await execAsync(`git ${gitArgs.join(" ")}`);
      return { output: result.stdout };
    } catch (error) {
      return { output: "", error: `Git command failed: ${error}` };
    }
  }
};
```

**使用示例：**

| 场景 | 命令 |
|------|------|
| 查看未暂存变更 | `{ "args": ["diff"] }` |
| 查看已暂存变更 | `{ "args": ["diff", "--cached"] }` |
| 查看特定 commit | `{ "args": ["show", "abc123"] }` |
| 比较分支差异 | `{ "args": ["diff", "main...HEAD"] }` |
| 查看 commit 历史 | `{ "args": ["log", "--oneline", "-10"] }` |
| 查看某次 commit 之后的变更 | `{ "args": ["diff", "abc123..HEAD"] }` |
| 查看分支列表 | `{ "args": ["branch", "-a"] }` |
| 查看文件状态 | `{ "args": ["status", "--short"] }` |

### 3.4 gh_command

执行 GitHub CLI 命令，用于获取 Pull Request 信息。LLM 决定调用时机与参数。

```typescript
const ghCommandTool: Tool = {
  name: "gh_command",
  description: "Execute a GitHub CLI (gh) command. Primarily used for PR operations.",
  parameters: {
    type: "object",
    properties: {
      args: {
        type: "array",
        items: { type: "string" },
        description: "Arguments to pass to gh command"
      }
    },
    required: ["args"]
  },
  execute: async (args) => {
    const { args: ghArgs } = args as { args: string[] };
    
    // 安全检查：只允许只读操作
    const allowedCommands = ["pr", "issue", "repo"];
    const firstArg = ghArgs[0]?.toLowerCase();
    if (!allowedCommands.includes(firstArg)) {
      return { 
        output: "", 
        error: `Only pr/issue/repo commands are allowed, got: ${firstArg}` 
      };
    }
    
    // 禁止修改操作
    const readOnly = ["view", "diff", "list", "status", "checks"];
    const secondArg = ghArgs[1]?.toLowerCase();
    if (!readOnly.includes(secondArg)) {
      return { 
        output: "", 
        error: `Only read-only operations allowed: ${readOnly.join(", ")}` 
      };
    }
    
    try {
      const result = await execAsync(`gh ${ghArgs.join(" ")}`);
      return { output: result.stdout };
    } catch (error) {
      return { output: "", error: `gh command failed: ${error}` };
    }
  }
};
```

**使用示例：**

| 场景 | 命令 |
|------|------|
| 查看 PR 详情 | `{ "args": ["pr", "view", "12"] }` |
| 获取 PR diff | `{ "args": ["pr", "diff", "12"] }` |
| 列出所有 PR | `{ "args": ["pr", "list"] }` |
| 查看 PR 检查状态 | `{ "args": ["pr", "checks", "12"] }` |
| 查看当前 PR 状态 | `{ "args": ["pr", "status"] }` |

---

## 4. 审查流程（由 LLM 在 system prompt 中执行）

### 4.1 整体流程

```
┌─────────────────────────────────────────────────────────────────┐
│                     Code Review Flow                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. 解析用户请求                                                 │
│     ↓                                                           │
│  2. 确定审查范围 (branch/commit/PR)                             │
│     ↓                                                           │
│  3. 获取 diff (git_command / gh_command)                        │
│     ↓                                                           │
│  4. 读取完整文件上下文 (read_file)                               │
│     ↓                                                           │
│  5. 分析代码变更                                                 │
│     ↓                                                           │
│  6. 输出审查结果                                                 │
│     ↓                                                           │
│  7. (可选) 写入报告文件 (write_file)                            │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 4.2 请求解析逻辑（LLM 推理规则，不在代码中实现）

LLM 需要根据用户输入智能判断审查类型（系统提示词提供规则与示例，运行时代码不做解析）：

| 用户输入模式 | 判断条件 | 执行命令 |
|-------------|----------|----------|
| 无参数/当前变更 | 默认 | `git diff` + `git diff --cached` |
| Commit SHA | 40字符 或 7字符 hash | `git show <sha>` |
| Commit 范围 | `abc123..HEAD` 格式 | `git diff <range>` |
| 分支名 | 存在的分支名 | `git diff <branch>...HEAD` |
| PR 编号 | 纯数字 | `gh pr view <num>` + `gh pr diff <num>` |
| PR URL | 包含 github.com | 提取编号后同上 |
| "最近 N 个 commits" | 自然语言 | `git log -N` 然后逐个 show |

### 4.3 上下文收集策略（LLM 调用工具完成）

**关键原则：Diff 不够，必须读完整文件。**

LLM 根据 diff 中的文件列表逐个调用 `read_file`，必要时再读取约定文件：

- 从 diff 输出中提取变更文件
- 读取每个变更文件的完整内容
- 视情况读取约定文件（`CONVENTIONS.md`、`AGENTS.md`、`.editorconfig` 等）

---

## 5. 审查标准（写入 system prompt，由 LLM 执行）

### 5.1 审查优先级

```
Priority 1: Bugs (最高优先级)
├── 逻辑错误、条件判断错误
├── 边界情况：null/undefined/empty
├── 错误处理：swallow、未捕获、类型不匹配
├── 安全问题：注入、认证绕过、数据泄露
└── 并发问题：竞态条件

Priority 2: Structure (结构问题)
├── 是否遵循现有模式
├── 是否使用了已有抽象
└── 过度嵌套

Priority 3: Performance (性能问题)
├── O(n²) 在大数据集上
├── N+1 查询
└── 热路径上的阻塞 I/O
```

### 5.2 严重等级定义

| 等级 | 定义 | 示例 |
|------|------|------|
| **Critical** | 会导致系统故障、数据丢失或安全漏洞 | SQL 注入、认证绕过、数据损坏 |
| **Bug** | 特定条件下的错误行为 | 边界条件未处理、类型错误 |
| **Warning** | 潜在问题或代码异味 | 过度嵌套、可能的空指针 |
| **Suggestion** | 改进建议，非缺陷 | 可读性改进、更好的命名 |

### 5.3 标记前的验证清单（LLM 自检规则）

在标记问题之前，LLM 必须确认：

- [ ] 这确实是本次变更引入的问题（不是既有代码）
- [ ] 我有足够的上下文来确定这是个 bug（已读完整文件）
- [ ] 这不是假设的问题（有具体的触发场景）
- [ ] 如果是风格问题，确认违反了项目约定（不是个人偏好）

---

## 6. 输出格式（写入 system prompt，由 LLM 生成）

### 6.1 审查报告结构

```markdown
**Summary**
- [Critical] 简短描述问题 1
- [Bug] 简短描述问题 2

**Details**

`src/auth/login.ts:42` — 未处理的空值
用户 token 可能为 undefined，但代码直接访问了 token.userId，
当用户未登录时会导致运行时错误。

建议添加空值检查：
```typescript
if (!token) {
  throw new AuthError("User not authenticated");
}
```

`src/api/users.ts:128` — N+1 查询
循环中每次都执行数据库查询，当用户数量增大时会严重影响性能。
建议使用批量查询替代。
```

### 6.2 无问题时的输出

```
代码变更审查完成，未发现问题。

变更涉及 3 个文件：
- `src/utils/format.ts` - 新增日期格式化函数
- `src/components/DatePicker.tsx` - 使用新格式化函数
- `tests/format.test.ts` - 添加对应测试
```

---

## 7. 项目结构（仅工具与提示词，无业务逻辑模块）

```
w6/codereview-agent/
├── package.json
├── tsconfig.json
├── src/
│   ├── index.ts              # 入口文件
│   ├── tools/
│   │   ├── index.ts          # 工具导出
│   │   ├── read-file.ts      # 读文件工具
│   │   ├── write-file.ts     # 写文件工具
│   │   ├── git-command.ts    # git 命令工具
│   │   └── gh-command.ts     # gh 命令工具
│   └── cli.ts                # CLI 入口
├── prompts/
│   └── system.md             # 系统提示词
└── examples/
    └── review-branch.ts      # 使用示例
```

---

## 8. 使用示例（只传递用户请求，不解析意图）

### 8.1 CLI 使用（不做参数解析）

```bash
# 直接将用户请求传给 Agent，不做业务解析
npx codereview-agent "帮我 review 当前 branch 新代码"
npx codereview-agent "帮我 review commit abc123 之后的代码"
npx codereview-agent "帮我 review pull request 12 的代码"
```

### 8.2 编程使用（不做业务解析）

```typescript
import { SimpleAgent } from "simple-agent";
import { 
  readFileTool, 
  writeFileTool, 
  gitCommandTool, 
  ghCommandTool 
} from "codereview-agent/tools";
import systemPrompt from "codereview-agent/prompts/system.md";

// 创建 Agent
const agent = new SimpleAgent({
  model: "claude-sonnet-4-20250514",
  systemPrompt,
});

// 注册工具
agent.addTools([
  readFileTool,
  writeFileTool,
  gitCommandTool,
  ghCommandTool,
]);

// 创建会话并运行
const session = agent.createSession();
const response = await agent.run(
  session.id,
  "帮我 review 当前 branch 新代码"
);

console.log(response);
```

---

## 9. 安全考量

### 9.1 命令执行安全

**Git 命令白名单/黑名单：**

```typescript
// 禁止的危险操作
const BLOCKED_GIT_COMMANDS = [
  "reset",
  "checkout",  // checkout 文件会丢弃修改
  "clean",
  "revert",
  "push",
  "pull",
  "merge",
  "rebase",
  "cherry-pick",
  "--force",
  "-f",
];
```

**GH 命令限制：**

```typescript
// 只允许只读操作
const ALLOWED_GH_OPERATIONS = {
  pr: ["view", "diff", "list", "status", "checks"],
  issue: ["view", "list"],
  repo: ["view"],
};
```

### 9.2 文件系统安全

```typescript
// 限制文件操作范围
function validatePath(path: string): boolean {
  // 1. 禁止绝对路径
  if (path.startsWith("/") || path.match(/^[A-Z]:/)) {
    return false;
  }
  
  // 2. 禁止路径穿越
  if (path.includes("..")) {
    return false;
  }
  
  // 3. 禁止访问敏感文件
  const sensitive = [".env", ".git/config", "id_rsa", "secrets"];
  if (sensitive.some(s => path.includes(s))) {
    return false;
  }
  
  return true;
}
```

---

## 10. 后续扩展（仅限提示词能力与工具扩展）

### 10.1 计划中的功能

| 功能 | 优先级 | 描述 |
|------|--------|------|
| 增量审查 | P1 | 通过提示词引导 LLM 只审查增量部分 |
| 审查历史 | P2 | 通过外部存储/上下文注入提供历史，LLM 负责解读 |
| 自定义规则 | P2 | 通过提示词/上下文注入项目规则 |
| CI 集成 | P2 | 作为运行入口集成到 CI，业务逻辑仍在 LLM |
| 多语言支持 | P3 | 提示词中加入语言特定检查点 |

### 10.2 未来工具扩展（扩展工具，不引入业务逻辑）

```typescript
// 可能添加的工具
const futureTols = [
  "grep_search",    // 搜索代码模式
  "run_tests",      // 运行相关测试
  "check_types",    // 类型检查
  "lint_file",      // 运行 linter
];
```

---

## 11. 参考资料

- [Simple Agent 设计文档](./0001-simple-agent-design.md)
- [OpenCode 系统提示词](../prompts/codex.txt)
- [OpenCode 审查模板](../prompts/review.txt)
- [GitHub CLI 文档](https://cli.github.com/manual/)

