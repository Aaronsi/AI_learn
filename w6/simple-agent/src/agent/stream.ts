/**
 * Streaming Agent - Core agent loop with streaming support
 */

import { v4 as uuidv4 } from "uuid";
import {
  Session,
  Message,
  MessageContent,
  ToolCallContent,
  AgentEvent,
  LLMEvent,
} from "../types";
import { LLMClient, LLMInput } from "../llm";
import { ToolRegistry } from "../tool/registry";
import { ToolExecutor } from "../tool/executor";
import { AgentConfig } from "./loop";

/**
 * Run agent loop with streaming support
 */
export async function* streamAgent(
  session: Session,
  config: AgentConfig,
  llmClient: LLMClient,
  toolRegistry: ToolRegistry
): AsyncGenerator<AgentEvent> {
  const executor = new ToolExecutor(toolRegistry);
  let step = 0;
  const maxSteps = config.maxSteps ?? 200;

  session.status = "running";

  try {
    while (step < maxSteps) {
      step++;

      yield { type: "message_start", role: "assistant" };

      const content: MessageContent[] = [];
      const toolCallsMap = new Map<
        string,
        { id: string; name: string; arguments: string }
      >();
      let textBuffer = "";

      // 1. Stream LLM response
      const llmInput: LLMInput = {
        model: config.model,
        messages: session.messages,
        systemPrompt: config.systemPrompt,
        tools: toolRegistry.toToolDefinitions(),
        temperature: config.temperature,
        maxTokens: config.maxTokens,
      };

      let finishReason = "stop";

      for await (const event of llmClient.stream(llmInput)) {
        switch (event.type) {
          case "text_delta":
            textBuffer += event.text;
            yield { type: "text", text: event.text };
            break;

          case "tool_call_start":
            toolCallsMap.set(event.id, {
              id: event.id,
              name: event.name,
              arguments: "",
            });
            break;

          case "tool_call_delta":
            const existing = toolCallsMap.get(event.id);
            if (existing) {
              existing.arguments += event.arguments;
            }
            break;

          case "tool_call_end":
            const toolCall = toolCallsMap.get(event.id);
            if (toolCall) {
              toolCall.name = event.name;
              toolCall.arguments =
                typeof event.arguments === "string"
                  ? event.arguments
                  : JSON.stringify(event.arguments);

              yield {
                type: "tool_call",
                name: event.name,
                args: event.arguments,
              };
            }
            break;

          case "finish":
            finishReason = event.reason;
            break;

          case "error":
            yield { type: "error", error: event.error };
            throw event.error;
        }
      }

      // 2. Build content array
      if (textBuffer) {
        content.push({
          type: "text",
          text: textBuffer,
        });
      }

      // Add tool calls to content
      for (const [_, toolCall] of toolCallsMap) {
        let parsedArgs: unknown;
        try {
          parsedArgs = JSON.parse(toolCall.arguments);
        } catch {
          parsedArgs = {};
        }

        content.push({
          type: "tool_call",
          id: toolCall.id,
          name: toolCall.name,
          arguments: parsedArgs,
        });
      }

      // 3. Save assistant message
      const assistantMessage: Message = {
        id: uuidv4(),
        role: "assistant",
        content,
        createdAt: new Date(),
      };
      session.messages.push(assistantMessage);

      yield { type: "message_end", finishReason };

      // 4. Check if there are tool calls
      const toolCalls = content.filter(
        (c) => c.type === "tool_call"
      ) as ToolCallContent[];

      if (toolCalls.length === 0) {
        // No tool calls, we're done
        session.status = "completed";
        break;
      }

      // 5. Execute tools
      const results = await executor.executeAll(toolCalls, {
        sessionId: session.id,
        messageId: assistantMessage.id,
      });

      // Emit tool result events
      for (const result of results) {
        yield {
          type: "tool_result",
          name: toolCalls.find((c) => c.id === result.toolCallId)?.name || "",
          result: result.result,
          isError: result.isError,
        };
      }

      // 6. Save tool results
      const toolMessage: Message = {
        id: uuidv4(),
        role: "tool",
        content: results,
        createdAt: new Date(),
      };
      session.messages.push(toolMessage);

      // 7. Continue loop
    }

    if (step >= maxSteps) {
      session.status = "error";
      yield {
        type: "error",
        error: new Error(
          `Maximum steps (${maxSteps}) reached. Agent may be in an infinite loop.`
        ),
      };
    }
  } catch (error) {
    session.status = "error";
    yield {
      type: "error",
      error: error as Error,
    };
  }
}
