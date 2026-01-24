# Simple Agent SDK

A simple and easy-to-use agent framework with tool calling and MCP (Model Context Protocol) support, powered by DeepSeek.

## Features

- **Easy-to-use API**: Simple, intuitive interface for building agents
- **Custom Tools**: Easily add your own tools with a simple interface
- **MCP Integration**: Connect to MCP servers to dynamically load tools
- **Streaming Support**: Real-time streaming responses with event handling
- **Session Management**: Built-in session and message management
- **Type-safe**: Full TypeScript support with comprehensive types
- **DeepSeek Powered**: Uses DeepSeek's powerful LLM via OpenAI-compatible API

## Installation

```bash
npm install
```

## Quick Start

### Basic Usage with Custom Tools

```typescript
import { SimpleAgent, Tool } from "./src";

// Define a custom tool
const weatherTool: Tool = {
  name: "get_weather",
  description: "Get weather for a city",
  parameters: {
    type: "object",
    properties: {
      city: { type: "string", description: "City name" }
    },
    required: ["city"]
  },
  execute: async (args: any) => {
    return {
      output: `Weather in ${args.city}: Sunny, 22°C`
    };
  }
};

// Create agent and add tool
const agent = new SimpleAgent({
  model: "deepseek-chat",
  systemPrompt: "You are a helpful weather assistant."
});

agent.addTool(weatherTool);

// Create session and run
const session = agent.createSession();
const response = await agent.run(
  session.id,
  "What's the weather in Tokyo?"
);

console.log(response);
```

### Streaming Responses

```typescript
// Stream responses in real-time
for await (const event of agent.stream(session.id, "Tell me about the weather")) {
  if (event.type === "text") {
    process.stdout.write(event.text);
  } else if (event.type === "tool_call") {
    console.log(`\nUsing tool: ${event.name}`);
  }
}
```

### Using MCP Servers

```typescript
// Add an MCP server (e.g., filesystem)
await agent.addMCPServer({
  name: "filesystem",
  command: "npx",
  args: ["-y", "@modelcontextprotocol/server-filesystem", process.cwd()]
});

// Now the agent has access to file operations
const response = await agent.run(
  session.id,
  "List the files in the current directory"
);
```

## Core Concepts

### Agent

The `SimpleAgent` class is the main entry point. It manages:
- LLM client (DeepSeek)
- Tool registry
- Session management
- MCP servers

### Tools

Tools are functions that the agent can call. Each tool has:
- **name**: Unique identifier
- **description**: What the tool does
- **parameters**: JSON Schema for arguments
- **execute**: Async function that performs the action

### Sessions

Sessions manage conversation state:
- Messages history
- System prompt
- Model configuration
- Available tools

### MCP Integration

MCP (Model Context Protocol) allows you to:
- Connect to external tool providers
- Dynamically load tools from servers
- Use standardized tool interfaces

## Configuration

### Agent Configuration

```typescript
const agent = new SimpleAgent({
  model: "deepseek-chat",           // Model name
  systemPrompt: "You are...",       // System prompt
  temperature: 0.7,                 // Sampling temperature
  maxTokens: 4096,                  // Max response tokens
  maxSteps: 200,                    // Max tool calling loops
  llmConfig: {
    apiKey: "your-key",             // DeepSeek API key
    baseURL: "https://..."          // Custom base URL
  }
});
```

### Environment Variables

```bash
DEEPSEEK_API_KEY=your-api-key
DEEPSEEK_BASE_URL=https://api.deepseek.com  # Optional
```

## API Reference

### SimpleAgent

#### Constructor
```typescript
new SimpleAgent(config?: SimpleAgentConfig)
```

#### Methods

- `addTool(tool: Tool): void` - Add a custom tool
- `addTools(tools: Tool[]): void` - Add multiple tools
- `removeTool(name: string): boolean` - Remove a tool
- `listTools(): Tool[]` - List all registered tools
- `addMCPServer(config: MCPConfig): Promise<void>` - Add an MCP server
- `removeMCPServer(name: string): Promise<boolean>` - Remove an MCP server
- `createSession(config?): Session` - Create a new session
- `run(sessionId, message?, config?): Promise<string>` - Run agent (non-streaming)
- `stream(sessionId, message?, config?): AsyncGenerator<AgentEvent>` - Run agent with streaming
- `getSession(sessionId): Session | undefined` - Get a session
- `getMessages(sessionId): Message[]` - Get session messages
- `deleteSession(sessionId): boolean` - Delete a session
- `cleanup(): Promise<void>` - Clean up resources

