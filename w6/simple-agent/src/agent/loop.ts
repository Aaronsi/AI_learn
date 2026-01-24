/**
 * Agent - Core agent loop implementation
 */

import { v4 as uuidv4 } from "uuid";
import {
  Session,
  Message,
  MessageContent,
  ToolCallContent,
  TextContent,
  AgentEvent,
} from "../types";
import { LLMClient, LLMInput } from "../llm";
import { ToolRegistry } from "../tool/registry";
import { ToolExecutor } from "../tool/executor";

export interface AgentConfig {
  model: string;
  systemPrompt: string;
  maxSteps?: number; // Maximum loop iterations, prevents infinite loops
  temperature?: number;
  maxTokens?: number;
  onEvent?: (event: AgentEvent) => void;
}

/**
 * Run agent loop (non-streaming)
 */
export async function runAgent(
  session: Session,
  config: AgentConfig,
  llmClient: LLMClient,
  toolRegistry: ToolRegistry
): Promise<Message[]> {
  const executor = new ToolExecutor(toolRegistry);
  let step = 0;
  const maxSteps = config.maxSteps ?? 200;

  // Set session status
  session.status = "running";

  try {
    while (step < maxSteps) {
      step++;

      // Emit message start event
      config.onEvent?.({
        type: "message_start",
        role: "assistant",
      });

      // 1. Call LLM
      const llmInput: LLMInput = {
        model: config.model,
        messages: session.messages,
        systemPrompt: config.systemPrompt,
        tools: toolRegistry.toToolDefinitions(),
        temperature: config.temperature,
        maxTokens: config.maxTokens,
      };

      const response = await llmClient.call(llmInput);

      // 2. Create assistant message
      const assistantMessage: Message = {
        id: uuidv4(),
        role: "assistant",
        content: response.content,
        createdAt: new Date(),
      };
      session.messages.push(assistantMessage);

      // Emit text content
      for (const content of response.content) {
        if (content.type === "text") {
          config.onEvent?.({
            type: "text",
            text: (content as TextContent).text,
          });
        }
      }

      // 3. Check for tool calls
      const toolCalls = response.content.filter(
        (c) => c.type === "tool_call"
      ) as ToolCallContent[];

      if (toolCalls.length === 0) {
        // No tool calls, we're done
        config.onEvent?.({
          type: "message_end",
          finishReason: response.finishReason,
        });
        session.status = "completed";
        break;
      }

      // Emit tool call events
      for (const call of toolCalls) {
        config.onEvent?.({
          type: "tool_call",
          name: call.name,
          args: call.arguments,
        });
      }

      config.onEvent?.({
        type: "message_end",
        finishReason: response.finishReason,
      });

      // 4. Execute all tool calls in parallel
      const results = await executor.executeAll(toolCalls, {
        sessionId: session.id,
        messageId: assistantMessage.id,
      });

      // Emit tool result events
      for (const result of results) {
        config.onEvent?.({
          type: "tool_result",
          name: toolCalls.find((c) => c.id === result.toolCallId)?.name || "",
          result: result.result,
          isError: result.isError,
        });
      }

      // 5. Add tool results to message history
      const toolMessage: Message = {
        id: uuidv4(),
        role: "tool",
        content: results,
        createdAt: new Date(),
      };
      session.messages.push(toolMessage);

      // 6. Continue loop to let LLM process tool results
    }

    if (step >= maxSteps) {
      session.status = "error";
      config.onEvent?.({
        type: "error",
        error: new Error(
          `Maximum steps (${maxSteps}) reached. Agent may be in an infinite loop.`
        ),
      });
    }

    return session.messages;
  } catch (error) {
    session.status = "error";
    config.onEvent?.({
      type: "error",
      error: error as Error,
    });
    throw error;
  }
}
