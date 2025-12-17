import React, { useState } from 'react'
import Editor from '@monaco-editor/react'
import { Button, Space, message } from 'antd'
import { PlayCircleOutlined } from '@ant-design/icons'
import { apiClient } from '../api/client'
import type { SqlQueryResponse } from '../types'

interface SqlEditorProps {
  databaseName: string | null
  onQueryResult: (result: SqlQueryResponse) => void
  initialSql?: string
  onSqlChange?: (sql: string) => void
}

export default function SqlEditor({
  databaseName,
  onQueryResult,
  initialSql,
  onSqlChange,
}: SqlEditorProps) {
  const [sql, setSql] = useState(initialSql || 'SELECT version();')
  const [loading, setLoading] = useState(false)

  // Update SQL when initialSql changes
  React.useEffect(() => {
    if (initialSql !== undefined) {
      setSql(initialSql)
    }
  }, [initialSql])

  const handleExecute = async () => {
    if (!databaseName) {
      message.warning('请先选择一个数据库')
      return
    }

    if (!sql.trim()) {
      message.warning('请输入 SQL 查询')
      return
    }

    setLoading(true)
    try {
      const result = await apiClient.queryDatabase(databaseName, { sql })
      onQueryResult(result)
      message.success(`查询成功，返回 ${result.rowCount} 行`)
    } catch (error: any) {
      message.error(error.message || '查询失败')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      <div style={{ padding: '8px', borderBottom: '1px solid #f0f0f0' }}>
        <Space>
          <Button
            type="primary"
            icon={<PlayCircleOutlined />}
            onClick={handleExecute}
            loading={loading}
            disabled={!databaseName}
          >
            执行查询
          </Button>
          <span style={{ fontSize: '12px', color: '#666' }}>
            {databaseName ? `数据库: ${databaseName}` : '请先选择数据库'}
          </span>
        </Space>
      </div>
      <div style={{ flex: 1 }}>
        <Editor
          height="100%"
          defaultLanguage="sql"
          value={sql}
          onChange={(value) => {
            const newSql = value || ''
            setSql(newSql)
            onSqlChange?.(newSql)
          }}
          theme="vs-dark"
          options={{
            minimap: { enabled: false },
            fontSize: 14,
            wordWrap: 'on',
            automaticLayout: true,
          }}
        />
      </div>
    </div>
  )
}

