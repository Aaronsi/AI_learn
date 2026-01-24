/**
 * Agent event types for streaming
 */

export type AgentEvent =
  | { type: "message_start"; role: "assistant" }
  | { type: "text"; text: string }
  | { type: "tool_call"; name: string; args: unknown }
  | { type: "tool_result"; name: string; result: string; isError?: boolean }
  | { type: "message_end"; finishReason: string }
  | { type: "error"; error: Error };

export type LLMEvent =
  | { type: "text_delta"; text: string }
  | { type: "tool_call_start"; id: string; name: string }
  | { type: "tool_call_delta"; id: string; arguments: string }
  | { type: "tool_call_end"; id: string; name: string; arguments: unknown }
  | { type: "finish"; reason: string; usage: Usage }
  | { type: "error"; error: Error };

export interface Usage {
  inputTokens: number;
  outputTokens: number;
  totalTokens: number;
}
