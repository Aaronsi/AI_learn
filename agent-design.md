# Simple Agent Design Document

## 概述

本文档描述一个简单但完整的 Agent 系统设计，能够完成多步的 agent loop。Agent 接收用户输入，通过 LLM 处理，判断是否需要调用工具，如果需要则执行工具并循环处理结果，直到获得最终响应。

## Agent Loop 流程

```
用户输入 (User Input)
    ↓
LLM 处理
    ↓
判断是否需要工具调用? (tool call?)
    ├─ 是 (Y) → 执行工具 (Execute Tool)
    │              ↓
    │          工具结果 (Tool Result)
    │              ↓
    │          返回 LLM (循环)
    │
    └─ 否 (N) → 结果响应 (Result Response) → 结束
```

## 核心概念

### 1. Agent 状态
Agent 在每次循环中维护以下状态：
- **消息历史** (Message History): 包含用户消息、助手消息、工具调用和工具结果
- **当前轮次** (Turn): 从用户输入到最终响应的完整交互过程
- **工具注册表** (Tool Registry): 可用的工具集合

### 2. LLM 交互
- **输入**: 系统提示 + 消息历史
- **输出**: 文本响应或工具调用请求
- **格式**: 支持结构化输出（JSON）用于工具调用

### 3. 工具系统
- **工具定义**: 名称、描述、参数 schema
- **工具执行**: 异步执行，返回结果
- **结果处理**: 将工具结果添加到消息历史，继续循环

## 架构设计

### 目录结构

```
simple-agent/
├── src/
│   ├── agent.ts              # Agent 核心类
│   ├── llm.ts                # LLM 接口和实现
│   ├── tool.ts               # 工具系统
│   ├── types.ts              # 类型定义
│   └── utils.ts              # 工具函数
├── tools/                    # 内置工具示例
│   ├── calculator.ts
│   ├── weather.ts
│   └── index.ts
├── examples/                 # 使用示例
│   └── basic.ts
├── package.json
└── tsconfig.json
```

## 类型定义

### 消息类型

```typescript
// 消息角色
type MessageRole = 'user' | 'assistant' | 'system' | 'tool'

// 基础消息
interface BaseMessage {
  role: MessageRole
  content: string
  timestamp: number
}

// 用户消息
interface UserMessage extends BaseMessage {
  role: 'user'
}

// 助手消息
interface AssistantMessage extends BaseMessage {
  role: 'assistant'
}

// 工具调用消息
interface ToolCallMessage extends BaseMessage {
  role: 'assistant'
  toolCalls: ToolCall[]
}

// 工具结果消息
interface ToolResultMessage extends BaseMessage {
  role: 'tool'
  toolCallId: string
  toolName: string
  result: any
}

type Message = UserMessage | AssistantMessage | ToolCallMessage | ToolResultMessage
```

### 工具类型

```typescript
// 工具参数定义
interface ToolParameter {
  name: string
  type: 'string' | 'number' | 'boolean' | 'object' | 'array'
  description: string
  required?: boolean
  enum?: any[]
}

// 工具定义
interface ToolDefinition {
  name: string
  description: string
  parameters: ToolParameter[]
}

// 工具调用
interface ToolCall {
  id: string
  name: string
  arguments: Record<string, any>
}

// 工具执行结果
interface ToolResult {
  toolCallId: string
  success: boolean
  result?: any
  error?: string
}

// 工具实现接口
interface Tool {
  definition: ToolDefinition
  execute(args: Record<string, any>): Promise<any>
}
```

### Agent 配置

```typescript
interface AgentConfig {
  // LLM 配置
  llm: {
    provider: 'openai' | 'anthropic' | 'custom'
    model: string
    apiKey?: string
    baseURL?: string
    temperature?: number
    maxTokens?: number
  }
  
  // 系统提示
  systemPrompt?: string
  
  // 工具列表
  tools: Tool[]
  
  // 循环控制
  maxIterations?: number  // 最大循环次数，防止无限循环
  timeout?: number        // 超时时间（毫秒）
}
```

## 核心类设计

### Agent 类

```typescript
class Agent {
  private config: AgentConfig
  private llm: LLMProvider
  private tools: Map<string, Tool>
  private messageHistory: Message[]
  
  constructor(config: AgentConfig)
  
  // 主入口：处理用户输入
  async chat(userInput: string): Promise<string>
  
  // Agent Loop 核心逻辑
  private async agentLoop(userInput: string): Promise<string>
  
  // 调用 LLM
  private async callLLM(): Promise<LLMResponse>
  
  // 解析 LLM 响应，判断是否有工具调用
  private parseLLMResponse(response: string): ParsedResponse
  
  // 执行工具调用
  private async executeToolCall(toolCall: ToolCall): Promise<ToolResult>
  
  // 添加消息到历史
  private addMessage(message: Message): void
  
  // 检查是否应该继续循环
  private shouldContinue(response: ParsedResponse): boolean
}
```

