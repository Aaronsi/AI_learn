import React from 'react'
import type { Turn } from '../types/turn'
import { formatRelativeTime, getInputPreview, getOutputPreview } from '../utils/formatter'

interface TurnListProps {
  turns: Turn[]
  selectedTurn: Turn | null
  onSelectTurn: (turn: Turn) => void
  collapsed?: boolean
  onToggleCollapse?: () => void
}

export const TurnList: React.FC<TurnListProps> = ({ 
  turns, 
  selectedTurn, 
  onSelectTurn,
  collapsed = false,
  onToggleCollapse
}) => {
  if (turns.length === 0) {
    return (
      <div style={{ padding: 'var(--space-lg)', textAlign: 'center', color: 'var(--md-slate)' }}>
        No turn data
      </div>
    )
  }

  return (
    <div style={{ 
      height: '100%', 
      display: 'flex', 
      flexDirection: 'column',
      width: collapsed ? '60px' : '100%',
      transition: 'width var(--transition-default)',
      overflow: 'hidden'
    }}>
      <div 
        style={{ 
          padding: 'var(--space-md)', 
          borderBottom: 'var(--border-strong)', 
          backgroundColor: 'var(--md-fog)', 
          flexShrink: 0,
          cursor: 'pointer',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center'
        }}
        onClick={onToggleCollapse}
      >
        {!collapsed && (
          <>
            <div>
              <h3 style={{ margin: 0, fontSize: 'var(--font-h3)' }}>Turn List</h3>
              <div style={{ fontSize: 'var(--font-tiny)', color: 'var(--md-slate)', marginTop: 'var(--space-xs)' }}>
                {turns.length} turns total
              </div>
            </div>
          </>
        )}
        <span style={{ fontSize: 'var(--font-small)', color: 'var(--md-slate)' }}>
          {collapsed ? '▶' : '◀'}
        </span>
      </div>
      {!collapsed && (
        <div style={{ fontSize: 'var(--font-tiny)', color: 'var(--md-slate)', padding: 'var(--space-xs) var(--space-md)', backgroundColor: 'var(--md-fog)' }}>
          Click header to collapse
        </div>
      )}
      {!collapsed && (
        <div className="scrollable" style={{ flex: 1, padding: 'var(--space-md)' }}>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-sm)' }}>
          {turns.map((turn, index) => {
            const isSelected = selectedTurn?.turnID === turn.turnID
            return (
              <div
                key={turn.turnID}
                className="card"
                onClick={() => onSelectTurn(turn)}
                style={{
                  cursor: 'pointer',
                  backgroundColor: isSelected ? 'var(--md-soft-blue)' : 'var(--md-cloud)',
                  border: isSelected ? 'var(--border-bold)' : 'var(--border-strong)',
                  transition: 'all var(--transition-quick)',
                  overflow: 'hidden'
                }}
                onMouseEnter={(e) => {
                  if (!isSelected) {
                    e.currentTarget.style.transform = 'translate(2px, -2px)'
                    e.currentTarget.style.boxShadow = 'var(--shadow-translate)'
                  }
                }}
                onMouseLeave={(e) => {
                  if (!isSelected) {
                    e.currentTarget.style.transform = 'translate(0, 0)'
                    e.currentTarget.style.boxShadow = 'none'
                  }
                }}
              >
                <div className="card-header" style={{ padding: 'var(--space-sm)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span className="badge badge-info" style={{ fontSize: 'var(--font-tiny)' }}>Turn {index + 1}</span>
                  <span style={{ fontSize: 'var(--font-tiny)', color: 'var(--md-slate)' }}>
                    {formatRelativeTime(turn.timestamp)}
                  </span>
                </div>
                 <div className="card-body" style={{ padding: 'var(--space-sm)' }}>
                  <div style={{ marginBottom: 'var(--space-xs)' }}>
                    <div style={{ fontSize: 'var(--font-tiny)', color: 'var(--md-slate)', marginBottom: '2px', fontWeight: 'var(--font-weight-bold)' }}>
                      Input
                    </div>
                    <div style={{ fontSize: 'var(--font-small)', color: 'var(--md-ink)' }}>
                      {getInputPreview(turn)}
                    </div>
                  </div>
                  <div>
                    <div style={{ fontSize: 'var(--font-tiny)', color: 'var(--md-slate)', marginBottom: '2px', fontWeight: 'var(--font-weight-bold)' }}>
                      Output
                    </div>
                    <div style={{ fontSize: 'var(--font-small)', color: 'var(--md-ink)' }}>
                      {getOutputPreview(turn)}
                    </div>
                  </div>
                </div>
              </div>
            )
          })}
        </div>
      </div>
      )}
    </div>
  )
}
