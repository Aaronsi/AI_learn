import React, { useRef, useState } from 'react'
import type { Turn } from '../types/turn'
import { parseJSONL, readFile } from '../utils/parser'

interface FileLoaderProps {
  onLoad: (turns: Turn[], filename: string) => void
}

export const FileLoader: React.FC<FileLoaderProps> = ({ onLoad }) => {
  const [isDragging, setIsDragging] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const handleFile = async (file: File) => {
    if (!file.name.endsWith('.jsonl')) {
      alert('请选择 JSONL 文件')
      return
    }

    setIsLoading(true)
    try {
      const content = await readFile(file)
      const turns = parseJSONL(content)
      onLoad(turns, file.name)
    } catch (error) {
      console.error('Failed to load file:', error)
      alert('文件加载失败: ' + (error instanceof Error ? error.message : String(error)))
    } finally {
      setIsLoading(false)
    }
  }

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) {
      handleFile(file)
    }
  }

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(true)
  }

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
    const file = e.dataTransfer.files?.[0]
    if (file) {
      handleFile(file)
    }
  }

  return (
    <div className="file-loader">
      <div
        className={`drop-zone ${isDragging ? 'drag-over' : ''}`}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
      >
        {isLoading ? (
          <div>Loading...</div>
        ) : (
          <>
            <div style={{ fontSize: 'var(--font-h3)', marginBottom: 'var(--space-md)' }}>
              Drop a JSONL file here
            </div>
            <div style={{ color: 'var(--md-slate)', marginBottom: 'var(--space-md)' }}>
              Or click to browse files
            </div>
            <button className="btn btn-primary">Select File</button>
          </>
        )}
      </div>
      <input
        ref={fileInputRef}
        type="file"
        accept=".jsonl"
        onChange={handleFileSelect}
        style={{ display: 'none' }}
      />
    </div>
  )
}

