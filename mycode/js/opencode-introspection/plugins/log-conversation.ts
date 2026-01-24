import type { Hooks, PluginInput } from "@opencode-ai/plugin"
import { existsSync, mkdirSync } from "fs"
import { appendFileSync } from "fs"
import { join } from "path"
import { randomUUID } from "crypto"

// Turn 状态跟踪
interface TurnState {
  sessionID: string
  conversationID: string
  turnID: string
  timestamp: number
  input: {
    messages: Array<{
      info: any
      parts: any[]
    }>
    systemPrompts?: string[]  // 系统提示
    params?: {
      temperature?: number
      topP?: number
      topK?: number
      options?: Record<string, any>
    }
  }
  output: {
    textParts: Array<{
      partID: string
      text: string
      timestamp: number
    }>
    toolCalls: Array<{
      callID: string
      tool: string
      args: any
      result?: {
        title: string
        output: string
        metadata: any
      }
      timestamp: number
    }>
  }
  // 用于跟踪是否已经完成
  completed: boolean
}

// 对话状态跟踪
interface ConversationState {
  conversationID: string
  sessionID: string
  startTime: number
  logFile: string
  completed: boolean
}

// 存储每个 session 的当前 turn 状态
const turnStates = new Map<string, TurnState>()
// 存储每个 session 的当前对话状态
const activeConversations = new Map<string, ConversationState>()
// 存储最近的消息转换，用于关联 sessionID
const pendingMessages = new Map<string, Array<{ info: any; parts: any[] }>>()
// 存储项目目录路径
let projectDirectory: string | undefined

// 生成简短的对话 ID（UUID 前 8 位）
function generateConversationID(): string {
  return randomUUID().replace(/-/g, "").substring(0, 8)
}

// 确保 logs 目录存在
function ensureLogsDir(): string {
  // 使用项目目录，如果未设置则使用当前工作目录
  const baseDir = projectDirectory || process.cwd()
  const logsDir = join(baseDir, "logs")
  console.log("[log-conversation] Ensuring logs directory exists:", logsDir)
  if (!existsSync(logsDir)) {
    console.log("[log-conversation] Creating logs directory:", logsDir)
    mkdirSync(logsDir, { recursive: true })
  }
  console.log("[log-conversation] Logs directory ready:", logsDir)
  return logsDir
}

// 获取或创建当前对话的日志文件路径
function getConversationLogFile(sessionID: string, conversationID: string): string {
  const logsDir = ensureLogsDir()
  const logFile = join(logsDir, `session-${sessionID}-${conversationID}.jsonl`)
  return logFile
}

// 写入 turn 到 jsonl 文件
function writeTurnToFile(sessionID: string, conversationID: string, turn: TurnState) {
  try {
    const logFile = getConversationLogFile(sessionID, conversationID)
    console.log("[log-conversation] Writing turn to file:", logFile)
    console.log("[log-conversation] Turn data:", {
      turnID: turn.turnID,
      hasMessages: turn.input.messages.length > 0,
      hasParams: !!turn.input.params,
      textPartsCount: turn.output.textParts.length,
      toolCallsCount: turn.output.toolCalls.length,
    })
    
    const turnRecord = {
      turnID: turn.turnID,
      timestamp: turn.timestamp,
      input: turn.input,
      output: turn.output,
    }
    
    const jsonLine = JSON.stringify(turnRecord) + "\n"
    appendFileSync(logFile, jsonLine)
    console.log("[log-conversation] Successfully wrote turn to file:", logFile)
  } catch (error) {
    console.error("[log-conversation] Error writing turn to file:", error)
    throw error
  }
}

// 开始新的对话
function startNewConversation(sessionID: string): ConversationState {
  // 完成之前的对话（如果存在）
  const previousConversation = activeConversations.get(sessionID)
  if (previousConversation && !previousConversation.completed) {
    completeConversation(sessionID)
  }

  const conversationID = generateConversationID()
  const logFile = getConversationLogFile(sessionID, conversationID)
  
  const conversation: ConversationState = {
    conversationID,
    sessionID,
    startTime: Date.now(),
    logFile,
    completed: false,
  }
  
  activeConversations.set(sessionID, conversation)
  return conversation
}

