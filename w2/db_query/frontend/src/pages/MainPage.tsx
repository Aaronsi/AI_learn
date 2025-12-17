import { useState } from 'react'
import { Layout, Card, message } from 'antd'
import { useQuery } from '@tanstack/react-query'
import DatabaseTree from '../components/DatabaseTree'
import DatabaseConnectionDialog from '../components/DatabaseConnectionDialog'
import SqlEditor from '../components/SqlEditor'
import QueryResults, { QueryResultsHeader } from '../components/QueryResults'
import NaturalLanguageQuery from '../components/NaturalLanguageQuery'
import { apiClient } from '../api/client'
import type { SqlQueryResponse, DatabaseConnection } from '../types'

const { Header, Content, Sider } = Layout

export default function MainPage() {
  const [selectedDatabase, setSelectedDatabase] = useState<string | null>(null)
  const [selectedTable, setSelectedTable] = useState<string | null>(null)
  const [queryResult, setQueryResult] = useState<SqlQueryResponse | null>(null)
  const [editorSql, setEditorSql] = useState<string>('SELECT version();')
  const [dialogOpen, setDialogOpen] = useState(false)
  const [editingDatabase, setEditingDatabase] = useState<DatabaseConnection | undefined>()

  const {
    data: databasesData,
    refetch,
  } = useQuery({
    queryKey: ['databases'],
    queryFn: () => apiClient.getDatabases(),
  })

  const databases = databasesData?.databases || []

  const handleSelectDatabase = (name: string) => {
    setSelectedDatabase(name)
    setSelectedTable(null)
    setQueryResult(null)
  }

  const handleSelectTable = (databaseName: string, schema: string, tableName: string) => {
    setSelectedDatabase(databaseName)
    setSelectedTable(`${schema}.${tableName}`)
    // Auto-generate SELECT query
    const sql = `SELECT * FROM ${schema}.${tableName} LIMIT 100;`
    setEditorSql(sql)
    setQueryResult(null)
  }

  const handleQueryResult = (result: SqlQueryResponse) => {
    setQueryResult(result)
  }

  const handleSqlGenerated = (sql: string) => {
    // Update SQL editor with generated SQL from natural language query
    setEditorSql(sql)
  }

  const handleAddDatabase = () => {
    setEditingDatabase(undefined)
    setDialogOpen(true)
  }

  const handleDeleteDatabase = async (name: string) => {
    try {
      await apiClient.deleteDatabase(name)
      message.success(`数据库连接 ${name} 已删除`)
      refetch()
      if (selectedDatabase === name) {
        setSelectedDatabase(null)
        setSelectedTable(null)
      }
    } catch (error: any) {
      message.error(error.message || '删除失败')
    }
  }


  return (
    <Layout style={{ height: '100vh' }}>
      <Header style={{ background: '#fff', boxShadow: '0 2px 8px rgba(0,0,0,0.1)', padding: '0 16px' }}>
        <div style={{ fontSize: '20px', fontWeight: 'bold', lineHeight: '64px' }}>DB Query Tool</div>
      </Header>
      <Layout>
        <Sider width={300} style={{ background: '#fff', borderRight: '1px solid #f0f0f0' }}>
          <DatabaseTree
            databases={databases}
            selectedDatabase={selectedDatabase}
            selectedTable={selectedTable}
            onSelectDatabase={handleSelectDatabase}
            onSelectTable={handleSelectTable}
            onRefresh={refetch}
            onAddDatabase={handleAddDatabase}
            onDeleteDatabase={handleDeleteDatabase}
          />
        </Sider>
        <Content style={{ padding: '16px', background: '#f5f5f5' }}>
          <div style={{ height: '100%', display: 'flex', flexDirection: 'column', gap: '16px' }}>
            <NaturalLanguageQuery
              databaseName={selectedDatabase}
              onSqlGenerated={handleSqlGenerated}
              onQueryResult={handleQueryResult}
            />
            <Card
              title="SQL 编辑器"
              size="small"
              style={{ flex: 1, display: 'flex', flexDirection: 'column', minHeight: '300px' }}
              styles={{ body: { display: 'flex', flexDirection: 'column', height: '100%', padding: 0 } }}
            >
              <div style={{ flex: 1 }}>
                <SqlEditor
                  databaseName={selectedDatabase}
                  onQueryResult={handleQueryResult}
                  initialSql={editorSql}
                  onSqlChange={setEditorSql}
                />
              </div>
            </Card>
            <Card
              title={
                <QueryResultsHeader
                  result={queryResult}
                  onExportCSV={() => {
                    if (queryResult) {
                      const csvHeaders = queryResult.columns.join(',')
                      const csvRows = queryResult.rows.map(row => 
                        row.map(cell => {
                          const cellStr = cell === null || cell === undefined ? '' : String(cell)
                          if (cellStr.includes(',') || cellStr.includes('"') || cellStr.includes('\n')) {
                            return `"${cellStr.replace(/"/g, '""')}"`
                          }
                          return cellStr
                        }).join(',')
                      )
                      const csvContent = [csvHeaders, ...csvRows].join('\n')
                      const blob = new Blob(['\ufeff' + csvContent], { type: 'text/csv;charset=utf-8;' })
                      const link = document.createElement('a')
                      const url = URL.createObjectURL(blob)
                      link.setAttribute('href', url)
                      link.setAttribute('download', `query_result_${new Date().getTime()}.csv`)
                      link.style.visibility = 'hidden'
                      document.body.appendChild(link)
                      link.click()
                      document.body.removeChild(link)
                    }
                  }}
                  onExportJSON={() => {
                    if (queryResult) {
                      const jsonData = queryResult.rows.map(row => {
                        const obj: Record<string, any> = {}
                        queryResult.columns.forEach((col, colIndex) => {
                          obj[col] = row[colIndex]
                        })
                        return obj
                      })
                      const jsonContent = JSON.stringify(jsonData, null, 2)
                      const blob = new Blob([jsonContent], { type: 'application/json;charset=utf-8;' })
                      const link = document.createElement('a')
                      const url = URL.createObjectURL(blob)
                      link.setAttribute('href', url)
                      link.setAttribute('download', `query_result_${new Date().getTime()}.json`)
                      link.style.visibility = 'hidden'
                      document.body.appendChild(link)
                      link.click()
                      document.body.removeChild(link)
                    }
                  }}
                />
              }
              size="small"
              style={{ flex: 1, display: 'flex', flexDirection: 'column', minHeight: '200px' }}
              styles={{ body: { display: 'flex', flexDirection: 'column', height: '100%', padding: 0 } }}
            >
              <div style={{ flex: 1 }}>
                <QueryResults result={queryResult} />
              </div>
            </Card>
          </div>
        </Content>
      </Layout>
      <DatabaseConnectionDialog
        open={dialogOpen}
        onClose={() => setDialogOpen(false)}
        onSuccess={() => {
          refetch()
          setDialogOpen(false)
        }}
        initialValues={editingDatabase}
      />
    </Layout>
  )
}