### LLM 响应解析

```typescript
interface ParsedResponse {
  type: 'text' | 'tool_calls'
  text?: string
  toolCalls?: ToolCall[]
}

// LLM 响应格式（结构化输出）
interface LLMStructuredResponse {
  reasoning?: string      // 思考过程（可选）
  response?: string       // 文本响应
  toolCalls?: ToolCall[]  // 工具调用列表
}
```

## Agent Loop 详细流程

### 1. 初始化阶段
```
1. 创建 Agent 实例
2. 注册工具
3. 设置系统提示
4. 初始化消息历史
```

### 2. 主循环阶段
```
WHILE (未达到最大迭代次数 AND 未超时):
  1. 构建 LLM 输入（系统提示 + 消息历史）
  2. 调用 LLM
  3. 解析 LLM 响应
  4. IF 响应包含工具调用:
     a. 执行每个工具调用
     b. 将工具结果添加到消息历史
     c. 继续循环
  5. ELSE IF 响应是文本:
     a. 返回最终响应
     b. 退出循环
  6. ELSE:
     a. 错误处理
     b. 退出循环
```

### 3. 错误处理
- **LLM 调用失败**: 重试或返回错误消息
- **工具执行失败**: 将错误信息添加到消息历史，让 LLM 决定下一步
- **超时**: 返回当前最佳响应或超时错误
- **无限循环**: 达到最大迭代次数时强制返回

## LLM 提示设计

### 系统提示模板

```
你是一个智能助手，可以使用工具来帮助用户完成任务。

可用工具：
{tool_descriptions}

工具调用格式：
{
  "toolCalls": [
    {
      "id": "call_xxx",
      "name": "tool_name",
      "arguments": {
        "param1": "value1"
      }
    }
  ]
}

规则：
1. 如果用户的问题需要调用工具，请使用工具调用格式响应
2. 如果不需要工具或已有足够信息，直接返回文本响应
3. 工具调用后，你会收到工具结果，然后继续处理
4. 始终以用户能理解的方式组织最终响应
```

### 消息历史格式

```
[
  {"role": "system", "content": "系统提示"},
  {"role": "user", "content": "用户输入"},
  {"role": "assistant", "content": "助手响应", "toolCalls": [...]},
  {"role": "tool", "content": "工具结果", "toolCallId": "...", "toolName": "..."},
  ...
]
```

## 工具系统设计

### 工具注册

```typescript
// 工具注册接口
interface ToolRegistry {
  register(tool: Tool): void
  get(name: string): Tool | undefined
  list(): ToolDefinition[]
}
```

### 内置工具示例

#### 1. 计算器工具
```typescript
class CalculatorTool implements Tool {
  definition = {
    name: 'calculator',
    description: '执行数学计算',
    parameters: [
      {
        name: 'expression',
        type: 'string',
        description: '数学表达式，如 "2 + 2"',
        required: true
      }
    ]
  }
  
  async execute(args: { expression: string }): Promise<number> {
    // 安全地执行数学表达式
    // 返回计算结果
  }
}
```

#### 2. 天气查询工具
```typescript
class WeatherTool implements Tool {
  definition = {
    name: 'get_weather',
    description: '获取指定城市的天气信息',
    parameters: [
      {
        name: 'city',
        type: 'string',
        description: '城市名称',
        required: true
      }
    ]
  }
  
  async execute(args: { city: string }): Promise<WeatherInfo> {
    // 调用天气 API
    // 返回天气信息
  }
}
```

## 实现细节

### 1. LLM 响应解析策略

**方案 A: JSON 模式（推荐）**
- 要求 LLM 返回结构化 JSON
- 使用 JSON Schema 验证
- 优点：可靠、易解析
- 缺点：需要 LLM 支持结构化输出

**方案 B: 文本解析**
- 从文本中提取工具调用信息
- 使用正则表达式或自然语言处理
- 优点：兼容性好
- 缺点：不够可靠

**方案 C: 函数调用（Function Calling）**
- 使用 LLM 原生的函数调用功能
- 优点：最可靠、原生支持
- 缺点：需要 LLM 支持函数调用