// 获取当前对话
function getCurrentConversation(sessionID: string): ConversationState | undefined {
  return activeConversations.get(sessionID)
}

// 完成当前对话
function completeConversation(sessionID: string) {
  const conversation = activeConversations.get(sessionID)
  if (conversation && !conversation.completed) {
    conversation.completed = true
    // 对话完成后，保留状态但不删除，以便后续可能需要查询
  }
}

// 开始新的 turn
function startNewTurn(sessionID: string, conversationID: string): TurnState {
  // 完成之前的 turn（如果存在）
  const previousTurn = turnStates.get(sessionID)
  if (previousTurn && !previousTurn.completed) {
    console.log("[log-conversation] Completing previous turn before starting new turn")
    // 立即完成之前的 turn，确保数据被写入
    completeTurn(sessionID)
  }

  const turnID = `${sessionID}-${conversationID}-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`
  const turn: TurnState = {
    sessionID,
    conversationID,
    turnID,
    timestamp: Date.now(),
    input: {
      messages: [],
    },
    output: {
      textParts: [],
      toolCalls: [],
    },
    completed: false,
  }
  turnStates.set(sessionID, turn)
  console.log("[log-conversation] Created new turn:", turnID, "for conversation:", conversationID)
  return turn
}

// 获取当前 turn
function getCurrentTurn(sessionID: string): TurnState | undefined {
  return turnStates.get(sessionID)
}

// 完成当前 turn 并写入文件
function completeTurn(sessionID: string) {
  const turn = turnStates.get(sessionID)
  if (turn && !turn.completed) {
    try {
      console.log("[log-conversation] Completing turn, sessionID:", sessionID, "conversationID:", turn.conversationID)
      writeTurnToFile(sessionID, turn.conversationID, turn)
      turn.completed = true
      console.log("[log-conversation] Turn completed and written to file")
      // 不删除 turn，保留它以便后续可能需要追加数据
      // 但标记为已完成，下次 startNewTurn 时会写入
    } catch (error) {
      console.error("[log-conversation] Error completing turn:", error)
    }
  }
}

