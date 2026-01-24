/**
 * Example 1: Basic Calculator Agent
 * Demonstrates how to create custom tools and use them with the agent
 */

import { SimpleAgent, Tool } from "../src";

// Define calculator tools
const calculatorTools: Tool[] = [
  {
    name: "add",
    description: "Add two numbers together",
    parameters: {
      type: "object",
      properties: {
        a: { type: "number", description: "First number" },
        b: { type: "number", description: "Second number" },
      },
      required: ["a", "b"],
    },
    execute: async (args: any) => {
      const result = args.a + args.b;
      return {
        output: `${args.a} + ${args.b} = ${result}`,
      };
    },
  },
  {
    name: "subtract",
    description: "Subtract two numbers",
    parameters: {
      type: "object",
      properties: {
        a: { type: "number", description: "First number" },
        b: { type: "number", description: "Second number" },
      },
      required: ["a", "b"],
    },
    execute: async (args: any) => {
      const result = args.a - args.b;
      return {
        output: `${args.a} - ${args.b} = ${result}`,
      };
    },
  },
  {
    name: "multiply",
    description: "Multiply two numbers",
    parameters: {
      type: "object",
      properties: {
        a: { type: "number", description: "First number" },
        b: { type: "number", description: "Second number" },
      },
      required: ["a", "b"],
    },
    execute: async (args: any) => {
      const result = args.a * args.b;
      return {
        output: `${args.a} * ${args.b} = ${result}`,
      };
    },
  },
  {
    name: "divide",
    description: "Divide two numbers",
    parameters: {
      type: "object",
      properties: {
        a: { type: "number", description: "Numerator" },
        b: { type: "number", description: "Denominator" },
      },
      required: ["a", "b"],
    },
    execute: async (args: any) => {
      if (args.b === 0) {
        return {
          output: "",
          error: "Cannot divide by zero",
        };
      }
      const result = args.a / args.b;
      return {
        output: `${args.a} / ${args.b} = ${result}`,
      };
    },
  },
];

async function main() {
  console.log("🧮 Calculator Agent Example\n");

  // Create the agent
  const agent = new SimpleAgent({
    model: "deepseek-chat",
    systemPrompt:
      "You are a helpful calculator assistant. Use the provided tools to perform calculations.",
    temperature: 0,
  });

  // Add calculator tools
  agent.addTools(calculatorTools);

  // Create a session
  const session = agent.createSession();

  console.log("Session created:", session.id);
  console.log("Available tools:", agent.listTools().map((t) => t.name).join(", "));
  console.log();

  // Example 1: Simple calculation
  console.log("Example 1: Simple calculation");
  console.log("User: What is 15 + 27?");
  const result1 = await agent.run(
    session.id,
    "What is 15 + 27?",
    {
      onEvent: (event) => {
        if (event.type === "tool_call") {
          console.log(`  🔧 Calling tool: ${event.name}(${JSON.stringify(event.args)})`);
        } else if (event.type === "tool_result") {
          console.log(`  ✓ Result: ${event.result}`);
        }
      },
    }
  );
  console.log("Assistant:", result1);
  console.log();

  // Example 2: Multi-step calculation
  console.log("Example 2: Multi-step calculation");
  console.log("User: Calculate (12 * 5) + (100 / 4)");
  const result2 = await agent.run(
    session.id,
    "Calculate (12 * 5) + (100 / 4)",
    {
      onEvent: (event) => {
        if (event.type === "tool_call") {
          console.log(`  🔧 Calling tool: ${event.name}(${JSON.stringify(event.args)})`);
        } else if (event.type === "tool_result") {
          console.log(`  ✓ Result: ${event.result}`);
        }
      },
    }
  );
  console.log("Assistant:", result2);
  console.log();

  // Example 3: Error handling
  console.log("Example 3: Error handling");
  console.log("User: What is 10 divided by 0?");
  const result3 = await agent.run(
    session.id,
    "What is 10 divided by 0?",
    {
      onEvent: (event) => {
        if (event.type === "tool_call") {
          console.log(`  🔧 Calling tool: ${event.name}(${JSON.stringify(event.args)})`);
        } else if (event.type === "tool_result") {
          console.log(`  ${event.isError ? '❌' : '✓'} Result: ${event.result}`);
        }
      },
    }
  );
  console.log("Assistant:", result3);
  console.log();

  // Clean up
  await agent.cleanup();
  console.log("✓ Done!");
}

main().catch(console.error);
