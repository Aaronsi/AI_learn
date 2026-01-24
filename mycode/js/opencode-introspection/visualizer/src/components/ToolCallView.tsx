import React, { useState } from 'react'
import type { ToolCall } from '../types/turn'
import { formatTimestamp } from '../utils/formatter'

interface ToolCallViewProps {
  toolCall: ToolCall
}

export const ToolCallView: React.FC<ToolCallViewProps> = ({ toolCall }) => {
  const [isExpanded, setIsExpanded] = useState(false)

  return (
    <div className="card" style={{ marginBottom: 'var(--space-md)' }}>
      <div
        className="card-header collapsible-trigger"
        onClick={() => setIsExpanded(!isExpanded)}
        style={{ cursor: 'pointer', userSelect: 'none' }}
      >
        <span className="badge badge-warning">Tool Call</span>
        <span style={{ marginLeft: 'var(--space-sm)', fontWeight: 'var(--font-weight-bold)' }}>
          {toolCall.tool}
        </span>
        <span style={{ marginLeft: 'auto', color: 'var(--md-slate)', fontSize: 'var(--font-small)' }}>
          {formatTimestamp(toolCall.timestamp)}
        </span>
        <span style={{ marginLeft: 'var(--space-sm)' }}>
          {isExpanded ? '▼' : '▶'}
        </span>
      </div>
      {isExpanded && (
        <div className="card-body">
          <div style={{ marginBottom: 'var(--space-md)' }}>
            <h4 style={{ marginBottom: 'var(--space-xs)' }}>Arguments:</h4>
            <pre style={{ fontSize: 'var(--font-small)', overflow: 'auto', maxHeight: '300px' }}>
              {JSON.stringify(toolCall.args, null, 2)}
            </pre>
          </div>
          {toolCall.result && (
            <div>
              <h4 style={{ marginBottom: 'var(--space-xs)' }}>Result:</h4>
              <div style={{ marginBottom: 'var(--space-xs)' }}>
                <strong>Title:</strong> {toolCall.result.title}
              </div>
              <div style={{ marginBottom: 'var(--space-xs)' }}>
                <strong>Output:</strong>
              </div>
              <pre style={{ fontSize: 'var(--font-small)', overflow: 'auto', maxHeight: '300px' }}>
                {toolCall.result.output}
              </pre>
              {toolCall.result.metadata && (
                <div style={{ marginTop: 'var(--space-sm)' }}>
                  <strong>Metadata:</strong>
                  <pre style={{ fontSize: 'var(--font-small)', overflow: 'auto', maxHeight: '200px' }}>
                    {JSON.stringify(toolCall.result.metadata, null, 2)}
                  </pre>
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  )
}

