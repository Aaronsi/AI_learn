import { useState, useEffect } from 'react'
import { Tree, Button, message, Tooltip, Popconfirm } from 'antd'
import {
  DatabaseOutlined,
  TableOutlined,
  ReloadOutlined,
  PlusOutlined,
  DeleteOutlined,
} from '@ant-design/icons'
import type { DataNode } from 'antd/es/tree'
import { apiClient } from '../api/client'
import type { DatabaseConnection } from '../types'

interface DatabaseTreeProps {
  databases: DatabaseConnection[]
  selectedDatabase: string | null
  selectedTable: string | null
  onSelectDatabase: (name: string) => void
  onSelectTable: (databaseName: string, schema: string, tableName: string) => void
  onRefresh: () => void
  onAddDatabase: () => void
  onDeleteDatabase: (name: string) => void
}

interface TreeNode extends DataNode {
  key: string
  title: string
  icon?: React.ReactNode
  children?: TreeNode[]
  isLeaf?: boolean
  databaseName?: string
  schema?: string
  tableName?: string
  rowCount?: number
  columns?: Array<{
    name: string
    type: string
    nullable: boolean
    default: string | null
  }>
}

export default function DatabaseTree({
  databases,
  selectedDatabase,
  selectedTable,
  onSelectDatabase,
  onSelectTable,
  onRefresh,
  onAddDatabase,
  onDeleteDatabase,
}: DatabaseTreeProps) {
  const [treeData, setTreeData] = useState<TreeNode[]>([])
  const [expandedKeys, setExpandedKeys] = useState<React.Key[]>([])
  const [expandedTableKeys, setExpandedTableKeys] = useState<Set<string>>(new Set())

  // Build initial tree from databases
  useEffect(() => {
    const nodes: TreeNode[] = databases.map((db) => ({
      key: `db-${db.name}`,
      title: db.name, // Database name will be displayed inline with icon
      icon: <DatabaseOutlined />, // Icon will be shown before the title
      databaseName: db.name,
      children: [
        {
          key: `db-${db.name}-loading`,
          title: '加载中...',
          isLeaf: true,
          disabled: true,
        },
      ],
    }))
    setTreeData(nodes)

    // Auto-expand selected database
    if (selectedDatabase) {
      setExpandedKeys([`db-${selectedDatabase}`])
      loadDatabaseMetadata(selectedDatabase)
    }
  }, [databases, selectedDatabase])

  const loadDatabaseMetadata = async (databaseName: string) => {
    try {
      // Use on-demand loading API to get tables
      const tablesData = await apiClient.getDatabaseTables(databaseName)
      updateTreeWithTables(databaseName, tablesData)
    } catch (error: any) {
      message.error(`加载表列表失败: ${error.message}`)
    }
  }

  const loadTableColumns = async (
    databaseName: string,
    schema: string,
    tableName: string
  ) => {
    try {
      const columnsData = await apiClient.getTableColumns(
        databaseName,
        schema,
        tableName
      )
      updateTreeWithTableColumns(databaseName, schema, tableName, columnsData.columns)
    } catch (error: any) {
      message.error(`加载列信息失败: ${error.message}`)
    }
  }

  const updateTreeWithTables = (
    databaseName: string,
    tablesData: {
      schemas: Array<{
        name: string
        tables: Array<{
          name: string
          type: string
          schema: string
        }>
      }>
    }
  ) => {
    setTreeData((prev) => {
      return prev.map((node) => {
        if (node.key === `db-${databaseName}`) {
          const schemaNodes: TreeNode[] = tablesData.schemas.map((schemaData) => ({
            key: `db-${databaseName}-schema-${schemaData.name}`,
            title: schemaData.name,
            databaseName,
            schema: schemaData.name,
            children: schemaData.tables.map((table) => ({
              key: `db-${databaseName}-schema-${schemaData.name}-table-${table.name}`,
              title: table.name,
              icon: <TableOutlined />,
              isLeaf: false, // Allow expansion to show columns
              databaseName,
              schema: schemaData.name,
              tableName: table.name,
              columns: [], // Will be loaded on demand
            })),
          }))

          return {
            ...node,
            children: schemaNodes.length > 0 ? schemaNodes : [],
          }
        }
        return node
      })
    })
  }


  const onLoadData = async (node: TreeNode) => {
    if (node.databaseName && !node.tableName) {
      // Loading database tables
      await loadDatabaseMetadata(node.databaseName)
    } else if (node.databaseName && node.schema && node.tableName) {
      // Loading table columns
      const tableKey = node.key
      if (!expandedTableKeys.has(tableKey)) {
        await loadTableColumns(node.databaseName, node.schema, node.tableName)
        setExpandedTableKeys((prev) => new Set(prev).add(tableKey))
      }
    }
  }

  const updateTreeWithTableColumns = (
    databaseName: string,
    schema: string,
    tableName: string,
    columns: Array<{
      name: string
      type: string
      nullable: boolean
      default: string | null
      position: number
    }>
  ) => {
    setTreeData((prev) => {
      return prev.map((dbNode) => {
        if (dbNode.key === `db-${databaseName}` && dbNode.children) {
          return {
            ...dbNode,
            children: dbNode.children.map((schemaNode) => {
              if (schemaNode.key === `db-${databaseName}-schema-${schema}` && schemaNode.children) {
                return {
                  ...schemaNode,
                  children: schemaNode.children.map((tableNode) => {
                    if (tableNode.key === `db-${databaseName}-schema-${schema}-table-${tableName}`) {
                      return {
                        ...tableNode,
                        columns: columns,
                        children: columns.map((col) => ({
                          key: `${tableNode.key}-col-${col.name}`,
                          title: `${col.name} (${col.type}${col.nullable ? ', nullable' : ''}${col.default ? `, default: ${col.default}` : ''})`,
                          isLeaf: true,
                          icon: null,
                        })),
                      }
                    }
                    return tableNode
                  }),
                }
              }
              return schemaNode
            }),
          }
        }
        return dbNode
      })
    })
  }

  const handleExpand = async (expandedKeys: React.Key[], info: any) => {
    setExpandedKeys(expandedKeys)
    const node = info.node as TreeNode
    
    // If expanding a table, load its columns if not already loaded
    if (node.databaseName && node.schema && node.tableName && info.expanded) {
      const tableKey = node.key
      if (!expandedTableKeys.has(tableKey)) {
        // Columns not loaded yet, load them
        await loadTableColumns(node.databaseName, node.schema, node.tableName)
        setExpandedTableKeys((prev) => new Set(prev).add(tableKey))
      }
    } else if (!info.expanded && node.tableName) {
      // Collapsing a table
      setExpandedTableKeys((prev) => {
        const next = new Set(prev)
        next.delete(node.key)
        return next
      })
    }
  }

  const onSelect = (_selectedKeys: React.Key[], info: any) => {
    const node = info.node as TreeNode

    if (node.databaseName && !node.tableName) {
      // Selected a database
      onSelectDatabase(node.databaseName)
    } else if (node.databaseName && node.schema && node.tableName) {
      // Selected a table
      onSelectTable(node.databaseName, node.schema, node.tableName)
    }
  }

  const renderTitle = (node: TreeNode) => {
    // For database nodes, ensure name is on the same line as icon
    if (node.databaseName && !node.schema && !node.tableName) {
      // Render icon and name together on the same line
      const titleContent = (
        <span style={{ display: 'inline-flex', alignItems: 'center', gap: '6px' }}>
          <DatabaseOutlined style={{ fontSize: '14px' }} />
          <span>{node.title}</span>
          {node.rowCount !== undefined && (
            <span style={{ color: '#999', marginLeft: '4px', fontSize: '12px' }}>
              ({node.rowCount.toLocaleString()})
            </span>
          )}
        </span>
      )

      return (
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', width: '100%' }}>
          <span style={{ flex: 1 }}>{titleContent}</span>
          <Popconfirm
            title="确定要删除这个数据库连接吗？"
            onConfirm={(e) => {
              e?.stopPropagation()
              onDeleteDatabase(node.databaseName!)
            }}
            onCancel={(e) => e?.stopPropagation()}
            okText="确定"
            cancelText="取消"
          >
            <Button
              type="text"
              size="small"
              icon={<DeleteOutlined />}
              danger
              onClick={(e) => {
                e.stopPropagation()
              }}
              style={{ opacity: 0.6, marginLeft: '8px' }}
            />
          </Popconfirm>
        </div>
      )
    }

    // For table nodes, add table icon
    if (node.databaseName && node.schema && node.tableName) {
      const titleContent = (
        <span style={{ display: 'inline-flex', alignItems: 'center', gap: '6px' }}>
          <TableOutlined style={{ fontSize: '14px' }} />
          <span>{node.title}</span>
          {node.rowCount !== undefined && (
            <span style={{ color: '#999', marginLeft: '4px', fontSize: '12px' }}>
              ({node.rowCount.toLocaleString()})
            </span>
          )}
        </span>
      )
      return titleContent
    }

    // For other nodes (schemas, columns, etc.)
    const titleContent = (
      <span>
        {node.title}
        {node.rowCount !== undefined && (
          <span style={{ color: '#999', marginLeft: '8px', fontSize: '12px' }}>
            ({node.rowCount.toLocaleString()})
          </span>
        )}
      </span>
    )

    return titleContent
  }

  return (
    <div style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      <div
        style={{
          padding: '8px',
          borderBottom: '1px solid #f0f0f0',
          display: 'flex',
          gap: '8px',
        }}
      >
        <Tooltip title="添加数据库连接">
          <Button
            type="text"
            icon={<PlusOutlined />}
            size="small"
            onClick={onAddDatabase}
          />
        </Tooltip>
        <Tooltip title="刷新">
          <Button
            type="text"
            icon={<ReloadOutlined />}
            size="small"
            onClick={onRefresh}
          />
        </Tooltip>
      </div>
      <div style={{ flex: 1, overflow: 'auto', padding: '8px' }}>
        <Tree
          showIcon={false}
          treeData={treeData}
          expandedKeys={expandedKeys}
          onExpand={handleExpand}
          onSelect={onSelect}
          loadData={onLoadData}
          selectedKeys={
            (selectedTable && selectedDatabase
              ? [
                  `db-${selectedDatabase}-schema-${selectedTable.split('.')[0]}-table-${selectedTable.split('.')[1]}`,
                ]
              : selectedDatabase
                ? [`db-${selectedDatabase}`]
                : []) as React.Key[]
          }
          titleRender={renderTitle}
          blockNode
          style={{ fontSize: '14px' }}
        />
      </div>
    </div>
  )
}

