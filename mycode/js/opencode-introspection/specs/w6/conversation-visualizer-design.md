# OpenCode Conversation Visualizer - Design Document

## 概述

构建一个 React 应用，用于可视化 OpenCode 与 LLM 交互的完整对话记录。用户可以打开 JSONL 文件，查看每个 turn 的详细输入输出信息。

## Schema 分析

### Turn 数据结构

```typescript
interface Turn {
  turnID: string                    // Turn 唯一标识符
  timestamp: number                 // Unix 时间戳（毫秒）
  input: {
    messages: Array<{
      info: {
        id: string                  // Message ID
        sessionID: string           // Session ID
        role: "user" | "assistant" | "system"
        time: {
          created: number          // 创建时间戳
        }
        agent?: string              // Agent 名称
        model?: {
          providerID: string       // Provider ID (如 "deepseek")
          modelID: string          // Model ID (如 "deepseek-reasoner")
        }
      }
      parts: Array<{
        id: string                  // Part ID
        sessionID: string
        messageID: string
        type: "text" | "tool" | ... // Part 类型
        text?: string              // 文本内容（如果是文本类型）
        // ... 其他类型可能有不同字段
      }>
    }>
    params?: {
      temperature?: number
      topP?: number
      topK?: number
      options?: Record<string, any>  // 其他参数
    }
  }
  output: {
    textParts: Array<{
      partID: string               // Part ID
      text: string                 // 文本内容（Markdown 格式）
      timestamp: number           // 时间戳
    }>
    toolCalls: Array<{
      callID: string               // Call ID
      tool: string                // 工具名称
      args: any                   // 工具参数
      result?: {
        title: string
        output: string
        metadata: any
      }
      timestamp: number
    }>
  }
}
```

## 功能需求

### 1. 文件加载
- 支持文件选择器选择 JSONL 文件
- 支持拖拽文件到页面
- 解析 JSONL 格式（每行一个 JSON 对象）

### 2. Turn 列表展示
- 左侧或顶部显示所有 turn 的列表
- 每个 turn 显示：
  - Turn ID（简化显示）
  - 时间戳（格式化显示）
  - 用户输入预览（第一行文本）
  - 输出预览（第一行文本）

### 3. Turn 详情展示
- 选中 turn 后，右侧或下方显示详细信息
- 分为多个区域：
  - **输入区域**：
    - Messages 列表（显示 role、agent、model 信息）
    - 每个 message 的 parts（文本内容使用 Markdown 渲染）
    - Parameters（temperature、topP、topK 等）
  - **输出区域**：
    - Text Parts（使用 Markdown 渲染）
    - Tool Calls（显示工具名称、参数、结果）

### 4. UI/UX 要求
- 使用 scrollbar 控制区域长度（避免页面过长）
- 文字内容使用 Markdown renderer 渲染
- 响应式设计，适配不同屏幕尺寸
- 使用提供的 design tokens 和 global CSS

## 技术架构

### 技术栈
- **React 18+** - UI 框架
- **TypeScript** - 类型安全
- **Vite** - 构建工具
- **react-markdown** - Markdown 渲染
- **react-syntax-highlighter** (可选) - 代码高亮

### 项目结构
```
visualizer/
├── src/
│   ├── App.tsx                 # 主应用组件
│   ├── main.tsx                # 入口文件
│   ├── components/
│   │   ├── FileLoader.tsx      # 文件加载组件
│   │   ├── TurnList.tsx        # Turn 列表组件
│   │   ├── TurnDetail.tsx      # Turn 详情组件
│   │   ├── MessageView.tsx     # Message 展示组件
│   │   ├── ToolCallView.tsx    # Tool Call 展示组件
│   │   └── MarkdownContent.tsx # Markdown 渲染组件
│   ├── types/
│   │   └── turn.ts             # TypeScript 类型定义
│   ├── utils/
│   │   ├── parser.ts           # JSONL 解析工具
│   │   └── formatter.ts        # 时间格式化等工具
│   └── styles/
│       ├── design-tokens.css   # (已存在)
│       └── global.css          # (已存在)
├── index.html                  # HTML 模板
├── package.json
├── tsconfig.json
└── vite.config.ts
```

