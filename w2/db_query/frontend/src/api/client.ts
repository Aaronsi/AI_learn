/** API client for backend communication */
import axios, { AxiosInstance } from 'axios'
import type {
  DatabaseConnection,
  DatabaseListResponse,
  DatabaseConnectionRequest,
  MetadataResponse,
  SqlQueryRequest,
  SqlQueryResponse,
  NaturalLanguageQueryRequest,
  NaturalLanguageQueryResponse,
  TestConnectionRequest,
  TestConnectionResponse,
} from '../types'

const API_BASE_URL = '/api/v1'

class ApiClient {
  private client: AxiosInstance

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      headers: {
        'Content-Type': 'application/json',
      },
    })

    // Response interceptor for error handling
    this.client.interceptors.response.use(
      (response) => response,
      (error) => {
        // Preserve the full error object for better error handling
        if (error.response?.data?.error) {
          // Attach the error detail to the error object
          const apiError = error.response.data.error
          const enhancedError = new Error(apiError.message || '请求失败')
          ;(enhancedError as any).code = apiError.code
          ;(enhancedError as any).details = apiError.details
          ;(enhancedError as any).response = error.response
          return Promise.reject(enhancedError)
        }
        return Promise.reject(error)
      }
    )
  }

  async getDatabases(): Promise<DatabaseListResponse> {
    const response = await this.client.get<DatabaseListResponse>('/dbs')
    return response.data
  }

  async putDatabase(
    name: string,
    request: DatabaseConnectionRequest
  ): Promise<DatabaseConnection> {
    const response = await this.client.put<DatabaseConnection>(
      `/dbs/${name}`,
      request
    )
    return response.data
  }

  async getDatabaseMetadata(name: string): Promise<MetadataResponse> {
    const response = await this.client.get<MetadataResponse>(`/dbs/${name}`)
    return response.data
  }

  async refreshDatabaseMetadata(name: string): Promise<MetadataResponse> {
    const response = await this.client.post<MetadataResponse>(
      `/dbs/${name}/refresh`
    )
    return response.data
  }

  async queryDatabase(
    name: string,
    request: SqlQueryRequest
  ): Promise<SqlQueryResponse> {
    const response = await this.client.post<SqlQueryResponse>(
      `/dbs/${name}/query`,
      request
    )
    return response.data
  }

  async naturalLanguageQuery(
    name: string,
    request: NaturalLanguageQueryRequest
  ): Promise<NaturalLanguageQueryResponse> {
    const response = await this.client.post<NaturalLanguageQueryResponse>(
      `/dbs/${name}/query/natural`,
      request
    )
    return response.data
  }

  async deleteDatabase(name: string): Promise<void> {
    await this.client.delete(`/dbs/${name}`)
  }

  async testConnection(request: TestConnectionRequest): Promise<TestConnectionResponse> {
    try {
      console.log('[API Client] Calling POST /dbs/test with:', { 
        ...request, 
        url: request.url.replace(/:[^:@]+@/, ':***@') 
      })
      
      const response = await this.client.post<TestConnectionResponse>(
        '/dbs/test',
        request,
        {
          timeout: 30000, // 30 second timeout
        }
      )
      
      console.log('[API Client] Response received:', response.data)
      return response.data
    } catch (error: any) {
      console.error('[API Client] Error:', error)
      console.error('[API Client] Error response:', error.response?.data)
      console.error('[API Client] Error status:', error.response?.status)
      
      // Handle API errors and convert to TestConnectionResponse format
      if (error.response?.data?.error) {
        const apiError = error.response.data.error
        return {
          success: false,
          message: apiError.message || '连接测试失败',
          databaseType: request.databaseType || null,
        }
      }
      
      // Handle network errors
      if (error.code === 'ECONNABORTED' || error.message?.includes('timeout')) {
        return {
          success: false,
          message: '连接超时，请检查后端服务是否正常运行',
          databaseType: request.databaseType || null,
        }
      }
      
      if (error.code === 'ERR_NETWORK' || error.message?.includes('Network Error')) {
        return {
          success: false,
          message: '网络错误，无法连接到后端服务',
          databaseType: request.databaseType || null,
        }
      }
      
      // Re-throw if it's not an API error
      throw error
    }
  }

  async getDatabaseTables(
    name: string,
    schema?: string
  ): Promise<{
    schemas: Array<{
      name: string
      tables: Array<{
        name: string
        type: string
        schema: string
      }>
    }>
  }> {
    const params = schema ? { schema } : {}
    const response = await this.client.get(`/dbs/${name}/tables`, { params })
    return response.data
  }

  async getTableColumns(
    name: string,
    schema: string,
    table: string
  ): Promise<{
    schema: string
    table: string
    columns: Array<{
      name: string
      type: string
      nullable: boolean
      default: string | null
      position: number
    }>
  }> {
    const response = await this.client.get(
      `/dbs/${name}/tables/${schema}/${table}/columns`
    )
    return response.data
  }
}

export const apiClient = new ApiClient()

