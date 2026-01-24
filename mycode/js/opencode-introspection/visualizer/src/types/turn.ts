export interface MessageInfo {
  id: string
  sessionID: string
  role: "user" | "assistant" | "system"
  time: {
    created: number
  }
  agent?: string
  model?: {
    providerID: string
    modelID: string
  }
}

export interface MessagePart {
  id: string
  sessionID: string
  messageID: string
  type: string
  text?: string
  [key: string]: any
}

export interface Message {
  info: MessageInfo
  parts: MessagePart[]
}

export interface InputParams {
  temperature?: number
  topP?: number
  topK?: number
  options?: Record<string, any>
}

export interface TurnInput {
  messages: Message[]
  systemPrompts?: string[]  // 系统提示数组
  params?: InputParams
}

export interface TextPart {
  partID: string
  text: string
  timestamp: number
}

export interface ToolCallResult {
  title: string
  output: string
  metadata: any
}

export interface ToolCall {
  callID: string
  tool: string
  args: any
  result?: ToolCallResult
  timestamp: number
}

export interface TurnOutput {
  textParts: TextPart[]
  toolCalls: ToolCall[]
}

export interface Turn {
  turnID: string
  timestamp: number
  input: TurnInput
  output: TurnOutput
}