### 2. 循环控制机制

```typescript
class LoopController {
  private maxIterations: number
  private timeout: number
  private startTime: number
  private iterationCount: number
  
  shouldContinue(): boolean {
    // 检查迭代次数
    if (this.iterationCount >= this.maxIterations) {
      return false
    }
    
    // 检查超时
    if (Date.now() - this.startTime > this.timeout) {
      return false
    }
    
    return true
  }
  
  increment(): void {
    this.iterationCount++
  }
}
```

### 3. 错误恢复策略

- **工具执行失败**: 将错误信息传递给 LLM，让它决定下一步
- **LLM 解析失败**: 尝试重新格式化提示，或返回错误消息
- **网络错误**: 指数退避重试

## 使用示例

### 基本使用

```typescript
import { Agent } from './src/agent'
import { CalculatorTool, WeatherTool } from './tools'

const agent = new Agent({
  llm: {
    provider: 'openai',
    model: 'gpt-4',
    apiKey: process.env.OPENAI_API_KEY,
    temperature: 0.7
  },
  systemPrompt: '你是一个有用的助手',
  tools: [
    new CalculatorTool(),
    new WeatherTool()
  ],
  maxIterations: 10,
  timeout: 30000
})

// 使用 Agent
const response = await agent.chat('计算 123 * 456，然后告诉我北京的天气')
console.log(response)
```

### 多步交互示例

```typescript
// 第一轮：用户询问
const response1 = await agent.chat('今天北京天气怎么样？')
// Agent 调用天气工具，返回结果

// 第二轮：继续对话
const response2 = await agent.chat('那上海呢？')
// Agent 记住上下文，调用天气工具查询上海
```

## 扩展性设计

### 1. 自定义工具

```typescript
class CustomTool implements Tool {
  definition = {
    name: 'my_tool',
    description: '自定义工具描述',
    parameters: [...]
  }
  
  async execute(args: Record<string, any>): Promise<any> {
    // 实现工具逻辑
  }
}

agent.registerTool(new CustomTool())
```

### 2. 自定义 LLM Provider

```typescript
interface LLMProvider {
  chat(messages: Message[]): Promise<string>
  chatStructured(messages: Message[], schema: JSONSchema): Promise<LLMStructuredResponse>
}

class CustomLLMProvider implements LLMProvider {
  // 实现自定义 LLM 接口
}
```

### 3. 中间件系统

```typescript
interface Middleware {
  beforeLLMCall?(messages: Message[]): Promise<Message[]>
  afterLLMCall?(response: string): Promise<string>
  beforeToolCall?(toolCall: ToolCall): Promise<ToolCall>
  afterToolCall?(result: ToolResult): Promise<ToolResult>
}

agent.use(middleware)
```

## 性能优化

### 1. 并发工具调用
- 如果多个工具调用相互独立，可以并发执行
- 使用 `Promise.all()` 并行处理

### 2. 消息历史压缩
- 当消息历史过长时，压缩或总结早期消息
- 保留最近的完整对话和工具调用结果

### 3. 缓存机制
- 缓存 LLM 响应（相同输入）
- 缓存工具结果（相同参数）

## 测试策略

### 1. 单元测试
- 工具执行测试
- LLM 响应解析测试
- 循环控制测试

### 2. 集成测试
- 完整 Agent Loop 测试
- 多步交互测试
- 错误处理测试

### 3. 端到端测试
- 真实场景测试
- 性能测试
- 压力测试

## 安全考虑

### 1. 工具执行安全
- 沙箱环境执行工具
- 参数验证和清理
- 资源限制（CPU、内存、时间）

### 2. LLM 输入安全
- 提示注入防护
- 输入长度限制
- 敏感信息过滤

### 3. 错误信息处理
- 不泄露内部实现细节
- 用户友好的错误消息

## 未来改进方向

1. **流式响应**: 支持流式输出，提升用户体验
2. **多 Agent 协作**: 多个 Agent 协同工作
3. **记忆系统**: 长期记忆和知识库
4. **学习能力**: 从交互中学习和改进
5. **可视化**: Agent Loop 的可视化调试工具

## 总结

这个设计提供了一个简单但完整的 Agent 系统，能够：
- ✅ 处理用户输入
- ✅ 通过 LLM 进行推理
- ✅ 判断是否需要工具调用
- ✅ 执行工具并处理结果
- ✅ 循环直到获得最终响应
- ✅ 错误处理和循环控制
- ✅ 可扩展的工具系统

设计遵循单一职责原则，各组件职责清晰，易于测试和维护。

