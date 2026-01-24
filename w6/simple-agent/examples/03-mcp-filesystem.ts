/**
 * Example 3: File Operations with MCP Server
 * Demonstrates how to integrate MCP servers to extend agent capabilities
 *
 * This example uses the filesystem MCP server.
 *
 * To run this example:
 * 1. Install the filesystem MCP server globally:
 *    npm install -g @modelcontextprotocol/server-filesystem
 *
 * 2. Or use npx to run it directly (no installation needed):
 *    This example uses npx, so you can run it without installation.
 *
 * 3. Run this example:
 *    npx tsx examples/03-mcp-filesystem.ts
 */

import { SimpleAgent } from "../src";
import * as path from "path";

async function main() {
  console.log("📁 File Operations with MCP Server\n");

  // Create the agent
  const agent = new SimpleAgent({
    model: "deepseek-chat",
    systemPrompt:
      "You are a helpful file management assistant. You can read, write, and list files in allowed directories.",
    temperature: 0.5,
  });

  try {
    // Add MCP filesystem server
    // This provides tools like: read_file, write_file, list_directory, etc.
    console.log("Connecting to MCP filesystem server...");

    const workingDir = process.cwd();

    await agent.addMCPServer({
      name: "filesystem",
      command: "npx",
      args: [
        "-y",
        "@modelcontextprotocol/server-filesystem",
        workingDir, // Allow access to current working directory
      ],
    });

    console.log("✓ MCP server connected");
    console.log("Available tools:", agent.listTools().map((t) => t.name).join(", "));
    console.log();

    // Create a session
    const session = agent.createSession();

    // Example 1: List files in a directory
    console.log("Example 1: List files in current directory");
    console.log("User: What files are in the current directory?\n");

    const result1 = await agent.run(
      session.id,
      "What files are in the current directory? Just give me a brief summary.",
      {
        onEvent: (event) => {
          if (event.type === "tool_call") {
            console.log(`  🔧 Calling: ${event.name}`);
          } else if (event.type === "tool_result") {
            if (event.isError) {
              console.log(`  ❌ Error: ${event.result}`);
            } else {
              console.log(`  ✓ Tool completed`);
            }
          }
        },
      }
    );
    console.log("Assistant:", result1);
    console.log();

    // Example 2: Read a specific file
    console.log("Example 2: Read package.json");
    console.log("User: Read the package.json file and tell me the project name\n");

    const result2 = await agent.run(
      session.id,
      "Read the package.json file and tell me the project name and version",
      {
        onEvent: (event) => {
          if (event.type === "tool_call") {
            console.log(`  🔧 Calling: ${event.name}`);
          } else if (event.type === "tool_result") {
            if (event.isError) {
              console.log(`  ❌ Error: ${event.result}`);
            } else {
              console.log(`  ✓ Tool completed`);
            }
          }
        },
      }
    );
    console.log("Assistant:", result2);
    console.log();

    // Example 3: Write a new file
    console.log("Example 3: Create a test file");
    console.log("User: Create a file called test-output.txt with a hello message\n");

    const result3 = await agent.run(
      session.id,
      "Create a file called test-output.txt with the content 'Hello from Simple Agent SDK!'",
      {
        onEvent: (event) => {
          if (event.type === "tool_call") {
            console.log(`  🔧 Calling: ${event.name}`);
          } else if (event.type === "tool_result") {
            if (event.isError) {
              console.log(`  ❌ Error: ${event.result}`);
            } else {
              console.log(`  ✓ Tool completed`);
            }
          }
        },
      }
    );
    console.log("Assistant:", result3);
    console.log();

    // Example 4: Verify the file was created
    console.log("Example 4: Verify the file");
    console.log("User: Read the test-output.txt file to verify it was created\n");

    const result4 = await agent.run(
      session.id,
      "Read the test-output.txt file and confirm its content",
      {
        onEvent: (event) => {
          if (event.type === "tool_call") {
            console.log(`  🔧 Calling: ${event.name}`);
          } else if (event.type === "tool_result") {
            if (event.isError) {
              console.log(`  ❌ Error: ${event.result}`);
            } else {
              console.log(`  ✓ Tool completed`);
            }
          }
        },
      }
    );
    console.log("Assistant:", result4);
    console.log();

    // Clean up
    await agent.cleanup();
    console.log("✓ Done!");
  } catch (error) {
    console.error("Error:", error);
    await agent.cleanup();
    process.exit(1);
  }
}

main().catch(console.error);