export default async function (input: PluginInput): Promise<Hooks> {
  // 保存项目目录路径
  projectDirectory = input.directory
  
  // 调试：确认 plugin 被加载
  console.log("[log-conversation] Plugin loaded successfully")
  console.log("[log-conversation] Project directory:", projectDirectory)
  
  return {
    // 捕获用户消息 - 这是新对话开始的标志
    "chat.message": async (input, output) => {
      try {
        const { sessionID } = input
        console.log("[log-conversation] chat.message hook triggered, sessionID:", sessionID)
        
        // 完成之前的 turn（如果有且未完成）
        const previousTurn = getCurrentTurn(sessionID)
        if (previousTurn && !previousTurn.completed) {
          console.log("[log-conversation] Completing previous turn before starting new message")
          completeTurn(sessionID)
        }
        
        // 开始新的对话
        const conversation = startNewConversation(sessionID)
        
        // 创建新的 turn
        const turn = startNewTurn(sessionID, conversation.conversationID)
        console.log("[log-conversation] Started new turn:", turn.turnID)
      } catch (error) {
        console.error("[log-conversation] Error in chat.message hook:", error)
      }
    },

    // 捕获系统提示
    "experimental.chat.system.transform": async (input, output) => {
      try {
        const { sessionID } = input
        console.log("[log-conversation] experimental.chat.system.transform hook triggered, sessionID:", sessionID)
        console.log("[log-conversation] System prompts:", output.system)
        
        // 确保有当前对话
        let conversation = getCurrentConversation(sessionID)
        if (!conversation) {
          conversation = startNewConversation(sessionID)
        }
        
        // 获取或创建当前 turn
        let turn = getCurrentTurn(sessionID)
        if (!turn) {
          turn = startNewTurn(sessionID, conversation.conversationID)
        } else {
          // 确保 turn 的 conversationID 正确
          turn.conversationID = conversation.conversationID
        }
        
        // 记录系统提示
        turn.input.systemPrompts = output.system
        console.log("[log-conversation] Recorded system prompts, count:", output.system.length)
      } catch (error) {
        console.error("[log-conversation] Error in experimental.chat.system.transform hook:", error)
      }
    },

    // 捕获完整的 messages 数组（输入）
    // 注意：这个 hook 没有 sessionID，但我们可以从 messages 中提取
    "experimental.chat.messages.transform": async (_input, output) => {
      try {
        console.log("[log-conversation] experimental.chat.messages.transform hook triggered")
        // 从 messages 中提取 sessionID（从第一个 message 的 parts 中）
        let sessionID: string | undefined
        for (const msg of output.messages) {
          if (msg.parts && msg.parts.length > 0 && msg.parts[0].sessionID) {
            sessionID = msg.parts[0].sessionID
            break
          }
        }

        if (sessionID) {
          console.log("[log-conversation] Found sessionID in messages:", sessionID)
          // 确保有当前对话
          let conversation = getCurrentConversation(sessionID)
          if (!conversation) {
            conversation = startNewConversation(sessionID)
          }
          
          // 获取或创建当前 turn
          let turn = getCurrentTurn(sessionID)
          if (!turn) {
            turn = startNewTurn(sessionID, conversation.conversationID)
          } else {
            // 确保 turn 的 conversationID 正确
            turn.conversationID = conversation.conversationID
          }
          // 记录 messages
          turn.input.messages = output.messages
          console.log("[log-conversation] Recorded messages, count:", output.messages.length)
        } else {
          console.warn("[log-conversation] No sessionID found in messages, storing to pending queue")
          // 如果没有找到 sessionID，存储到 pending 队列
          const messagesKey = `messages-${Date.now()}`
          pendingMessages.set(messagesKey, output.messages)
          setTimeout(() => {
            pendingMessages.delete(messagesKey)
          }, 5000)
        }
      } catch (error) {
        console.error("[log-conversation] Error in experimental.chat.messages.transform hook:", error)
      }
    },

    // 捕获参数（输入的一部分）- 这是 LLM 调用前的关键 hook
    "chat.params": async (input, output) => {
      try {
        const { sessionID } = input
        console.log("[log-conversation] chat.params hook triggered, sessionID:", sessionID)
        
        // 确保有当前对话
        let conversation = getCurrentConversation(sessionID)
        if (!conversation) {
          conversation = startNewConversation(sessionID)
        }
        
        // 获取或创建当前 turn（messages.transform 可能已经创建了）
        let turn = getCurrentTurn(sessionID)
        if (!turn) {
          turn = startNewTurn(sessionID, conversation.conversationID)
        } else {
          // 确保 turn 的 conversationID 正确
          turn.conversationID = conversation.conversationID
        }
        
        // 记录参数
        turn.input.params = {
          temperature: output.temperature,
          topP: output.topP,
          topK: output.topK,
          options: output.options,
        }

        // 如果 messages 还没有设置，尝试从 pending 队列中获取
        if (!turn.input.messages || turn.input.messages.length === 0) {
          const pendingKeys = Array.from(pendingMessages.keys()).sort().reverse()
          if (pendingKeys.length > 0) {
            // 取最近的 messages（假设是当前 turn 的）
            const recentKey = pendingKeys[0]
            const messages = pendingMessages.get(recentKey)
            if (messages) {
              turn.input.messages = messages
              pendingMessages.delete(recentKey)
            }
          }
        }
      } catch (error) {
        console.error("[log-conversation] Error in chat.params hook:", error)
      }
    },

    // 捕获文本输出
    "experimental.text.complete": async (input, output) => {
      try {
        const { sessionID } = input
        console.log("[log-conversation] experimental.text.complete hook triggered, sessionID:", sessionID)
        
        // 确保有当前对话
        let conversation = getCurrentConversation(sessionID)
        if (!conversation) {
          conversation = startNewConversation(sessionID)
        }
        
        let turn = getCurrentTurn(sessionID)
        if (!turn) {
          // 如果没有 turn，创建一个（可能发生在某些边缘情况）
          turn = startNewTurn(sessionID, conversation.conversationID)
        } else {
          // 确保 turn 的 conversationID 正确
          turn.conversationID = conversation.conversationID
        }
        
        turn.output.textParts.push({
          partID: input.partID,
          text: output.text,
          timestamp: Date.now(),
        })
        console.log("[log-conversation] Recorded text part, length:", output.text.length)
        
        // 延迟完成 turn（作为备用机制）
        // 如果事件系统没有触发完成，这个可以确保 turn 被写入
        setTimeout(() => {
          const currentTurn = getCurrentTurn(sessionID)
          if (currentTurn && !currentTurn.completed && currentTurn.output.textParts.length > 0) {
            console.log("[log-conversation] Auto-completing turn after text.complete (backup mechanism)")
            completeTurn(sessionID)
          }
        }, 5000)
      } catch (error) {
        console.error("[log-conversation] Error in experimental.text.complete hook:", error)
      }
    },

    // 捕获工具调用（输出的一部分）
    "tool.execute.before": async (input, output) => {
      const { sessionID, callID, tool } = input
      
      // 确保有当前对话
      let conversation = getCurrentConversation(sessionID)
      if (!conversation) {
        conversation = startNewConversation(sessionID)
      }
      
      let turn = getCurrentTurn(sessionID)
      if (!turn) {
        turn = startNewTurn(sessionID, conversation.conversationID)
      } else {
        // 确保 turn 的 conversationID 正确
        turn.conversationID = conversation.conversationID
      }
      
      turn.output.toolCalls.push({
        callID,
        tool,
        args: output.args,
        timestamp: Date.now(),
      })
    },

    "tool.execute.after": async (input, output) => {
      const { sessionID, callID } = input
      const turn = getCurrentTurn(sessionID)
      if (turn) {
        const toolCall = turn.output.toolCalls.find((tc) => tc.callID === callID)
        if (toolCall) {
          toolCall.result = {
            title: output.title,
            output: output.output,
            metadata: output.metadata,
          }
        }
      }
    },

    // 监听事件，在适当的时候完成 turn
    event: async ({ event }) => {
      try {
        console.log("[log-conversation] Event received:", event.type, event.properties)
        
        // 监听各种可能的事件类型
        const sessionID = event.properties?.sessionID
        
        if (sessionID) {
          // 监听 session.message.created 事件
          if (event.type === "session.message.created") {
            console.log("[log-conversation] Event: session.message.created, sessionID:", sessionID)
            // 延迟完成 turn，给输出 hooks 时间记录数据
            setTimeout(() => {
              const turn = getCurrentTurn(sessionID)
              if (turn && !turn.completed) {
                console.log("[log-conversation] Completing turn from session.message.created event")
                completeTurn(sessionID)
              }
            }, 5000)
          }
          
          // 监听其他可能的事件类型（备用）
          if (event.type === "session.message.completed" || 
              event.type === "message.completed" ||
              event.type === "assistant.message.completed") {
            console.log("[log-conversation] Event:", event.type, "sessionID:", sessionID)
            setTimeout(() => {
              const turn = getCurrentTurn(sessionID)
              if (turn && !turn.completed) {
                console.log("[log-conversation] Completing turn from", event.type, "event")
                completeTurn(sessionID)
              }
            }, 2000)
          }
        }
      } catch (error) {
        console.error("[log-conversation] Error in event hook:", error)
      }
    },
  }
}

