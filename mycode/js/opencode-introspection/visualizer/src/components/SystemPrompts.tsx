import React from 'react'
import type { Turn } from '../types/turn'
import { MarkdownContent } from './MarkdownContent'

interface SystemPromptsProps {
  turn: Turn | null
}

export const SystemPrompts: React.FC<SystemPromptsProps> = ({ turn }) => {
  if (!turn) {
    return (
      <div className="card" style={{ height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <div style={{ textAlign: 'center', color: 'var(--md-slate)' }}>
          <div style={{ fontSize: '48px', marginBottom: 'var(--space-md)' }}>▶</div>
          <div>System Prompts</div>
        </div>
      </div>
    )
  }

  // 优先使用 systemPrompts 字段（从 experimental.chat.system.transform hook 捕获）
  const systemPrompts = turn.input.systemPrompts || []
  
  // 如果没有 systemPrompts，尝试从 messages 中提取 system 角色的消息
  const systemMessages = turn.input.messages.filter(msg => msg.info.role === 'system')

  return (
    <div className="card scrollable" style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      <div className="card-header">
        <h3 style={{ margin: 0 }}>System Prompts</h3>
      </div>
      <div className="card-body" style={{ flex: 1, overflow: 'auto' }}>
        {systemPrompts.length > 0 ? (
          systemPrompts.map((prompt, index) => (
            <div key={index} style={{ marginBottom: 'var(--space-lg)' }}>
              <div style={{ 
                fontSize: 'var(--font-tiny)', 
                color: 'var(--md-slate)', 
                marginBottom: 'var(--space-xs)',
                fontWeight: 'var(--font-weight-bold)'
              }}>
                System Prompt {index + 1}
              </div>
              <MarkdownContent content={prompt} />
            </div>
          ))
        ) : systemMessages.length > 0 ? (
          systemMessages.map((message, index) => (
            <div key={message.info.id || index} style={{ marginBottom: 'var(--space-lg)' }}>
              {message.parts.map((part, partIndex) => (
                <div key={part.id || partIndex}>
                  {part.type === 'text' && part.text && (
                    <MarkdownContent content={part.text} />
                  )}
                </div>
              ))}
            </div>
          ))
        ) : (
          <div style={{ color: 'var(--md-slate)', fontStyle: 'italic', textAlign: 'center', padding: 'var(--space-xl)' }}>
            No system prompts found
            <div style={{ fontSize: 'var(--font-small)', marginTop: 'var(--space-sm)' }}>
              (System prompts may not be included in current turn data)
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