## UI 布局设计

### 桌面端布局
```
┌─────────────────────────────────────────────────────────┐
│                    Header / File Loader                 │
├──────────────┬──────────────────────────────────────────┤
│              │                                          │
│  Turn List   │         Turn Detail View                 │
│              │                                          │
│  - Turn 1    │    Input Section:                        │
│  - Turn 2    │    ┌─────────────────────────────┐      │
│  - Turn 3    │    │ Messages                    │      │
│  ...         │    │ - User: "..."               │      │
│              │    └─────────────────────────────┘      │
│  (scrollable) │    ┌─────────────────────────────┐      │
│              │    │ Parameters                   │      │
│              │    │ - temperature: 0.7           │      │
│              │    └─────────────────────────────┘      │
│              │    Output Section:                        │
│              │    ┌─────────────────────────────┐      │
│              │    │ Text Parts                  │      │
│              │    │ (Markdown rendered)         │      │
│              │    └─────────────────────────────┘      │
│              │    ┌─────────────────────────────┐      │
│              │    │ Tool Calls                  │      │
│              │    │ - tool: "..."               │      │
│              │    └─────────────────────────────┘      │
│              │                                          │
│              │         (scrollable)                     │
└──────────────┴──────────────────────────────────────────┘
```

### 移动端布局
```
┌─────────────────────────────┐
│      File Loader            │
├─────────────────────────────┤
│      Turn List              │
│  (horizontal scrollable)     │
├─────────────────────────────┤
│                             │
│    Turn Detail View         │
│                             │
│    (scrollable)             │
│                             │
└─────────────────────────────┘
```

## 组件设计

### FileLoader
- 文件选择按钮
- 拖拽区域
- 文件信息显示（文件名、turn 数量）

### TurnList
- 可滚动的 turn 列表
- 每个 turn 卡片显示：
  - 时间戳（格式化）
  - 输入预览（截取前 50 字符）
  - 输出预览（截取前 50 字符）
- 选中状态高亮

### TurnDetail
- 输入区域：
  - Messages 列表（可折叠）
  - Parameters 表格
- 输出区域：
  - Text Parts（Markdown 渲染）
  - Tool Calls（可折叠，显示详细信息）

### MarkdownContent
- 使用 react-markdown 渲染
- 支持代码块高亮
- 应用 markdown-content CSS 类

## 样式指南

### 使用 Design Tokens
- 颜色：`var(--md-ink)`, `var(--md-slate)`, `var(--md-cloud)`, etc.
- 间距：`var(--space-md)`, `var(--space-lg)`, etc.
- 字体：`var(--font-body)`, `var(--font-h2)`, etc.

### 滚动区域
- 使用 `.scrollable` 类
- 最大高度限制，超出显示滚动条
- Turn List: 固定高度，垂直滚动
- Turn Detail: 固定高度，垂直滚动

### 卡片样式
- 使用 `.card` 类
- 边框：`var(--border-strong)`
- 背景：`var(--md-cloud)`

## 实现步骤

1. ✅ 创建项目基础结构（package.json, tsconfig, vite.config）
2. ✅ 实现文件加载功能（FileLoader）
3. ✅ 实现 JSONL 解析（parser.ts）
4. ✅ 实现 Turn 列表组件（TurnList）
5. ✅ 实现 Turn 详情组件（TurnDetail）
6. ✅ 集成 Markdown 渲染（MarkdownContent）
7. ✅ 实现响应式布局
8. ✅ 添加样式和交互效果

## 注意事项

1. **性能优化**：
   - 大文件分页加载（如果 turn 数量很多）
   - 虚拟滚动（如果列表很长）

2. **错误处理**：
   - 文件格式验证
   - JSON 解析错误处理
   - 空状态处理

3. **可访问性**：
   - 键盘导航支持
   - ARIA 标签
   - 焦点管理

4. **用户体验**：
   - 加载状态指示
   - 错误提示
   - 空状态提示

