import { useState } from 'react'
import { Input, Button, Space, message, Card } from 'antd'
import { ThunderboltOutlined } from '@ant-design/icons'
import { apiClient } from '../api/client'

const { TextArea } = Input

interface NaturalLanguageQueryProps {
  databaseName: string | null
  onSqlGenerated: (sql: string) => void
  onQueryResult?: (result: any) => void
}

export default function NaturalLanguageQuery({
  databaseName,
  onSqlGenerated,
}: NaturalLanguageQueryProps) {
  const [prompt, setPrompt] = useState('')
  const [loading, setLoading] = useState(false)
  const [generatedSql, setGeneratedSql] = useState<string | null>(null)

  const handleGenerate = async () => {
    if (!databaseName) {
      message.warning('请先选择一个数据库')
      return
    }

    if (!prompt.trim()) {
      message.warning('请输入查询需求')
      return
    }

    setLoading(true)
    try {
      // Call DeepSeek API to generate SQL
      const result = await apiClient.naturalLanguageQuery(databaseName, {
        prompt,
      })
      
      // Set generated SQL to state for display
      setGeneratedSql(result.sql)
      
      // Pass SQL to parent component to fill into SQL editor
      onSqlGenerated(result.sql)
      
      message.success('SQL 生成成功，已自动填充到编辑器')
    } catch (error: any) {
      // Handle different error formats
      let errorMessage = '生成 SQL 失败'
      
      if (error?.message) {
        errorMessage = error.message
      } else if (error?.code) {
        // Handle error codes
        if (error.code === 'metadata_not_found') {
          errorMessage = '数据库元数据不存在，请先刷新数据库元数据'
        } else if (error.code === 'connection_not_found') {
          errorMessage = '数据库连接不存在'
        } else {
          errorMessage = error.message || `错误代码: ${error.code}`
        }
      } else if (typeof error === 'string') {
        errorMessage = error
      } else if (error?.response?.data?.error) {
        // Handle API error response
        const apiError = error.response.data.error
        if (apiError.code === 'metadata_not_found') {
          errorMessage = '数据库元数据不存在，请先刷新数据库元数据'
        } else if (apiError.code === 'connection_not_found') {
          errorMessage = '数据库连接不存在'
        } else {
          errorMessage = apiError.message || apiError.code || '生成 SQL 失败'
        }
      } else if (error?.response?.status === 404) {
        errorMessage = '数据库连接或元数据不存在，请检查数据库连接并刷新元数据'
      }
      
      message.error(`生成 SQL 失败: ${errorMessage}`)
      setGeneratedSql(null)
    } finally {
      setLoading(false)
    }
  }

  return (
    <Card title="自然语言查询" size="small" style={{ marginBottom: '16px' }}>
      <Space direction="vertical" style={{ width: '100%' }} size="middle">
        <TextArea
          rows={3}
          placeholder="例如：查询所有用户表的信息"
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          disabled={!databaseName}
        />
        <Button
          type="primary"
          icon={<ThunderboltOutlined />}
          onClick={handleGenerate}
          loading={loading}
          disabled={!databaseName}
          block
        >
          生成 SQL
        </Button>
        {generatedSql && (
          <div style={{ marginTop: '8px' }}>
            <div style={{ fontSize: '12px', color: '#666', marginBottom: '4px' }}>生成的 SQL:</div>
            <pre style={{ background: '#f5f5f5', padding: '8px', borderRadius: '4px', fontSize: '12px', overflow: 'auto' }}>
              {generatedSql}
            </pre>
          </div>
        )}
      </Space>
    </Card>
  )
}

