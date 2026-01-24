# OpenCode Conversation Visualizer

一个用于可视化 OpenCode 与 LLM 交互对话记录的 React 应用。

## 功能特性

- 📁 **文件加载**: 支持拖拽或选择 JSONL 文件
- 📋 **Turn 列表**: 显示所有对话 turn 的预览
- 🔍 **Turn 详情**: 详细展示每个 turn 的输入输出
- 📝 **Markdown 渲染**: 自动渲染 Markdown 格式的文本内容
- 🎨 **响应式设计**: 适配桌面和移动设备
- 🎯 **Design Tokens**: 使用统一的设计系统

## 安装依赖

```bash
cd visualizer
npm install
# 或
bun install
```

## 开发运行

```bash
npm run dev
# 或
bun run dev
```

应用将在 `http://localhost:3000` 启动。

## 构建

```bash
npm run build
# 或
bun run build
```

## 使用方法

1. 启动应用后，拖拽或选择 JSONL 文件
2. 文件加载后，左侧显示 Turn 列表
3. 点击任意 Turn 查看详细信息
4. 详细信息包括：
   - **输入**: 消息列表、参数设置
   - **输出**: 文本输出（Markdown 渲染）、工具调用

## 项目结构

```
visualizer/
├── src/
│   ├── App.tsx                 # 主应用组件
│   ├── main.tsx                # 入口文件
│   ├── components/             # React 组件
│   │   ├── FileLoader.tsx      # 文件加载组件
│   │   ├── TurnList.tsx        # Turn 列表组件
│   │   ├── TurnDetail.tsx     # Turn 详情组件
│   │   ├── MessageView.tsx     # 消息展示组件
│   │   ├── ToolCallView.tsx    # 工具调用展示组件
│   │   └── MarkdownContent.tsx # Markdown 渲染组件
│   ├── types/                  # TypeScript 类型定义
│   │   └── turn.ts
│   ├── utils/                  # 工具函数
│   │   ├── parser.ts           # JSONL 解析
│   │   └── formatter.ts        # 格式化工具
│   └── styles/                 # 样式文件
│       └── app.css             # 应用特定样式
├── styles/                     # 全局样式
│   ├── design-tokens.css       # 设计变量
│   └── global.css              # 全局样式
├── index.html                  # HTML 模板
├── package.json
├── tsconfig.json
└── vite.config.ts
```

## 技术栈

- **React 18+** - UI 框架
- **TypeScript** - 类型安全
- **Vite** - 构建工具
- **react-markdown** - Markdown 渲染
- **remark-gfm** - GitHub Flavored Markdown 支持

## 数据格式

应用期望的 JSONL 文件格式：

每行一个 JSON 对象，包含：
- `turnID`: Turn 唯一标识符
- `timestamp`: Unix 时间戳（毫秒）
- `input`: 输入数据
  - `messages`: 消息数组
  - `params`: 参数（可选）
- `output`: 输出数据
  - `textParts`: 文本输出数组
  - `toolCalls`: 工具调用数组

详细类型定义请参考 `src/types/turn.ts`。

