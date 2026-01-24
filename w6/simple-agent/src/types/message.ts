/**
 * Core message types for the agent system
 */

export interface Message {
  id: string;
  role: "user" | "assistant" | "tool";
  content: MessageContent[];
  createdAt: Date;
}

export type MessageContent =
  | TextContent
  | ToolCallContent
  | ToolResultContent;

export interface TextContent {
  type: "text";
  text: string;
}

export interface ToolCallContent {
  type: "tool_call";
  id: string;           // Tool call unique ID
  name: string;         // Tool name
  arguments: unknown;   // Tool arguments (JSON)
}

export interface ToolResultContent {
  type: "tool_result";
  toolCallId: string;   // Corresponding tool call ID
  result: string;       // Execution result
  isError?: boolean;    // Whether it's an error
}
