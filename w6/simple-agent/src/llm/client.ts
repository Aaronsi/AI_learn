/**
 * DeepSeek LLM client with streaming support
 * Compatible with OpenAI API format
 */

import OpenAI from "openai";
import {
  Message,
  MessageContent,
  TextContent,
  ToolCallContent,
  ToolDefinition,
  LLMEvent,
  Usage,
} from "../types";

export interface LLMInput {
  model: string;
  messages: Message[];
  systemPrompt: string;
  tools: ToolDefinition[];
  temperature?: number;
  maxTokens?: number;
  abortSignal?: AbortSignal;
}

export interface LLMOutput {
  content: MessageContent[];
  finishReason: string;
  usage: Usage;
}

export interface LLMClientConfig {
  apiKey?: string;
  baseURL?: string;
}

export class LLMClient {
  private client: OpenAI;

  constructor(config?: LLMClientConfig) {
    this.client = new OpenAI({
      apiKey: config?.apiKey || process.env.DEEPSEEK_API_KEY || process.env.OPENAI_API_KEY,
      baseURL: config?.baseURL || process.env.DEEPSEEK_BASE_URL || "https://api.deepseek.com",
    });
  }

  /**
   * Convert internal message format to OpenAI format
   */
  private convertMessages(
    messages: Message[],
    systemPrompt: string
  ): OpenAI.Chat.ChatCompletionMessageParam[] {
    const result: OpenAI.Chat.ChatCompletionMessageParam[] = [];

    // Add system message
    if (systemPrompt) {
      result.push({
        role: "system",
        content: systemPrompt,
      });
    }

    // Convert messages
    for (const msg of messages) {
      if (msg.role === "user") {
        const textContent = msg.content.find((c) => c.type === "text") as
          | TextContent
          | undefined;
        result.push({
          role: "user",
          content: textContent?.text || "",
        });
      } else if (msg.role === "assistant") {
        const textParts = msg.content.filter((c) => c.type === "text") as TextContent[];
        const toolCalls = msg.content.filter((c) => c.type === "tool_call") as ToolCallContent[];

        const message: OpenAI.Chat.ChatCompletionAssistantMessageParam = {
          role: "assistant",
          content: textParts.map((t) => t.text).join("") || null,
        };

        if (toolCalls.length > 0) {
          message.tool_calls = toolCalls.map((tc) => ({
            id: tc.id,
            type: "function" as const,
            function: {
              name: tc.name,
              arguments: JSON.stringify(tc.arguments),
            },
          }));
        }

        result.push(message);
      } else if (msg.role === "tool") {
        // Tool results
        for (const content of msg.content) {
          if (content.type === "tool_result") {
            result.push({
              role: "tool",
              tool_call_id: content.toolCallId,
              content: content.result,
            });
          }
        }
      }
    }

    return result;
  }

  /**
   * Non-streaming LLM call
   */
  async call(input: LLMInput): Promise<LLMOutput> {
    const messages = this.convertMessages(input.messages, input.systemPrompt);

    const response = await this.client.chat.completions.create({
      model: input.model,
      messages,
      tools: input.tools.length > 0 ? input.tools : undefined,
      temperature: input.temperature,
      max_tokens: input.maxTokens,
    });

    const choice = response.choices[0];
    const content: MessageContent[] = [];

    // Add text content
    if (choice.message.content) {
      content.push({
        type: "text",
        text: choice.message.content,
      });
    }

    // Add tool calls
    if (choice.message.tool_calls) {
      for (const toolCall of choice.message.tool_calls) {
        if (toolCall.type === "function") {
          content.push({
            type: "tool_call",
            id: toolCall.id,
            name: toolCall.function.name,
            arguments: JSON.parse(toolCall.function.arguments),
          });
        }
      }
    }

    return {
      content,
      finishReason: choice.finish_reason || "stop",
      usage: {
        inputTokens: response.usage?.prompt_tokens || 0,
        outputTokens: response.usage?.completion_tokens || 0,
        totalTokens: response.usage?.total_tokens || 0,
      },
    };
  }

  /**
   * Streaming LLM call
   */
  async *stream(input: LLMInput): AsyncGenerator<LLMEvent> {
    const messages = this.convertMessages(input.messages, input.systemPrompt);

    try {
      const stream = await this.client.chat.completions.create({
        model: input.model,
        messages,
        tools: input.tools.length > 0 ? input.tools : undefined,
        temperature: input.temperature,
        max_tokens: input.maxTokens,
        stream: true,
      });

      const toolCallsMap = new Map<
        number,
        { id: string; name: string; arguments: string }
      >();

      for await (const chunk of stream) {
        const delta = chunk.choices[0]?.delta;

        if (!delta) continue;

        // Text delta
        if (delta.content) {
          yield {
            type: "text_delta",
            text: delta.content,
          };
        }

        // Tool calls
        if (delta.tool_calls) {
          for (const toolCall of delta.tool_calls) {
            const index = toolCall.index;
            const existing = toolCallsMap.get(index);

            if (!existing) {
              // New tool call
              const id = toolCall.id || "";
              const name = toolCall.function?.name || "";
              toolCallsMap.set(index, { id, name, arguments: "" });

              yield {
                type: "tool_call_start",
                id,
                name,
              };
            }

            // Accumulate arguments
            if (toolCall.function?.arguments) {
              const current = toolCallsMap.get(index)!;
              current.arguments += toolCall.function.arguments;

              yield {
                type: "tool_call_delta",
                id: current.id,
                arguments: toolCall.function.arguments,
              };
            }
          }
        }

        // Finish
        if (chunk.choices[0]?.finish_reason) {
          // Emit tool_call_end for all tool calls
          for (const [_, toolCall] of toolCallsMap) {
            let parsedArgs: unknown;
            try {
              parsedArgs = JSON.parse(toolCall.arguments);
            } catch {
              parsedArgs = {};
            }

            yield {
              type: "tool_call_end",
              id: toolCall.id,
              name: toolCall.name,
              arguments: parsedArgs,
            };
          }

          yield {
            type: "finish",
            reason: chunk.choices[0].finish_reason,
            usage: {
              inputTokens: 0,
              outputTokens: 0,
              totalTokens: 0,
            },
          };
        }
      }
    } catch (error) {
      yield {
        type: "error",
        error: error as Error,
      };
    }
  }
}
