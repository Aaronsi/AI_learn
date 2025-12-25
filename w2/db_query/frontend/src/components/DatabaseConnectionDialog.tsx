import { useState, useEffect } from 'react'
import {
  Modal,
  Form,
  Input,
  Button,
  message,
  Select,
  Space,
} from 'antd'
import { DatabaseOutlined } from '@ant-design/icons'
import { apiClient } from '../api/client'
import type { DatabaseConnection } from '../types'

const { Option } = Select

interface DatabaseConnectionDialogProps {
  open: boolean
  onClose: () => void
  onSuccess: () => void
  initialValues?: DatabaseConnection
}

export default function DatabaseConnectionDialog({
  open,
  onClose,
  onSuccess,
  initialValues,
}: DatabaseConnectionDialogProps) {
  const [form] = Form.useForm()
  const [connectionMethod, setConnectionMethod] = useState<'host' | 'url'>('host')
  const [databaseType, setDatabaseType] = useState<string>('postgresql')
  const [testing, setTesting] = useState(false)
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    if (open) {
      if (initialValues) {
        // Parse URL to fill form
        const url = initialValues.url
        // Detect database type from URL
        const dbTypeMatch = url.match(/^(\w+):\/\//)
        const detectedType = dbTypeMatch ? dbTypeMatch[1] : 'postgresql'
        setDatabaseType(initialValues.databaseType || detectedType)
        
        // Try to parse as host-based connection
        const match = url.match(/^(\w+):\/\/([^:]+):([^@]+)@([^:]+):(\d+)\/(.+)$/)
        if (match) {
          const [, scheme, user, password, host, port, database] = match
          setConnectionMethod('host')
          form.setFieldsValue({
            name: initialValues.name,
            connectionMethod: 'host',
            databaseType: initialValues.databaseType || scheme,
            host,
            port,
            database,
            username: user,
            password,
            url: undefined, // Clear URL field
          })
        } else {
          setConnectionMethod('url')
          form.setFieldsValue({
            name: initialValues.name,
            connectionMethod: 'url',
            databaseType: initialValues.databaseType || detectedType,
            url: initialValues.url,
            host: undefined, // Clear host fields
            port: undefined,
            database: undefined,
            username: undefined,
            password: undefined,
          })
        }
      } else {
        form.resetFields()
        setConnectionMethod('host')
        setDatabaseType('postgresql')
      }
    } else {
      // Reset form when dialog closes
      form.resetFields()
      setConnectionMethod('host')
      setDatabaseType('postgresql')
    }
  }, [open, initialValues, form])

  const handleTestConnection = async () => {
    console.log('[Test Connection] Button clicked')
    console.log('[Test Connection] Connection method:', connectionMethod)
    console.log('[Test Connection] Database type:', databaseType)
    
    try {
      // Validate fields based on connection method
      const fieldsToValidate = connectionMethod === 'host' 
        ? ['host', 'port', 'database', 'username', 'password']
        : ['url']
      
      console.log('[Test Connection] Fields to validate:', fieldsToValidate)
      
      // Get all form values first for debugging
      const allValues = form.getFieldsValue()
      console.log('[Test Connection] All form values:', { 
        ...allValues, 
        password: allValues.password ? '***' : undefined 
      })
      
      console.log('[Test Connection] Starting validation...')
      const values = await form.validateFields(fieldsToValidate)
      console.log('[Test Connection] Validation passed!', { ...values, password: '***' })
      
      setTesting(true)
      console.log('[Test Connection] Set testing state to true')

      let connectionUrl: string
      const dbType = values.databaseType || databaseType || 'postgresql'
      
      if (connectionMethod === 'host') {
        const { host, port, database, username, password } = values
        if (!password) {
          message.error('请输入密码')
          setTesting(false)
          return
        }
        // Encode password for URL
        const encodedPassword = encodeURIComponent(password)
        connectionUrl = `${dbType}://${username}:${encodedPassword}@${host}:${port}/${database}`
      } else {
        connectionUrl = values.url
      }

      console.log('[Test Connection] Calling API...')
      console.log('[Test Connection] URL:', connectionUrl.replace(/:[^:@]+@/, ':***@'))
      console.log('[Test Connection] Database type:', dbType)
      
      // Use the new test connection API
      const result = await apiClient.testConnection({
        url: connectionUrl,
        databaseType: dbType,
      })
      
      console.log('[Test Connection] API response:', result)
      
      if (result.success) {
        console.log('[Test Connection] Success!')
        message.success(result.message || '连接测试成功！数据库连接正常。')
        // Update database type if detected
        if (result.databaseType && result.databaseType !== dbType) {
          setDatabaseType(result.databaseType)
          form.setFieldValue('databaseType', result.databaseType)
        }
      } else {
        console.log('[Test Connection] Failed:', result.message)
        message.error(result.message || '连接测试失败')
      }
    } catch (error: any) {
      const errorMessage = error.message || error?.response?.data?.error?.message || '连接测试失败'
      
      // Check if it's a validation error
      const isValidationError = errorMessage.includes('required') || 
                                errorMessage.includes('请填写') || 
                                errorMessage.includes('请输入') ||
                                (error?.errorFields && error.errorFields.length > 0)
      
      if (isValidationError) {
        // Validation errors are shown by Form.Item, but show a general message too
        message.warning('请先填写所有必填字段')
      } else {
        // Show API errors
        message.error(`连接测试失败: ${errorMessage}`)
      }
    } finally {
      setTesting(false)
    }
  }

  const handleFinish = async () => {
    try {
      setSaving(true)
      
      // Step 1: Validate all form fields (check if form is complete)
      const fieldsToValidate = connectionMethod === 'host'
        ? ['name', 'host', 'port', 'database', 'username', 'password']
        : ['name', 'url']
      
      const values = await form.validateFields(fieldsToValidate)
      
      // Step 2: Build connection URL
      let connectionUrl: string
      const dbType = values.databaseType || databaseType || 'postgresql'
      
      if (connectionMethod === 'host') {
        const { host, port, database, username, password } = values
        // Encode password for URL
        const encodedPassword = encodeURIComponent(password)
        connectionUrl = `${dbType}://${username}:${encodedPassword}@${host}:${port}/${database}`
      } else {
        connectionUrl = values.url
      }
      
      // Step 3: Test connection before saving
      try {
        const testResult = await apiClient.testConnection({
          url: connectionUrl,
          databaseType: dbType,
        })
        
        if (!testResult.success) {
          message.error(testResult.message || '数据库连接测试失败')
          setSaving(false)
          return
        }
      } catch (error: any) {
        const errorMessage = error.message || '数据库连接失败'
        message.error(`数据库连接测试失败: ${errorMessage}`)
        setSaving(false)
        return
      }
      
      // Step 4: Save the connection
      await apiClient.putDatabase(values.name, { 
        url: connectionUrl,
        databaseType: dbType,
      })
      message.success(initialValues ? '数据库连接已更新' : '数据库连接已添加')
      
      // Step 5: Reset form and close dialog
      form.resetFields()
      onSuccess()
      onClose()
    } catch (error: any) {
      // Handle validation errors (they are shown by Form.Item)
      const errorMessage = error.message || '保存失败'
      if (!errorMessage.includes('required') && !errorMessage.includes('请填写') && !errorMessage.includes('请输入')) {
        message.error(errorMessage)
      }
    } finally {
      setSaving(false)
    }
  }

  const connectionFormContent = (
    <Form 
      form={form} 
      layout="vertical" 
      style={{ marginTop: '24px' }}
      initialValues={{
        connectionMethod: 'host',
        databaseType: 'postgresql',
        host: 'localhost',
        port: '5432',
        username: 'postgres',
      }}
      onFinish={(values) => {
        // Prevent form submission from triggering on button click
        console.log('Form onFinish called (should not happen for test button)')
      }}
    >
      <Form.Item
        label="连接名称"
        name="name"
        rules={[{ required: true, message: '请输入连接名称' }]}
      >
        <Input placeholder="例如: postgres" />
      </Form.Item>

      <Form.Item
        label="数据库类型"
        name="databaseType"
        rules={[{ required: true, message: '请选择数据库类型' }]}
      >
        <Select
          value={databaseType}
          onChange={(value) => {
            setDatabaseType(value)
            form.setFieldValue('databaseType', value)
            // Update default port based on database type
            if (connectionMethod === 'host') {
              const defaultPorts: Record<string, string> = {
                postgresql: '5432',
                mysql: '3306',
                mariadb: '3306',
              }
              if (defaultPorts[value]) {
                form.setFieldValue('port', defaultPorts[value])
              }
            }
          }}
        >
          <Option value="postgresql">PostgreSQL</Option>
          <Option value="mysql">MySQL</Option>
          <Option value="mariadb">MariaDB</Option>
        </Select>
      </Form.Item>

      <Form.Item
        label="连接方式"
        name="connectionMethod"
      >
        <Select
          value={connectionMethod}
          onChange={(value) => {
            setConnectionMethod(value)
            form.setFieldValue('connectionMethod', value)
            // Clear fields when switching methods
            if (value === 'host') {
              form.setFieldsValue({
                url: undefined,
              })
            } else {
              form.setFieldsValue({
                host: undefined,
                port: undefined,
                database: undefined,
                username: undefined,
                password: undefined,
              })
            }
          }}
        >
          <Option value="host">主机</Option>
          <Option value="url">URL</Option>
        </Select>
      </Form.Item>

      {connectionMethod === 'host' ? (
        <>
          <Form.Item
            label="主机"
            name="host"
            rules={[{ required: true, message: '请输入主机地址' }]}
          >
            <Input placeholder="localhost" />
          </Form.Item>
          <Form.Item
            label="端口"
            name="port"
            rules={[{ required: true, message: '请输入端口' }]}
          >
            <Input placeholder="5432" />
          </Form.Item>
          <Form.Item
            label="数据库"
            name="database"
            rules={[{ required: true, message: '请输入数据库名称' }]}
          >
            <Input placeholder="postgres" />
          </Form.Item>
          <Form.Item
            label="用户名"
            name="username"
            rules={[{ required: true, message: '请输入用户名' }]}
          >
            <Input placeholder="postgres" />
          </Form.Item>
          <Form.Item
            label="密码"
            name="password"
            rules={[{ required: true, message: '请输入密码' }]}
          >
            <Input.Password placeholder="密码" />
          </Form.Item>
        </>
      ) : (
        <Form.Item
          label="连接 URL"
          name="url"
          rules={[
            { required: true, message: '请输入连接 URL' },
            {
              pattern: /^(postgresql|mysql|mariadb):\/\//,
              message: 'URL 格式不正确，应以 postgresql://、mysql:// 或 mariadb:// 开头',
            },
          ]}
        >
          <Input.TextArea
            rows={3}
            placeholder={`${databaseType}://user:password@host:port/database`}
          />
        </Form.Item>
      )}
    </Form>
  )

  return (
    <Modal
      title={
        <Space>
          <DatabaseOutlined />
          <span>{initialValues ? '编辑数据库连接' : '连接到数据库'}</span>
        </Space>
      }
      open={open}
      onCancel={onClose}
      width={600}
      footer={[
        <Button key="cancel" onClick={onClose} disabled={testing || saving}>
          取消
        </Button>,
        <Button
          key="test"
          htmlType="button"
          onClick={(e) => {
            console.log('[Button] onClick triggered')
            e.preventDefault()
            e.stopPropagation()
            console.log('[Button] Calling handleTestConnection')
            handleTestConnection().catch((err) => {
              console.error('[Button] Unhandled error:', err)
              message.error('测试连接时发生错误: ' + (err.message || '未知错误'))
            })
          }}
          loading={testing}
          type="default"
          disabled={saving}
        >
          测试连接
        </Button>,
        <Button
          key="finish"
          type="primary"
          onClick={handleFinish}
          loading={saving}
          disabled={testing}
        >
          完成
        </Button>,
      ]}
    >
      {connectionFormContent}
    </Modal>
  )
}

