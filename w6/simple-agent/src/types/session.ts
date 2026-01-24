/**
 * Session management types
 */

import { Message } from "./message";
import { Tool } from "./tool";

export interface Session {
  id: string;
  messages: Message[];
  systemPrompt: string;
  model: string;
  tools: Tool[];
  status: "idle" | "running" | "completed" | "error";
}

export interface ModelConfig {
  model: string;
  temperature?: number;
  maxTokens?: number;
  topP?: number;
}
