# OpenCode Prompt 架构深度解析

本文档详细介绍 OpenCode 中 System Prompt 和工具调用相关的 Prompt 架构设计。

---

## 目录

1. [整体架构概览](#1-整体架构概览)
2. [System Prompt 层级结构](#2-system-prompt-层级结构)
3. [模型特定 Prompt 变体](#3-模型特定-prompt-变体)
4. [工具定义与描述系统](#4-工具定义与描述系统)
5. [动态 Prompt 注入机制](#5-动态-prompt-注入机制)
6. [Agent 系统与子任务](#6-agent-系统与子任务)
7. [消息处理流程](#7-消息处理流程)

---

## 1. 整体架构概览

OpenCode 的 Prompt 系统采用**分层组合**的设计模式，将不同职责的 Prompt 组件组合成完整的上下文。

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        LLM 最终接收的消息结构                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌────────────────────────────────────────────────────────────────────┐    │
│  │                     System Messages 层                              │    │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌────────────┐   │    │
│  │  │ Header     │  │ Provider   │  │Environment │  │ Custom     │   │    │
│  │  │ (Anthropic)│  │ Prompt     │  │ Info       │  │ Rules      │   │    │
│  │  └────────────┘  └────────────┘  └────────────┘  └────────────┘   │    │
│  └────────────────────────────────────────────────────────────────────┘    │
│                                                                             │
│  ┌────────────────────────────────────────────────────────────────────┐    │
│  │                     Tools 定义层                                    │    │
│  │  ┌─────────────────────────────────────────────────────────────┐   │    │
│  │  │  Tool Schema (name, description, parameters)                │   │    │
│  │  │  - Read, Edit, Write, Bash, Glob, Grep, Task, ...          │   │    │
│  │  │  - MCP 外部工具                                              │   │    │
│  │  │  - 插件自定义工具                                            │   │    │
│  │  └─────────────────────────────────────────────────────────────┘   │    │
│  └────────────────────────────────────────────────────────────────────┘    │
│                                                                             │
│  ┌────────────────────────────────────────────────────────────────────┐    │
│  │                     Conversation History 层                        │    │
│  │  ┌─────────────────────────────────────────────────────────────┐   │    │
│  │  │  User Messages + Assistant Messages + Tool Results          │   │    │
│  │  │  (可能包含 <system-reminder> 动态注入)                       │   │    │
│  │  └─────────────────────────────────────────────────────────────┘   │    │
│  └────────────────────────────────────────────────────────────────────┘    │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 核心文件位置

```
packages/opencode/src/session/
├── prompt.ts          # 主 Prompt 处理逻辑
├── system.ts          # System Prompt 构建
├── prompt/            # Prompt 模板文件
│   ├── anthropic.txt  # Claude 模型专用
│   ├── codex.txt      # GPT-5/Codex 模型专用
│   ├── gemini.txt     # Gemini 模型专用
│   ├── beast.txt      # GPT-4/O1/O3 模型专用
│   ├── qwen.txt       # Qwen/其他模型
│   ├── plan.txt       # Plan 模式提醒
│   └── max-steps.txt  # 最大步数限制提醒
```

---

## 2. System Prompt 层级结构

System Prompt 由 `SystemPrompt` 命名空间管理（`system.ts`），分为以下层级：

### 2.1 Header 层（仅 Anthropic）

```typescript
export function header(providerID: string) {
  if (providerID.includes("anthropic")) return [PROMPT_ANTHROPIC_SPOOF.trim()]
  return []
}
```

**作用**：为 Anthropic 模型添加身份声明
**内容**：`"You are Claude Code, Anthropic's official CLI for Claude."`

### 2.2 Provider Prompt 层

根据模型类型选择不同的基础 Prompt：

```typescript
export function provider(model: Provider.Model) {
  if (model.api.id.includes("gpt-5")) return [PROMPT_CODEX]
  if (model.api.id.includes("gpt-") || model.api.id.includes("o1") || model.api.id.includes("o3"))
    return [PROMPT_BEAST]
  if (model.api.id.includes("gemini-")) return [PROMPT_GEMINI]
  if (model.api.id.includes("claude")) return [PROMPT_ANTHROPIC]
  return [PROMPT_ANTHROPIC_WITHOUT_TODO]  // qwen.txt 作为默认
}
```

```
┌─────────────────────────────────────────────────────────────────┐
│                    模型 → Prompt 映射关系                        │
├─────────────────────────────────────────────────────────────────┤
│  Model ID 包含      │     使用的 Prompt 文件                    │
├─────────────────────┼───────────────────────────────────────────┤
│  "gpt-5"            │     codex.txt (最详细的指令集)            │
│  "gpt-", "o1", "o3" │     beast.txt (自主Agent风格)            │
│  "gemini-"          │     gemini.txt (简洁指令风格)            │
│  "claude"           │     anthropic.txt (平衡风格)             │
│  其他               │     qwen.txt (无TodoWrite工具说明)       │
└─────────────────────────────────────────────────────────────────┘
```

### 2.3 Environment 信息层

```typescript
export async function environment() {
  return [
    [
      `Here is some useful information about the environment you are running in:`,
      `<env>`,
      `  Working directory: ${Instance.directory}`,
      `  Is directory a git repo: ${project.vcs === "git" ? "yes" : "no"}`,
      `  Platform: ${process.platform}`,
      `  Today's date: ${new Date().toDateString()}`,
      `</env>`,
    ].join("\n"),
  ]
}
```

**作用**：提供运行时环境信息，让 LLM 了解当前上下文

### 2.4 Custom Rules 层

从以下位置加载自定义规则：

```
本地规则文件 (按优先级):
├── AGENTS.md
├── CLAUDE.md  
└── CONTEXT.md (已弃用)

全局规则文件:
├── ~/.config/opencode/AGENTS.md
└── ~/.claude/CLAUDE.md (如未禁用)

配置指定的额外指令:
└── config.instructions 数组中的文件/URL
```

---

## 3. 模型特定 Prompt 变体

### 3.1 anthropic.txt (Claude 专用)

**特点**：平衡的指令风格，强调专业性和简洁性

**主要章节**：

```
# 身份声明
"You are OpenCode, the best coding agent on the planet."

# 核心行为约束
- 不生成恶意 URL
- 帮助信息指引 (ctrl+p, GitHub issues)
- 使用 WebFetch 查询 OpenCode 文档

# 风格指南
- 不使用 emoji（除非明确要求）
- 简洁的 CLI 输出
- GitHub-flavored Markdown

# 任务管理
- TodoWrite 工具使用指南
- 完整的使用示例

# 工具使用策略
- 偏好 Task 工具进行文件搜索
- 使用专用工具而非 bash
- 并行工具调用

# 代码引用格式
"file_path:line_number"
```

### 3.2 codex.txt (GPT-5/Codex)

**特点**：最详细的指令集，包含大量格式化和行为约束

**独特内容**：

```
# 编辑约束
- 默认使用 ASCII
- 谨慎添加注释
- 优先使用 apply_patch

# Git 工作区卫生
- 永不回滚用户的更改
- 禁止 git reset --hard
- 禁止强制推送

# 前端任务指南
- 字体选择
- 色彩和主题
- 动画效果
- 背景设计

# 最终答案格式
- 标题使用 **...** 包裹
- 列表使用 - 
- 代码用 backticks
```

### 3.3 beast.txt (GPT-4/O1/O3 - "自主Beast模式")

**特点**：强调自主性和深度思考

**关键指令**：

```
"You MUST iterate and keep going until the problem is solved."

"You have everything you need to resolve this problem. 
I want you to fully solve this autonomously before coming back to me."

"THE PROBLEM CAN NOT BE SOLVED WITHOUT EXTENSIVE INTERNET RESEARCH."

# 工作流程
1. Fetch URLs
2. Deeply Understand the Problem  
3. Codebase Investigation
4. Internet Research (使用 WebFetch 搜索 Google)
5. Develop a Detailed Plan
6. Making Code Changes
7. Debugging
8. Testing

# 记忆系统
使用 .github/instructions/memory.instruction.md 存储用户偏好
```

### 3.4 gemini.txt (Gemini)

**特点**：最简洁直接的指令风格

**核心特征**：

```
# 极简响应示例
user: 1 + 2
model: 3

user: is 13 a prime number?
model: true

# 安全规则
- 解释关键命令的影响
- 安全第一原则

# 工具使用
- 使用绝对路径
- 并行执行独立工具调用
- 后台进程使用 &
```

### 3.5 qwen.txt (Qwen/通用)

**特点**：精简版 anthropic.txt，移除了 TodoWrite 工具相关内容

```
# 核心差异
- 无任务管理部分
- 无 TodoWrite 使用示例
- 更简短的工具使用策略
```

---

## 4. 工具定义与描述系统

### 4.1 工具定义结构

```typescript
// tool/tool.ts
export interface Info<Parameters extends z.ZodType, Metadata> {
  id: string
  init: (ctx?: InitContext) => Promise<{
    description: string           // 工具描述（给 LLM 看）
    parameters: Parameters        // Zod schema 定义参数
    execute(args, ctx): Promise<{
      title: string
      metadata: Metadata
      output: string
      attachments?: FilePart[]
    }>
  }>
}
```

### 4.2 工具描述文件 (.txt)

每个工具都有配套的 `.txt` 文件提供详细描述：

```
packages/opencode/src/tool/
├── read.ts    →    read.txt
├── edit.ts    →    edit.txt
├── bash.ts    →    bash.txt
├── task.ts    →    task.txt
└── ...
```

### 4.3 核心工具描述示例

#### Read 工具

```
Reads a file from the local filesystem.

Usage:
- The filePath parameter must be an absolute path
- By default reads up to 2000 lines from the beginning
- Lines longer than 2000 chars will be truncated
- Results use cat -n format (line numbers starting at 1)
- Can read image files
```

#### Edit 工具

```
Performs exact string replacements in files.

Usage:
- MUST use Read tool at least once before editing
- Preserve exact indentation (tabs/spaces)
- ALWAYS prefer editing existing files
- oldString not found → error
- oldString found multiple times → error (need more context)
- Use replaceAll for renaming across file
```

#### Bash 工具

```
Executes bash command in persistent shell session.

IMPORTANT: DO NOT use for file operations (reading, writing, 
editing, searching) - use specialized tools instead.

# 使用专用工具代替 bash：
- File search: Use Glob (NOT find or ls)
- Content search: Use Grep (NOT grep or rg)  
- Read files: Use Read (NOT cat/head/tail)
- Edit files: Use Edit (NOT sed/awk)
- Write files: Use Write (NOT echo >/cat <<EOF)

# Git 安全协议
- NEVER update git config
- NEVER run destructive commands unless requested
- NEVER skip hooks
- Avoid git commit --amend (除非满足条件)
```

#### Task 工具 (子Agent)

```
Launch a new agent to handle complex, multistep tasks autonomously.

Available agent types and the tools they have access to:
{agents}  ← 动态注入可用 agent 列表

When to use:
- Execute custom slash commands
- Complex multistep tasks

When NOT to use:
- Reading specific file path → use Read/Glob
- Searching specific class → use Glob
- Searching within 2-3 files → use Read

Usage notes:
1. Launch multiple agents concurrently when possible
2. Agent result is NOT visible to user - summarize it
3. Each invocation is stateless unless providing session_id
```

### 4.4 工具注册流程

```typescript
// tool/registry.ts
export async function tools(model, agent) {
  const tools = await all()
  
  return tools
    .filter((t) => {
      // 根据模型类型筛选工具
      // gpt-* 使用 apply_patch，其他使用 edit/write
      const usePatch = model.modelID.includes("gpt-") && !model.modelID.includes("gpt-4")
      if (t.id === "apply_patch") return usePatch
      if (t.id === "edit" || t.id === "write") return !usePatch
      return true
    })
    .map(async (t) => ({
      id: t.id,
      ...(await t.init({ agent })),
    }))
}
```

```
┌─────────────────────────────────────────────────────────────────┐
│                    工具筛选逻辑                                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  GPT-5/GPT-3.5 系列:                                           │
│  ├── ✓ apply_patch (Codex 风格编辑)                            │
│  ├── ✗ edit                                                    │
│  └── ✗ write                                                   │
│                                                                 │
│  其他模型 (Claude, GPT-4, Gemini, etc.):                       │
│  ├── ✗ apply_patch                                             │
│  ├── ✓ edit                                                    │
│  └── ✓ write                                                   │
│                                                                 │
│  特殊工具:                                                     │
│  ├── codesearch/websearch: 仅 opencode provider 或启用 EXA    │
│  ├── lsp: 需要 OPENCODE_EXPERIMENTAL_LSP_TOOL                  │
│  ├── batch: 需要 config.experimental.batch_tool                │
│  └── plan_exit/plan_enter: 需要 PLAN_MODE && CLI 客户端       │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 5. 动态 Prompt 注入机制

### 5.1 System Reminder 标签

OpenCode 使用 `<system-reminder>` 标签在对话过程中动态注入系统提醒：

```typescript
// 在用户消息中包裹系统提醒
if (step > 1 && lastFinished) {
  for (const msg of sessionMessages) {
    if (msg.info.role !== "user") continue
    part.text = [
      "<system-reminder>",
      "The user sent the following message:",
      part.text,
      "",
      "Please address this message and continue with your tasks.",
      "</system-reminder>",
    ].join("\n")
  }
}
```

### 5.2 Plan Mode 提醒

当进入 Plan 模式时，注入详细的工作流程指导：

```
<system-reminder>
# Plan Mode - System Reminder

CRITICAL: Plan mode ACTIVE - you are in READ-ONLY phase.

## Plan Workflow

### Phase 1: Initial Understanding
Launch up to 3 explore agents IN PARALLEL...

### Phase 2: Design  
Launch general agent(s) to design the implementation...

### Phase 3: Review
Read critical files, ensure alignment with user intentions...

### Phase 4: Final Plan
Write final plan to the plan file...

### Phase 5: Call plan_exit tool
</system-reminder>
```

### 5.3 Max Steps 限制

当达到最大步数时，强制停止工具调用：

```
// max-steps.txt
CRITICAL - MAXIMUM STEPS REACHED

Tools are disabled until next user input. Respond with text only.

STRICT REQUIREMENTS:
1. Do NOT make any tool calls
2. MUST provide text response summarizing work done
3. This constraint overrides ALL other instructions

Response must include:
- Statement that maximum steps reached
- Summary of accomplishments  
- List of remaining tasks
- Recommendations for next steps
```

### 5.4 Build Mode 切换

从 Plan 切换到 Build 模式时的提醒：

```
<system-reminder>
Your operational mode has changed from plan to build.
You are no longer in read-only mode.
You are permitted to make file changes, run shell commands, 
and utilize your arsenal of tools as needed.
</system-reminder>
```

---

## 6. Agent 系统与子任务

### 6.1 Agent 类型

OpenCode 支持多种 Agent 类型，每种有不同的工具集和行为：

```
┌─────────────────────────────────────────────────────────────────┐
│                    Agent 类型概览                               │
├─────────────────────────────────────────────────────────────────┤
│  Agent Name  │  描述                    │  工具集               │
├──────────────┼──────────────────────────┼───────────────────────┤
│  build       │  默认构建代理            │  Full tools           │
│  plan        │  规划模式                │  Read-only + plan     │
│  explore     │  代码库探索              │  Search tools only    │
│  title       │  生成会话标题            │  Minimal              │
│  summary     │  总结压缩消息            │  Read-only            │
└─────────────────────────────────────────────────────────────────┘
```

### 6.2 Task 工具与子代理

Task 工具允许启动独立的子代理：

```typescript
// 子代理调用示例
Task({
  prompt: "Search for all usages of AuthService",
  description: "Find authentication patterns",
  subagent_type: "explore"
})
```

子代理特性：
- **无状态**：每次调用独立（除非指定 session_id）
- **隔离上下文**：不共享父代理的对话历史
- **结果摘要**：子代理结果需要主代理摘要后呈现给用户

### 6.3 Subtask 处理流程

```
┌─────────────────────────────────────────────────────────────────┐
│                    Subtask 执行流程                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. 主代理发起 Task 调用                                        │
│     ↓                                                          │
│  2. 创建 Assistant Message + Tool Part                         │
│     ↓                                                          │
│  3. 触发 Plugin Hook (tool.execute.before)                     │
│     ↓                                                          │
│  4. 执行子代理 (独立 session)                                   │
│     ↓                                                          │
│  5. 触发 Plugin Hook (tool.execute.after)                      │
│     ↓                                                          │
│  6. 创建合成用户消息:                                           │
│     "Summarize the task tool output above and continue..."     │
│     ↓                                                          │
│  7. 主代理继续循环                                              │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 7. 消息处理流程

### 7.1 完整处理流程

```
┌─────────────────────────────────────────────────────────────────┐
│                    Prompt 处理主循环                            │
│                    (SessionPrompt.loop)                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  while (true) {                                                │
│    ↓                                                           │
│    ┌─────────────────────────────────────────────┐             │
│    │ 1. 获取消息历史 (过滤已压缩消息)            │             │
│    └─────────────────────────────────────────────┘             │
│    ↓                                                           │
│    ┌─────────────────────────────────────────────┐             │
│    │ 2. 查找最后的用户/助手消息                  │             │
│    └─────────────────────────────────────────────┘             │
│    ↓                                                           │
│    ┌─────────────────────────────────────────────┐             │
│    │ 3. 检查退出条件                             │             │
│    │    - 助手完成 (非 tool-calls)               │             │
│    │    - 用户中断                               │             │
│    └─────────────────────────────────────────────┘             │
│    ↓                                                           │
│    ┌─────────────────────────────────────────────┐             │
│    │ 4. 处理待处理任务                           │             │
│    │    - subtask (子代理调用)                   │             │
│    │    - compaction (消息压缩)                  │             │
│    └─────────────────────────────────────────────┘             │
│    ↓                                                           │
│    ┌─────────────────────────────────────────────┐             │
│    │ 5. 注入动态提醒 (insertReminders)           │             │
│    │    - Plan mode prompt                       │             │
│    │    - Build switch prompt                    │             │
│    │    - User message wrappers                  │             │
│    └─────────────────────────────────────────────┘             │
│    ↓                                                           │
│    ┌─────────────────────────────────────────────┐             │
│    │ 6. 解析工具集 (resolveTools)                │             │
│    │    - 根据模型筛选                           │             │
│    │    - 包含 MCP 工具                          │             │
│    │    - 包含插件工具                           │             │
│    └─────────────────────────────────────────────┘             │
│    ↓                                                           │
│    ┌─────────────────────────────────────────────┐             │
│    │ 7. 触发插件 Hook                            │             │
│    │    (experimental.chat.messages.transform)   │             │
│    └─────────────────────────────────────────────┘             │
│    ↓                                                           │
│    ┌─────────────────────────────────────────────┐             │
│    │ 8. 调用 LLM (processor.process)             │             │
│    │    - system: environment() + custom()       │             │
│    │    - messages: 转换后的消息历史             │             │
│    │    - tools: 解析后的工具集                  │             │
│    │    - (可能追加 MAX_STEPS 提醒)              │             │
│    └─────────────────────────────────────────────┘             │
│    ↓                                                           │
│    continue / break / compact                                  │
│  }                                                             │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 7.2 System Prompt 组装

```typescript
// prompt.ts 中的 processor.process 调用
const result = await processor.process({
  user: lastUser,
  agent,
  abort,
  sessionID,
  system: [
    ...await SystemPrompt.environment(),  // 环境信息
    ...await SystemPrompt.custom(),       // 自定义规则
  ],
  messages: [
    ...MessageV2.toModelMessage(sessionMessages),
    ...(isLastStep ? [{ role: "assistant", content: MAX_STEPS }] : []),
  ],
  tools,
  model,
})
```

### 7.3 消息转换

用户消息在发送给 LLM 前会经过转换：

```
┌─────────────────────────────────────────────────────────────────┐
│                    消息类型转换                                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  用户输入                    LLM 接收                          │
│  ─────────                  ─────────                          │
│                                                                 │
│  @file.txt        →    "Called Read tool..." + 文件内容        │
│                                                                 │
│  @directory/      →    "Called list tool..." + 目录列表        │
│                                                                 │
│  @agent-name      →    AgentPart + "Use the above message      │
│                        to generate a prompt and call task      │
│                        tool with subagent: agent-name"         │
│                                                                 │
│  @mcp-resource    →    "Reading MCP resource..." + 资源内容    │
│                                                                 │
│  普通文本         →    TextPart (可能被 system-reminder 包裹)  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 附录：关键常量与配置

### 输出限制

```typescript
OUTPUT_TOKEN_MAX = 32_000  // 最大输出 token
```

### 本地规则文件

```typescript
LOCAL_RULE_FILES = ["AGENTS.md", "CLAUDE.md", "CONTEXT.md"]
GLOBAL_RULE_FILES = [
  "~/.config/opencode/AGENTS.md",
  "~/.claude/CLAUDE.md"
]
```

### 特性开关

```typescript
Flag.OPENCODE_EXPERIMENTAL_PLAN_MODE     // Plan 模式
Flag.OPENCODE_EXPERIMENTAL_LSP_TOOL      // LSP 工具
Flag.OPENCODE_ENABLE_EXA                 // Exa 搜索
Flag.OPENCODE_DISABLE_CLAUDE_CODE_PROMPT // 禁用 Claude Code prompt
```

---

## 总结

OpenCode 的 Prompt 架构体现了以下设计理念：

1. **分层组合**：System Prompt 由多个独立层级组合，便于维护和扩展
2. **模型适配**：不同 LLM 使用优化过的专用 Prompt
3. **工具描述分离**：工具逻辑与描述文档分离，便于迭代
4. **动态注入**：通过 `<system-reminder>` 标签在运行时注入上下文
5. **插件扩展**：支持通过插件和 MCP 添加自定义工具
6. **Agent 协作**：支持子代理调用实现复杂任务分解

这种架构使 OpenCode 能够灵活适应不同的使用场景，同时保持代码的可维护性。

