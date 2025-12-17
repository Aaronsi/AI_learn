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
  const [testing, setTesting] = useState(false)
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    if (open) {
      if (initialValues) {
        // Parse URL to fill form
        const url = initialValues.url
        const match = url.match(/^postgresql:\/\/([^:]+):([^@]+)@([^:]+):(\d+)\/(.+)$/)
        if (match) {
          const [, user, password, host, port, database] = match
          setConnectionMethod('host')
          form.setFieldsValue({
            name: initialValues.name,
            connectionMethod: 'host',
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
      }
    } else {
      // Reset form when dialog closes
      form.resetFields()
      setConnectionMethod('host')
    }
  }, [open, initialValues, form])

  const handleTestConnection = async () => {
    try {
      // Validate name first
      await form.validateFields(['name'])
      
      // Validate fields based on connection method
      const fieldsToValidate = connectionMethod === 'host' 
        ? ['host', 'port', 'database', 'username', 'password']
        : ['url']
      
      const values = await form.validateFields(fieldsToValidate)
      setTesting(true)

      let connectionUrl: string
      if (connectionMethod === 'host') {
        const { host, port, database, username, password } = values
        connectionUrl = `postgresql://${username}:${password}@${host}:${port}/${database}`
      } else {
        connectionUrl = values.url
      }

      // Create a temporary connection name for testing
      const testName = `__test_${Date.now()}`
      try {
        await apiClient.putDatabase(testName, { url: connectionUrl })
        
        // Try to delete test connection
        try {
          await apiClient.deleteDatabase(testName)
        } catch {
          // Ignore delete errors for test connection
        }
        
        message.success('连接测试成功！数据库连接正常。')
      } catch (error: any) {
        // Try to delete test connection even if test failed
        try {
          await apiClient.deleteDatabase(testName)
        } catch {
          // Ignore delete errors
        }
        const errorMessage = error.message || '连接测试失败'
        message.error(`连接测试失败: ${errorMessage}`)
        throw error
      }
    } catch (error: any) {
      const errorMessage = error.message || '连接测试失败'
      // Only show error if it's not a validation error (validation errors are shown by Form.Item)
      if (!errorMessage.includes('required') && !errorMessage.includes('请填写') && !errorMessage.includes('请输入')) {
        // Error already shown above
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
      if (connectionMethod === 'host') {
        const { host, port, database, username, password } = values
        connectionUrl = `postgresql://${username}:${password}@${host}:${port}/${database}`
      } else {
        connectionUrl = values.url
      }
      
      // Step 3: Test connection before saving
      const testName = `__test_${Date.now()}`
      try {
        await apiClient.putDatabase(testName, { url: connectionUrl })
        
        // Delete test connection
        try {
          await apiClient.deleteDatabase(testName)
        } catch {
          // Ignore delete errors
        }
      } catch (error: any) {
        // Try to delete test connection even if test failed
        try {
          await apiClient.deleteDatabase(testName)
        } catch {
          // Ignore delete errors
        }
        const errorMessage = error.message || '数据库连接失败'
        message.error(`数据库连接测试失败: ${errorMessage}`)
        setSaving(false)
        return
      }
      
      // Step 4: Save the connection
      await apiClient.putDatabase(values.name, { url: connectionUrl })
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
        host: 'localhost',
        port: '5432',
        username: 'postgres',
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
              pattern: /^postgresql:\/\//,
              message: 'URL 格式不正确，应以 postgresql:// 开头',
            },
          ]}
        >
          <Input.TextArea
            rows={3}
            placeholder="postgresql://user:password@host:5432/database"
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
          onClick={handleTestConnection}
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

