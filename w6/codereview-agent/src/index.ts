/**
 * Code Review Agent
 * Main entry point for the code review agent
 */

import { SimpleAgent } from "simple-agent";
import * as fs from "fs";
import * as path from "path";
import {
  readFileTool,
  writeFileTool,
  gitCommandTool,
  ghCommandTool,
} from "./tools";

// Load system prompt
const systemPromptPath = path.join(__dirname, "../prompts/system.md");
let systemPrompt: string;

try {
  systemPrompt = fs.readFileSync(systemPromptPath, "utf-8");
} catch (error) {
  // Try alternate paths (for different build configurations)
  const alternatePath = path.join(process.cwd(), "prompts/system.md");
  try {
    systemPrompt = fs.readFileSync(alternatePath, "utf-8");
  } catch {
    throw new Error(
      `Failed to load system prompt from ${systemPromptPath} or ${alternatePath}. ` +
        `Please ensure prompts/system.md exists.`
    );
  }
}

export interface CodeReviewAgentConfig {
  model?: string;
  apiKey?: string;
  baseURL?: string;
  temperature?: number;
  maxTokens?: number;
  maxSteps?: number;
}

/**
 * Create a code review agent instance
 */
export function createCodeReviewAgent(
  config: CodeReviewAgentConfig = {}
): SimpleAgent {
  const agent = new SimpleAgent({
    model: config.model || "deepseek-chat",
    systemPrompt,
    temperature: config.temperature ?? 0.7,
    maxTokens: config.maxTokens ?? 4096,
    maxSteps: config.maxSteps ?? 50,
    llmConfig: {
      apiKey: config.apiKey,
      baseURL: config.baseURL,
    },
  });

  // Register tools
  agent.addTools([readFileTool, writeFileTool, gitCommandTool, ghCommandTool]);

  return agent;
}

/**
 * Run code review with a user message
 */
export async function runCodeReview(
  userMessage: string,
  config: CodeReviewAgentConfig = {}
): Promise<string> {
  const agent = createCodeReviewAgent(config);
  const session = agent.createSession();

  try {
    const response = await agent.run(session.id, userMessage);
    return response;
  } catch (error) {
    throw new Error(`Code review failed: ${(error as Error).message}`);
  }
}

/**
 * Run code review with streaming output
 */
export async function* streamCodeReview(
  userMessage: string,
  config: CodeReviewAgentConfig = {}
): AsyncGenerator<string> {
  const agent = createCodeReviewAgent(config);
  const session = agent.createSession();

  try {
    for await (const event of agent.stream(session.id, userMessage)) {
      if (event.type === "text") {
        yield event.text;
      } else if (event.type === "tool_call") {
        // Optionally show tool calls
        // yield `\n[Calling ${event.name}...]\n`;
      } else if (event.type === "error") {
        throw event.error;
      }
    }
  } catch (error) {
    throw new Error(`Code review failed: ${(error as Error).message}`);
  }
}

// Export tools for advanced usage
export * from "./tools";

