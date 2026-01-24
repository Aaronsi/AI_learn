import React from 'react'
import type { Turn } from '../types/turn'
import { ToolCallView } from './ToolCallView'

interface ToolHistoryProps {
  turn: Turn | null
}

export const ToolHistory: React.FC<ToolHistoryProps> = ({ turn }) => {
  if (!turn) {
    return (
      <div className="card" style={{ height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <div style={{ textAlign: 'center', color: 'var(--md-slate)' }}>
          Tool History
        </div>
      </div>
    )
  }

  // 从 output 中获取 tool calls
  const toolCalls = turn.output.toolCalls || []

  // 也从 input messages 中提取 tool 相关的 parts
  const toolPartsFromMessages: Array<{ message: any; part: any }> = []
  turn.input.messages.forEach(message => {
    message.parts.forEach((part: any) => {
      if (part.type === 'tool' || part.type === 'tool-call' || part.type === 'tool-result') {
        toolPartsFromMessages.push({ message, part })
      }
    })
  })

  return (
    <div className="card scrollable" style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      <div className="card-header">
        <h3 style={{ margin: 0 }}>Tool History</h3>
      </div>
      <div className="card-body" style={{ flex: 1, overflow: 'auto' }}>
        {toolCalls.length > 0 ? (
          toolCalls.map((toolCall, index) => (
            <ToolCallView key={toolCall.callID || index} toolCall={toolCall} />
          ))
        ) : toolPartsFromMessages.length > 0 ? (
          toolPartsFromMessages.map(({ message, part }, index) => (
            <div key={part.id || index} className="card" style={{ marginBottom: 'var(--space-md)' }}>
              <div className="card-header">
                <span className="badge badge-warning">Tool Call</span>
                <span style={{ marginLeft: 'var(--space-sm)' }}>Type: {part.type}</span>
              </div>
              <div className="card-body">
                <pre style={{ fontSize: 'var(--font-small)', overflow: 'auto', maxHeight: '300px' }}>
                  {JSON.stringify(part, null, 2)}
                </pre>
              </div>
            </div>
          ))
        ) : (
          <div style={{ color: 'var(--md-slate)', fontStyle: 'italic', textAlign: 'center', padding: 'var(--space-xl)' }}>
            No tool calls
          </div>
        )}
      </div>
    </div>
  )
}

