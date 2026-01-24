/**
 * Session Manager - manages agent sessions
 */

import { v4 as uuidv4 } from "uuid";
import { Session, Message, Tool } from "../types";

export class SessionManager {
  private sessions: Map<string, Session> = new Map();

  /**
   * Create a new session
   */
  create(config: {
    systemPrompt: string;
    model: string;
    tools?: Tool[];
  }): Session {
    const session: Session = {
      id: uuidv4(),
      messages: [],
      systemPrompt: config.systemPrompt,
      model: config.model,
      tools: config.tools || [],
      status: "idle",
    };

    this.sessions.set(session.id, session);
    return session;
  }

  /**
   * Get a session by ID
   */
  get(id: string): Session | undefined {
    return this.sessions.get(id);
  }

  /**
   * Update a session
   */
  update(id: string, updates: Partial<Session>): boolean {
    const session = this.sessions.get(id);
    if (!session) {
      return false;
    }

    Object.assign(session, updates);
    return true;
  }

  /**
   * Delete a session
   */
  delete(id: string): boolean {
    return this.sessions.delete(id);
  }

  /**
   * Add a message to a session
   */
  addMessage(sessionId: string, message: Message): boolean {
    const session = this.sessions.get(sessionId);
    if (!session) {
      return false;
    }

    session.messages.push(message);
    return true;
  }

  /**
   * List all sessions
   */
  list(): Session[] {
    return Array.from(this.sessions.values());
  }

  /**
   * Clear all sessions
   */
  clear(): void {
    this.sessions.clear();
  }
}
