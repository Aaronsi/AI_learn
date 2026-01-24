import React, { useState } from 'react'
import type { Message } from '../types/turn'
import { formatTimestamp } from '../utils/formatter'
import { MarkdownContent } from './MarkdownContent'

interface MessageViewProps {
  message: Message
}

export const MessageView: React.FC<MessageViewProps> = ({ message }) => {
  const [isExpanded, setIsExpanded] = useState(true)
  const { info, parts } = message

  const roleLabel = info.role === 'user' ? 'User' : info.role === 'assistant' ? 'Assistant' : 'System'
  const roleBadgeClass = info.role === 'user' ? 'badge-user' : info.role === 'assistant' ? 'badge-assistant' : 'badge-system'

  return (
    <div className="card" style={{ marginBottom: 'var(--space-md)', overflow: 'hidden' }}>
      <div
        className="card-header collapsible-trigger"
        onClick={() => setIsExpanded(!isExpanded)}
        style={{ 
          cursor: 'pointer', 
          userSelect: 'none',
          display: 'flex',
          alignItems: 'center',
          gap: 'var(--space-sm)'
        }}
      >
        <span className={`badge ${roleBadgeClass}`}>
          {roleLabel}
        </span>
        {info.agent && (
          <span className="badge badge-info" style={{ fontSize: 'var(--font-tiny)' }}>
            {info.agent}
          </span>
        )}
        {info.model && (
          <span className="badge badge-info" style={{ fontSize: 'var(--font-tiny)' }}>
            {info.model.providerID}/{info.model.modelID}
          </span>
        )}
        <span style={{ marginLeft: 'auto', color: 'var(--md-slate)', fontSize: 'var(--font-tiny)' }}>
          {formatTimestamp(info.time.created)}
        </span>
        <span style={{ color: 'var(--md-slate)', fontSize: 'var(--font-tiny)', marginLeft: 'var(--space-xs)' }}>
          {isExpanded ? '▼' : '▶'}
        </span>
      </div>
      {isExpanded && (
        <div className="card-body" style={{ padding: 'var(--space-md)' }}>
          {parts.map((part, index) => (
            <div key={part.id || index} style={{ marginBottom: part.text ? 'var(--space-md)' : 'var(--space-xs)' }}>
              {part.type === 'text' && part.text ? (
                <MarkdownContent content={part.text} />
              ) : part.type !== 'text' ? (
                <pre style={{ 
                  fontSize: 'var(--font-small)', 
                  overflow: 'auto',
                  maxHeight: '300px',
                  padding: 'var(--space-sm)',
                  backgroundColor: 'var(--md-fog)',
                  border: '1px solid var(--md-grid-line)',
                  borderRadius: 'var(--radius-micro)'
                }}>
                  {JSON.stringify(part, null, 2)}
                </pre>
              ) : null}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
