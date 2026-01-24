/**
 * Simple Agent SDK
 * A simple and easy-to-use agent framework with tool calling and MCP support
 */

import { v4 as uuidv4 } from "uuid";
import {
  Tool,
  Session,
  Message,
  AgentEvent,
  MessageContent,
  TextContent,
} from "./types";
import { LLMClient, LLMClientConfig } from "./llm";
import { ToolRegistry } from "./tool/registry";
import { SessionManager } from "./session";
import { runAgent, streamAgent, AgentConfig } from "./agent";
import { MCPManager, MCPConfig } from "./mcp";

export interface SimpleAgentConfig {
  model?: string;
  systemPrompt?: string;
  temperature?: number;
  maxTokens?: number;
  maxSteps?: number;
  llmConfig?: LLMClientConfig;
}

/**
 * Simple Agent - Main SDK class
 */
export class SimpleAgent {
  private llmClient: LLMClient;
  private toolRegistry: ToolRegistry;
  private sessionManager: SessionManager;
  private mcpManager: MCPManager;
  private config: Required<SimpleAgentConfig>;

  constructor(config: SimpleAgentConfig = {}) {
    this.config = {
      model: config.model || "deepseek-chat",
      systemPrompt:
        config.systemPrompt ||
        "You are a helpful AI assistant with access to tools.",
      temperature: config.temperature ?? 0.7,
      maxTokens: config.maxTokens ?? 4096,
      maxSteps: config.maxSteps ?? 200,
      llmConfig: config.llmConfig || {},
    };

    this.llmClient = new LLMClient(this.config.llmConfig);
    this.toolRegistry = new ToolRegistry();
    this.sessionManager = new SessionManager();
    this.mcpManager = new MCPManager();
  }

  /**
   * Add a custom tool
   */
  addTool(tool: Tool): void {
    this.toolRegistry.register(tool);
  }

  /**
   * Add multiple custom tools
   */
  addTools(tools: Tool[]): void {
    this.toolRegistry.registerAll(tools);
  }

  /**
   * Remove a tool by name
   */
  removeTool(name: string): boolean {
    return this.toolRegistry.unregister(name);
  }

  /**
   * List all registered tools
   */
  listTools(): Tool[] {
    return this.toolRegistry.list();
  }

  /**
   * Add an MCP server and load its tools
   */
  async addMCPServer(config: MCPConfig): Promise<void> {
    const client = await this.mcpManager.addServer(config);
    const tools = await client.listTools();
    this.toolRegistry.registerAll(tools);
  }

  /**
   * Remove an MCP server and its tools
   */
  async removeMCPServer(name: string): Promise<boolean> {
    // Note: This doesn't remove the tools, they remain registered
    // Users can manually remove tools if needed
    return this.mcpManager.removeServer(name);
  }

  /**
   * Create a new session
   */
  createSession(config?: {
    systemPrompt?: string;
    model?: string;
  }): Session {
    return this.sessionManager.create({
      systemPrompt: config?.systemPrompt || this.config.systemPrompt,
      model: config?.model || this.config.model,
      tools: this.toolRegistry.list(),
    });
  }

  /**
   * Add a user message to a session
   */
  addMessage(sessionId: string, content: string): Message {
    const message: Message = {
      id: uuidv4(),
      role: "user",
      content: [{ type: "text", text: content }],
      createdAt: new Date(),
    };

    this.sessionManager.addMessage(sessionId, message);
    return message;
  }

  /**
   * Run the agent (non-streaming)
   */
  async run(
    sessionId: string,
    userMessage?: string,
    config?: Partial<AgentConfig>
  ): Promise<string> {
    const session = this.sessionManager.get(sessionId);
    if (!session) {
      throw new Error(`Session not found: ${sessionId}`);
    }

    // Add user message if provided
    if (userMessage) {
      this.addMessage(sessionId, userMessage);
    }

    // Run agent loop
    const agentConfig: AgentConfig = {
      model: config?.model || this.config.model,
      systemPrompt: config?.systemPrompt || session.systemPrompt,
      temperature: config?.temperature ?? this.config.temperature,
      maxTokens: config?.maxTokens ?? this.config.maxTokens,
      maxSteps: config?.maxSteps ?? this.config.maxSteps,
      onEvent: config?.onEvent,
    };

    await runAgent(session, agentConfig, this.llmClient, this.toolRegistry);

    // Extract the last assistant message text
    const lastMessage = session.messages[session.messages.length - 1];
    if (lastMessage && lastMessage.role === "assistant") {
      const textContent = lastMessage.content.find(
        (c) => c.type === "text"
      ) as TextContent | undefined;
      return textContent?.text || "";
    }

    return "";
  }

  /**
   * Run the agent with streaming
   */
  async *stream(
    sessionId: string,
    userMessage?: string,
    config?: Partial<AgentConfig>
  ): AsyncGenerator<AgentEvent> {
    const session = this.sessionManager.get(sessionId);
    if (!session) {
      throw new Error(`Session not found: ${sessionId}`);
    }

    // Add user message if provided
    if (userMessage) {
      this.addMessage(sessionId, userMessage);
    }

    // Run streaming agent loop
    const agentConfig: AgentConfig = {
      model: config?.model || this.config.model,
      systemPrompt: config?.systemPrompt || session.systemPrompt,
      temperature: config?.temperature ?? this.config.temperature,
      maxTokens: config?.maxTokens ?? this.config.maxTokens,
      maxSteps: config?.maxSteps ?? this.config.maxSteps,
    };

    yield* streamAgent(session, agentConfig, this.llmClient, this.toolRegistry);
  }

  /**
   * Get a session by ID
   */
  getSession(sessionId: string): Session | undefined {
    return this.sessionManager.get(sessionId);
  }

  /**
   * Get all messages from a session
   */
  getMessages(sessionId: string): Message[] {
    const session = this.sessionManager.get(sessionId);
    return session?.messages || [];
  }

  /**
   * Delete a session
   */
  deleteSession(sessionId: string): boolean {
    return this.sessionManager.delete(sessionId);
  }

  /**
   * Clean up all resources
   */
  async cleanup(): Promise<void> {
    await this.mcpManager.disconnectAll();
  }
}

// Re-export types for convenience
export * from "./types";
export * from "./mcp";
export { Tool, ToolResult, JSONSchema } from "./types";
