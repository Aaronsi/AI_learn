import React from 'react'
import type { Turn } from '../types/turn'
import { formatTimestamp } from '../utils/formatter'
import { MessageView } from './MessageView'
import { ToolCallView } from './ToolCallView'
import { MarkdownContent } from './MarkdownContent'

interface TurnDetailProps {
  turn: Turn | null
}

export const TurnDetail: React.FC<TurnDetailProps> = ({ turn }) => {
  if (!turn) {
    return (
      <div style={{ 
        padding: 'var(--space-2xl)', 
        textAlign: 'center', 
        color: 'var(--md-slate)',
        height: '100%',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center'
      }}>
        选择一个 Turn 查看详情
      </div>
    )
  }

  return (
    <div style={{ height: '100%', display: 'flex', flexDirection: 'column', padding: 'var(--space-md)' }}>
      <div style={{ marginBottom: 'var(--space-md)', flexShrink: 0 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 'var(--space-xs)' }}>
          <h2 style={{ margin: 0 }}>Turn 详情</h2>
          <span className="badge badge-info">{turn.turnID.slice(0, 8)}...</span>
        </div>
        <div style={{ color: 'var(--md-slate)', fontSize: 'var(--font-small)' }}>
          {formatTimestamp(turn.timestamp)}
        </div>
      </div>

      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: 'var(--space-md)', overflow: 'hidden' }}>
        <div style={{ flex: 1, display: 'flex', flexDirection: 'column', minHeight: 0, border: 'var(--border-strong)', borderRadius: 'var(--radius-micro)', backgroundColor: 'var(--md-cloud)' }}>
          <div style={{ padding: 'var(--space-md)', borderBottom: 'var(--border-strong)', backgroundColor: 'var(--md-fog)', flexShrink: 0 }}>
            <h3 style={{ margin: 0, fontSize: 'var(--font-h3)' }}>输入</h3>
          </div>
          <div className="scrollable" style={{ flex: 1, padding: 'var(--space-md)' }}>
            {turn.input.messages.map((message, index) => (
              <MessageView key={message.info.id || index} message={message} />
            ))}
            {turn.input.params && (
              <div className="card" style={{ marginTop: 'var(--space-lg)' }}>
                <div className="card-header" style={{ padding: 'var(--space-sm)', fontSize: 'var(--font-small)' }}>
                  参数
                </div>
                <div className="card-body" style={{ padding: 'var(--space-sm)' }}>
                  <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 'var(--font-small)' }}>
                    <tbody>
                      {turn.input.params.temperature !== undefined && (
                        <tr>
                          <td style={{ padding: 'var(--space-xs)', fontWeight: 'var(--font-weight-bold)' }}>Temperature:</td>
                          <td style={{ padding: 'var(--space-xs)' }}>{turn.input.params.temperature}</td>
                        </tr>
                      )}
                      {turn.input.params.topP !== undefined && (
                        <tr>
                          <td style={{ padding: 'var(--space-xs)', fontWeight: 'var(--font-weight-bold)' }}>Top P:</td>
                          <td style={{ padding: 'var(--space-xs)' }}>{turn.input.params.topP}</td>
                        </tr>
                      )}
                      {turn.input.params.topK !== undefined && (
                        <tr>
                          <td style={{ padding: 'var(--space-xs)', fontWeight: 'var(--font-weight-bold)' }}>Top K:</td>
                          <td style={{ padding: 'var(--space-xs)' }}>{turn.input.params.topK}</td>
                        </tr>
                      )}
                      {turn.input.params.options && Object.keys(turn.input.params.options).length > 0 && (
                        <tr>
                          <td style={{ padding: 'var(--space-xs)', fontWeight: 'var(--font-weight-bold)' }}>Options:</td>
                          <td style={{ padding: 'var(--space-xs)' }}>
                            <pre style={{ fontSize: 'var(--font-small)', margin: 0 }}>
                              {JSON.stringify(turn.input.params.options, null, 2)}
                            </pre>
                          </td>
                        </tr>
                      )}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </div>
        </div>

        <div style={{ flex: 1, display: 'flex', flexDirection: 'column', minHeight: 0, border: 'var(--border-strong)', borderRadius: 'var(--radius-micro)', backgroundColor: 'var(--md-cloud)' }}>
          <div style={{ padding: 'var(--space-md)', borderBottom: 'var(--border-strong)', backgroundColor: 'var(--md-fog)', flexShrink: 0 }}>
            <h3 style={{ margin: 0, fontSize: 'var(--font-h3)' }}>输出</h3>
          </div>
          <div className="scrollable" style={{ flex: 1, padding: 'var(--space-md)' }}>
            {turn.output.textParts.length > 0 && (
              <div style={{ marginBottom: 'var(--space-lg)' }}>
                {turn.output.textParts.map((part, index) => (
                  <div key={part.partID || index} className="card" style={{ marginBottom: 'var(--space-md)' }}>
                    <div className="card-header" style={{ padding: 'var(--space-sm)', fontSize: 'var(--font-small)', color: 'var(--md-slate)' }}>
                      文本输出 {index + 1} - {formatTimestamp(part.timestamp)}
                    </div>
                    <div className="card-body" style={{ padding: 'var(--space-sm)' }}>
                      <MarkdownContent content={part.text} />
                    </div>
                  </div>
                ))}
              </div>
            )}

            {turn.output.toolCalls.length > 0 && (
              <div>
                <div style={{ marginBottom: 'var(--space-sm)', fontWeight: 'var(--font-weight-bold)' }}>
                  工具调用 ({turn.output.toolCalls.length})
                </div>
                {turn.output.toolCalls.map((toolCall, index) => (
                  <ToolCallView key={toolCall.callID || index} toolCall={toolCall} />
                ))}
              </div>
            )}

            {turn.output.textParts.length === 0 && turn.output.toolCalls.length === 0 && (
              <div style={{ color: 'var(--md-slate)', fontStyle: 'italic', textAlign: 'center', padding: 'var(--space-xl)' }}>
                无输出内容
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
