/**
 * MCP (Model Context Protocol) Client Integration
 */

import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { StdioClientTransport } from "@modelcontextprotocol/sdk/client/stdio.js";
import { Tool, ToolResult, JSONSchema } from "../types";

export interface MCPConfig {
  name: string;
  command: string;
  args?: string[];
  env?: Record<string, string>;
}

/**
 * MCP Client wrapper
 */
export class MCPClient {
  private client: Client;
  private transport: StdioClientTransport | null = null;
  private isConnected = false;
  public readonly name: string;

  constructor(public readonly config: MCPConfig) {
    this.name = config.name;
    this.client = new Client(
      {
        name: `simple-agent-${config.name}`,
        version: "1.0.0",
      },
      {
        capabilities: {},
      }
    );
  }

  /**
   * Connect to the MCP server
   */
  async connect(): Promise<void> {
    if (this.isConnected) {
      return;
    }

    this.transport = new StdioClientTransport({
      command: this.config.command,
      args: this.config.args || [],
      env: this.config.env,
    });

    await this.client.connect(this.transport);
    this.isConnected = true;
  }

  /**
   * Disconnect from the MCP server
   */
  async disconnect(): Promise<void> {
    if (!this.isConnected) {
      return;
    }

    await this.client.close();
    this.isConnected = false;
    this.transport = null;
  }

  /**
   * List all tools available from the MCP server
   */
  async listTools(): Promise<Tool[]> {
    if (!this.isConnected) {
      await this.connect();
    }

    const response = await this.client.listTools();
    return response.tools.map((mcpTool) => this.adaptMCPTool(mcpTool));
  }

  /**
   * Call a tool on the MCP server
   */
  async callTool(name: string, args: unknown): Promise<ToolResult> {
    if (!this.isConnected) {
      await this.connect();
    }

    try {
      const response = await this.client.callTool({
        name,
        arguments: args as Record<string, unknown>,
      });

      // Extract text content from the response
      const content = Array.isArray(response.content) ? response.content : [];
      const textContent = content
        .filter((c: any) => c.type === "text")
        .map((c: any) => c.text)
        .join("\n");

      return {
        output: textContent || JSON.stringify(response.content),
        metadata: {
          isError: response.isError,
        },
        error: response.isError ? textContent : undefined,
      };
    } catch (error) {
      const errorMessage =
        error instanceof Error ? error.message : String(error);
      return {
        output: "",
        error: errorMessage,
      };
    }
  }

  /**
   * Adapt MCP tool definition to our Tool interface
   */
  private adaptMCPTool(mcpTool: any): Tool {
    return {
      name: mcpTool.name,
      description: mcpTool.description || "",
      parameters: mcpTool.inputSchema as JSONSchema,
      execute: async (args: unknown) => {
        return this.callTool(mcpTool.name, args);
      },
    };
  }
}

/**
 * MCP Manager - manages multiple MCP clients
 */
export class MCPManager {
  private clients: Map<string, MCPClient> = new Map();

  /**
   * Add an MCP server
   */
  async addServer(config: MCPConfig): Promise<MCPClient> {
    if (this.clients.has(config.name)) {
      throw new Error(`MCP server '${config.name}' already exists`);
    }

    const client = new MCPClient(config);
    await client.connect();
    this.clients.set(config.name, client);
    return client;
  }

  /**
   * Remove an MCP server
   */
  async removeServer(name: string): Promise<boolean> {
    const client = this.clients.get(name);
    if (!client) {
      return false;
    }

    await client.disconnect();
    return this.clients.delete(name);
  }

  /**
   * Get an MCP client by name
   */
  getClient(name: string): MCPClient | undefined {
    return this.clients.get(name);
  }

  /**
   * List all MCP clients
   */
  listClients(): MCPClient[] {
    return Array.from(this.clients.values());
  }

  /**
   * Get all tools from all connected MCP servers
   */
  async getAllTools(): Promise<Tool[]> {
    const allTools: Tool[] = [];
    for (const client of this.clients.values()) {
      const tools = await client.listTools();
      allTools.push(...tools);
    }
    return allTools;
  }

  /**
   * Disconnect all MCP servers
   */
  async disconnectAll(): Promise<void> {
    const promises = Array.from(this.clients.values()).map((client) =>
      client.disconnect()
    );
    await Promise.all(promises);
    this.clients.clear();
  }
}
