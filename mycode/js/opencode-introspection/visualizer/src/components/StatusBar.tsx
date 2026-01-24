import React, { useMemo } from 'react'
import type { Turn } from '../types/turn'

interface StatusBarProps {
  turn: Turn | null
}

// 简单的 token 估算（粗略计算）
function estimateTokens(text: string): number {
  // 粗略估算：中文约 1.5 字符 = 1 token，英文约 4 字符 = 1 token
  // 这里使用更简单的估算：平均 3 字符 = 1 token
  return Math.ceil(text.length / 3)
}

export const StatusBar: React.FC<StatusBarProps> = ({ turn }) => {
  const stats = useMemo(() => {
    if (!turn) {
      return {
        systemPromptTokens: 0,
        chatHistoryTokens: 0,
        toolHistoryCount: 0,
        totalInputTokens: 0,
        totalOutputTokens: 0,
      }
    }

    // 计算 system prompt tokens
    // 优先使用 systemPrompts 字段
    let systemPromptText = ''
    if (turn.input.systemPrompts && turn.input.systemPrompts.length > 0) {
      systemPromptText = turn.input.systemPrompts.join('\n\n')
    } else {
      // 如果没有 systemPrompts，从 messages 中提取
      turn.input.messages
        .filter(msg => msg.info.role === 'system')
        .forEach(msg => {
          msg.parts.forEach(part => {
            if (part.text) systemPromptText += part.text
          })
        })
    }
    const systemPromptTokens = estimateTokens(systemPromptText)

    // 计算 chat history tokens（不含 tool）
    let chatHistoryText = ''
    turn.input.messages
      .filter(msg => {
        if (msg.info.role === 'system') return false
        const hasToolParts = msg.parts.some(part => 
          part.type === 'tool' || part.type === 'tool-call' || part.type === 'tool-result'
        )
        return !hasToolParts
      })
      .forEach(msg => {
        msg.parts.forEach(part => {
          if (part.text) chatHistoryText += part.text
        })
      })
    const chatHistoryTokens = estimateTokens(chatHistoryText)

    // 工具调用数量
    const toolHistoryCount = turn.output.toolCalls.length

    // 总输入 tokens（如果有 tokens 信息）
    const totalInputTokens = turn.input.messages.reduce((sum, msg) => {
      // 尝试从 message info 中获取 tokens
      const tokens = (msg.info as any).tokens?.input || 0
      return sum + tokens
    }, 0) || estimateTokens(JSON.stringify(turn.input))

    // 总输出 tokens
    const totalOutputTokens = turn.output.textParts.reduce((sum, part) => {
      return sum + estimateTokens(part.text)
    }, 0)

    return {
      systemPromptTokens,
      chatHistoryTokens,
      toolHistoryCount,
      totalInputTokens,
      totalOutputTokens,
    }
  }, [turn])

  const formatTokens = (tokens: number) => {
    if (tokens >= 1000) {
      return `${(tokens / 1000).toFixed(1)}k`
    }
    return tokens.toString()
  }

  return (
    <div style={{
      padding: 'var(--space-sm) var(--space-md)',
      borderTop: 'var(--border-strong)',
      backgroundColor: 'var(--md-fog)',
      fontSize: 'var(--font-small)',
      color: 'var(--md-slate)',
      display: 'flex',
      gap: 'var(--space-lg)',
      flexWrap: 'wrap',
    }}>
      <span>
        <strong>Sysprompt:</strong> {formatTokens(stats.systemPromptTokens)} tokens
      </span>
      <span>
        <strong>Chat history:</strong> {formatTokens(stats.chatHistoryTokens)} tokens
      </span>
      <span>
        <strong>Tool calls:</strong> {stats.toolHistoryCount}
      </span>
      <span>
        <strong>Total input:</strong> {formatTokens(stats.totalInputTokens)} tokens
      </span>
      <span>
        <strong>Total output:</strong> {formatTokens(stats.totalOutputTokens)} tokens
      </span>
      <span style={{ marginLeft: 'auto', fontStyle: 'italic' }}>
        Status bar show stats info
      </span>
    </div>
  )
}

