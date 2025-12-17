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

