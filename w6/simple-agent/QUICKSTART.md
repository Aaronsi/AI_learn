# Quick Start Guide

This guide will help you get started with the Simple Agent SDK in 5 minutes.

## Prerequisites

- Node.js (v18 or higher)
- DeepSeek API key (get one from https://platform.deepseek.com/)

## Installation

```bash
# Install dependencies
npm install
```

## Setup

1. Copy the example environment file:
```bash
cp .env.example .env
```

2. Edit `.env` and add your DeepSeek API key:
```
DEEPSEEK_API_KEY=your-api-key-here
```

## Build

```bash
npm run build
```

## Run Examples

### Example 1: Calculator Agent (Custom Tools)

```bash
npm run example:calculator
```

This example shows how to:
- Create custom tools
- Register tools with the agent
- Handle tool execution
- Deal with errors

**Expected output**: The agent will perform calculations using the calculator tools.

### Example 2: Weather Agent (Streaming)

```bash
npm run example:weather
```

This example demonstrates:
- Streaming responses in real-time
- Event handling
- Multi-step tool calling
- Friendly conversational responses

**Expected output**: You'll see the response streaming in real-time as the agent retrieves weather data.

### Example 3: MCP Filesystem (MCP Integration)

```bash
npm run example:mcp
```

This example shows:
- Connecting to an MCP server
- Automatically loading tools from MCP
- Using filesystem operations
- Reading and writing files

**Expected output**: The agent will list, read, and write files in your current directory.

## Your First Agent

Create a file called `my-agent.ts`:

```typescript
import { SimpleAgent, Tool } from "./src";

// Define a tool
const greetTool: Tool = {
  name: "greet",
  description: "Greet someone by name",
  parameters: {
    type: "object",
    properties: {
      name: { type: "string", description: "Person's name" }
    },
    required: ["name"]
  },
  execute: async (args: any) => {
    return {
      output: `Hello, ${args.name}! Nice to meet you!`
    };
  }
};

async function main() {
  // Create agent
  const agent = new SimpleAgent({
    systemPrompt: "You are a friendly greeter."
  });

  // Add tool
  agent.addTool(greetTool);

  // Create session
  const session = agent.createSession();

  // Run agent
  const response = await agent.run(
    session.id,
    "Greet Alice and Bob"
  );

  console.log(response);

  // Cleanup
  await agent.cleanup();
}

main();
```

Run it:
```bash
npx tsx my-agent.ts
```

## Next Steps

1. **Read the full README.md** for complete API documentation
2. **Check IMPLEMENTATION_VERIFICATION.md** to understand how the implementation matches the design spec
3. **Explore the examples/** directory for more advanced use cases
4. **Build your own tools** and integrate them with the agent

## Common Issues

### API Key Not Found
Make sure your `.env` file exists and contains `DEEPSEEK_API_KEY`.

### MCP Server Not Found
For the MCP example, the filesystem server is installed via npx automatically. If you have connection issues, check your internet connection.

### Build Errors
Make sure you're using Node.js v18 or higher and have run `npm install`.

## Getting Help

- Check the [README.md](README.md) for full documentation
- Review the [examples](examples/) for working code
- Read the [design spec](../specs/w6/0001-simple-agent-design.md) for architecture details

Happy building! 🚀