### Tool Interface

```typescript
interface Tool {
  name: string;
  description: string;
  parameters: JSONSchema;
  execute: (args: unknown) => Promise<ToolResult>;
}

interface ToolResult {
  output: string;
  metadata?: Record<string, unknown>;
  error?: string;
}
```

### Event Types

```typescript
type AgentEvent =
  | { type: "message_start"; role: "assistant" }
  | { type: "text"; text: string }
  | { type: "tool_call"; name: string; args: unknown }
  | { type: "tool_result"; name: string; result: string; isError?: boolean }
  | { type: "message_end"; finishReason: string }
  | { type: "error"; error: Error };
```

## Examples

The `examples` directory contains complete working examples:

### 1. Calculator Agent (`01-calculator.ts`)
Shows how to create custom tools for mathematical operations.

```bash
npm run example:calculator
```

### 2. Weather Agent with Streaming (`02-weather-streaming.ts`)
Demonstrates streaming responses and event handling.

```bash
npm run example:weather
```

### 3. MCP Filesystem Integration (`03-mcp-filesystem.ts`)
Shows how to use MCP servers for file operations.

```bash
npm run example:mcp
```

## Architecture

```
src/
├── agent/          # Agent loop logic
│   ├── loop.ts     # Non-streaming agent loop
│   └── stream.ts   # Streaming agent loop
├── llm/            # LLM client
│   └── client.ts   # DeepSeek client (OpenAI compatible)
├── tool/           # Tool management
│   ├── registry.ts # Tool registry
│   └── executor.ts # Tool executor
├── mcp/            # MCP integration
│   └── client.ts   # MCP client and manager
├── session/        # Session management
│   └── manager.ts  # Session manager
├── types/          # TypeScript types
│   ├── message.ts  # Message types
│   ├── tool.ts     # Tool types
│   ├── session.ts  # Session types
│   └── events.ts   # Event types
├── utils/          # Utilities
│   └── index.ts    # Helper functions
└── index.ts        # Main SDK entry point
```

## Design Principles

Based on the [design specification](../specs/w6/0001-simple-agent-design.md):

1. **Streaming First**: All LLM calls support streaming for real-time feedback
2. **Tool as First-Class Citizens**: Unified tool interface for custom, built-in, and MCP tools
3. **Loop Until Complete**: Agent continues until LLM stops requesting tools
4. **Type Safety**: Full TypeScript support with comprehensive types
5. **Simple API**: Easy to use, hard to misuse

## Comparison with Design Spec

| Component | Spec Required | Implemented |
|-----------|---------------|-------------|
| Message Structure | ✅ | ✅ |
| Tool Definition | ✅ | ✅ |
| LLM Client | ✅ | ✅ |
| Streaming Support | Optional | ✅ |
| Agent Loop | ✅ | ✅ |
| Tool Registry | ✅ | ✅ |
| Tool Executor | ✅ | ✅ |
| Session Manager | ✅ | ✅ |
| MCP Integration | Optional | ✅ |
| Permission System | Optional | ❌ (not implemented) |
| Message Compression | Optional | ❌ (not implemented) |
| Retry Mechanism | Optional | ✅ (utility provided) |

## Advanced Usage

### Custom Event Handling

```typescript
await agent.run(sessionId, "Hello", {
  onEvent: (event) => {
    if (event.type === "tool_call") {
      console.log(`Calling ${event.name} with`, event.args);
    } else if (event.type === "error") {
      console.error("Error:", event.error);
    }
  }
});
```

### Error Handling in Tools

```typescript
const safeTool: Tool = {
  name: "divide",
  description: "Divide two numbers",
  parameters: { /* ... */ },
  execute: async (args: any) => {
    if (args.b === 0) {
      return {
        output: "",
        error: "Cannot divide by zero"
      };
    }
    return {
      output: String(args.a / args.b)
    };
  }
};
```

### Using Multiple MCP Servers

```typescript
// Add multiple MCP servers
await agent.addMCPServer({
  name: "filesystem",
  command: "npx",
  args: ["-y", "@modelcontextprotocol/server-filesystem", "./"]
});

await agent.addMCPServer({
  name: "github",
  command: "npx",
  args: ["-y", "@modelcontextprotocol/server-github"]
});

// All tools from both servers are now available
console.log(agent.listTools());
```

## Building

```bash
# Build the project
npm run build

# Watch mode for development
npm run dev

# Clean build artifacts
npm run clean
```

## License

MIT

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
