import { Table, Button, Space } from 'antd'
import { DownloadOutlined } from '@ant-design/icons'
import type { SqlQueryResponse } from '../types'

interface QueryResultsProps {
  result: SqlQueryResponse | null
}

export default function QueryResults({ result }: QueryResultsProps) {
  if (!result || result.rowCount === 0) {
    return (
      <div style={{ padding: '16px', textAlign: 'center', color: '#999' }}>
        暂无查询结果
      </div>
    )
  }

  const columns = result.columns.map((col) => ({
    title: col,
    dataIndex: col,
    key: col,
    ellipsis: true,
    render: (text: any) => {
      if (text === null || text === undefined) {
        return <span style={{ color: '#999' }}>NULL</span>
      }
      if (typeof text === 'object') {
        return JSON.stringify(text)
      }
      return String(text)
    },
  }))

  const dataSource = result.rows.map((row, index) => {
    const record: Record<string, any> = { key: index }
    result.columns.forEach((col, colIndex) => {
      record[col] = row[colIndex]
    })
    return record
  })

  return (
    <div style={{ height: '100%', overflow: 'auto' }}>
      <Table
        columns={columns}
        dataSource={dataSource}
        pagination={{
          pageSize: 50,
          showSizeChanger: true,
          showTotal: (total) => `共 ${total} 条`,
        }}
        scroll={{ x: 'max-content', y: 'calc(100vh - 200px)' }}
        size="small"
      />
    </div>
  )
}

export function QueryResultsHeader({ result, onExportCSV, onExportJSON }: { result: SqlQueryResponse | null, onExportCSV: () => void, onExportJSON: () => void }) {
  return (
    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
      <span>查询结果</span>
      {result && result.rowCount > 0 && (
        <Space>
          <Button
            size="small"
            icon={<DownloadOutlined />}
            onClick={onExportCSV}
          >
            导出 CSV
          </Button>
          <Button
            size="small"
            icon={<DownloadOutlined />}
            onClick={onExportJSON}
          >
            导出 JSON
          </Button>
        </Space>
      )}
    </div>
  )
}

