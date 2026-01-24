import React from 'react'
import type { Turn } from '../types/turn'
import { MessageView } from './MessageView'

interface ChatHistoryProps {
  turn: Turn | null
}

export const ChatHistory: React.FC<ChatHistoryProps> = ({ turn }) => {
  if (!turn) {
    return (
      <div className="card" style={{ height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <div style={{ textAlign: 'center', color: 'var(--md-slate)' }}>
          Chat History (excluding tool calls)
        </div>
      </div>
    )
  }

  // 过滤出非 system、非 tool 的消息（只显示 user 和 assistant 的文本消息）
  const chatMessages = turn.input.messages.filter(msg => {
    if (msg.info.role === 'system') return false
    // 检查是否有 tool 相关的 parts
    const hasToolParts = msg.parts.some(part => 
      part.type === 'tool' || 
      part.type === 'tool-call' ||
      part.type === 'tool-result'
    )
    return !hasToolParts
  })

  return (
    <div className="card scrollable" style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      <div className="card-header">
        <h3 style={{ margin: 0 }}>Chat History (excluding tool calls)</h3>
      </div>
      <div className="card-body" style={{ flex: 1, overflow: 'auto' }}>
        {chatMessages.length > 0 ? (
          chatMessages.map((message, index) => (
            <MessageView key={message.info.id || index} message={message} />
          ))
        ) : (
          <div style={{ color: 'var(--md-slate)', fontStyle: 'italic', textAlign: 'center', padding: 'var(--space-xl)' }}>
            No chat history
          </div>
        )}
      </div>
    </div>
  )
}

