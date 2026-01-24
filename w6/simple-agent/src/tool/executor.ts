/**
 * Tool Executor - executes tool calls and handles results
 */

import { ToolCallContent, ToolResultContent } from "../types";
import { ToolRegistry } from "./registry";

export interface ExecutionContext {
  sessionId: string;
  messageId: string;
  abortSignal?: AbortSignal;
}

export class ToolExecutor {
  constructor(private registry: ToolRegistry) {}

  /**
   * Execute a single tool call
   */
  async execute(
    call: ToolCallContent,
    ctx: ExecutionContext
  ): Promise<ToolResultContent> {
    // Check if aborted
    if (ctx.abortSignal?.aborted) {
      return {
        type: "tool_result",
        toolCallId: call.id,
        result: "Execution aborted",
        isError: true,
      };
    }

    // Get the tool
    const tool = this.registry.get(call.name);
    if (!tool) {
      return {
        type: "tool_result",
        toolCallId: call.id,
        result: `Tool not found: ${call.name}`,
        isError: true,
      };
    }

    try {
      // Execute the tool
      const result = await tool.execute(call.arguments);

      // Check if the tool returned an error
      if (result.error) {
        return {
          type: "tool_result",
          toolCallId: call.id,
          result: result.error,
          isError: true,
        };
      }

      return {
        type: "tool_result",
        toolCallId: call.id,
        result: result.output,
        isError: false,
      };
    } catch (error) {
      const errorMessage =
        error instanceof Error ? error.message : String(error);
      return {
        type: "tool_result",
        toolCallId: call.id,
        result: `Error executing tool '${call.name}': ${errorMessage}`,
        isError: true,
      };
    }
  }

  /**
   * Execute multiple tool calls in parallel
   */
  async executeAll(
    calls: ToolCallContent[],
    ctx: ExecutionContext
  ): Promise<ToolResultContent[]> {
    return Promise.all(calls.map((call) => this.execute(call, ctx)));
  }

  /**
   * Execute multiple tool calls sequentially (one after another)
   */
  async executeSequential(
    calls: ToolCallContent[],
    ctx: ExecutionContext
  ): Promise<ToolResultContent[]> {
    const results: ToolResultContent[] = [];
    for (const call of calls) {
      const result = await this.execute(call, ctx);
      results.push(result);
    }
    return results;
  }
}
