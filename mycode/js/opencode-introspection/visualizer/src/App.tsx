import React, { useState } from 'react'
import type { Turn } from './types/turn'
import { FileLoader } from './components/FileLoader'
import { TurnList } from './components/TurnList'
import { SystemPrompts } from './components/SystemPrompts'
import { ChatHistory } from './components/ChatHistory'
import { ToolHistory } from './components/ToolHistory'
import { StatusBar } from './components/StatusBar'
import '../styles/design-tokens.css'
import '../styles/global.css'
import './styles/app.css'

function App() {
  const [turns, setTurns] = useState<Turn[]>([])
  const [selectedTurnIndex, setSelectedTurnIndex] = useState<number>(0)
  const [filename, setFilename] = useState<string>('')
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false)

  const selectedTurn = turns.length > 0 && selectedTurnIndex >= 0 && selectedTurnIndex < turns.length
    ? turns[selectedTurnIndex]
    : null

  const handleLoad = (loadedTurns: Turn[], loadedFilename: string) => {
    setTurns(loadedTurns)
    setFilename(loadedFilename)
    setSelectedTurnIndex(0)
  }

  const handlePrevious = () => {
    if (selectedTurnIndex > 0) {
      setSelectedTurnIndex(selectedTurnIndex - 1)
    }
  }

  const handleNext = () => {
    if (selectedTurnIndex < turns.length - 1) {
      setSelectedTurnIndex(selectedTurnIndex + 1)
    }
  }

  const handleSelectTurn = (turn: Turn) => {
    const index = turns.findIndex(t => t.turnID === turn.turnID)
    if (index >= 0) {
      setSelectedTurnIndex(index)
    }
  }

  return (
    <div className="app-container">
      {/* Header */}
      <header className="app-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h1 style={{ margin: 0, fontSize: 'var(--font-h2)' }}>OpenCode Session Visualizer</h1>
        {turns.length > 0 && (
          <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-md)' }}>
            <button
              className="btn btn-ghost"
              onClick={handlePrevious}
              disabled={selectedTurnIndex === 0}
              style={{ opacity: selectedTurnIndex === 0 ? 0.5 : 1 }}
            >
              ← Previous
            </button>
            <button
              className="btn btn-ghost"
              onClick={handleNext}
              disabled={selectedTurnIndex === turns.length - 1}
              style={{ opacity: selectedTurnIndex === turns.length - 1 ? 0.5 : 1 }}
            >
              Next →
            </button>
            <span style={{ fontSize: 'var(--font-small)', color: 'var(--md-slate)' }}>
              Turn {selectedTurnIndex + 1} / {turns.length}
            </span>
            {filename && (
              <button 
                className="btn btn-ghost"
                onClick={() => {
                  setTurns([])
                  setSelectedTurnIndex(0)
                  setFilename('')
                }}
                style={{ marginLeft: 'var(--space-md)' }}
              >
                Close
              </button>
            )}
          </div>
        )}
      </header>

      {/* Main Content */}
      {turns.length === 0 ? (
        <div className="file-loader-container">
          <div className="file-loader-wrapper">
            <FileLoader onLoad={handleLoad} />
          </div>
        </div>
      ) : (
        <div className="app-main-new-layout">
          {/* Left Sidebar - Log List Panel */}
          <div className="turn-list-container-new">
            <TurnList 
              turns={turns} 
              selectedTurn={selectedTurn}
              onSelectTurn={handleSelectTurn}
              collapsed={sidebarCollapsed}
              onToggleCollapse={() => setSidebarCollapsed(!sidebarCollapsed)}
            />
          </div>

          {/* Right Main View - Three Panels */}
          <div className="main-view-container">
            {/* Top Row */}
            <div className="main-view-top-row">
              {/* Top-Middle: System Prompts */}
              <div className="system-prompts-panel">
                <SystemPrompts turn={selectedTurn} />
              </div>

              {/* Top-Right: Chat History */}
              <div className="chat-history-panel">
                <ChatHistory turn={selectedTurn} />
              </div>
            </div>

            {/* Bottom Row: Tool History */}
            <div className="tool-history-panel">
              <ToolHistory turn={selectedTurn} />
            </div>
          </div>
        </div>
      )}

      {/* Footer - Status Bar */}
      {turns.length > 0 && (
        <StatusBar turn={selectedTurn} />
      )}
    </div>
  )
}

export default App
