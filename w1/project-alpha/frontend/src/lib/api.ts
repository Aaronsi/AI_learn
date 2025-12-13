import axios, { AxiosError } from 'axios'
import type {
  Ticket,
  TicketsListResponse,
  TicketCreate,
  TicketUpdate,
  Tag,
  TagCreate,
  ListTicketsParams,
  ListTagsParams,
  ErrorResponse,
} from '@/types'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// 错误类型
export enum ErrorType {
  NETWORK = 'network',
  VALIDATION = 'validation',
  SERVER = 'server',
  UNKNOWN = 'unknown',
}

export interface ParsedError {
  type: ErrorType
  message: string
  code?: string
  details?: Record<string, unknown>
}

// 错误处理
function handleError(error: unknown): ParsedError {
  if (axios.isAxiosError(error)) {
    const axiosError = error as AxiosError<ErrorResponse>

    // 网络错误（无响应）
    if (!axiosError.response) {
      return {
        type: ErrorType.NETWORK,
        message: '网络连接失败，请检查网络连接或稍后重试',
        code: 'network_error',
      }
    }

    // 服务器返回的错误
    if (axiosError.response.data?.error) {
      const errorData = axiosError.response.data.error
      const status = axiosError.response.status

      // 校验错误（422）
      if (status === 422) {
        return {
          type: ErrorType.VALIDATION,
          message: errorData.message || '输入数据验证失败',
          code: errorData.code,
          details: errorData.details,
        }
      }

      // 服务器错误（500+）
      if (status >= 500) {
        return {
          type: ErrorType.SERVER,
          message: '服务器错误，请稍后重试',
          code: errorData.code,
        }
      }

      // 其他客户端错误（400-499）
      return {
        type: ErrorType.SERVER,
        message: errorData.message || `请求失败 (${status})`,
        code: errorData.code,
        details: errorData.details,
      }
    }

    // 其他 HTTP 错误
    return {
      type: ErrorType.SERVER,
      message: `请求失败 (${axiosError.response.status})`,
      code: `http_${axiosError.response.status}`,
    }
  }

  return {
    type: ErrorType.UNKNOWN,
    message: '未知错误，请稍后重试',
    code: 'unknown_error',
  }
}

// Tickets API
export const ticketsApi = {
  list: async (params: ListTicketsParams = {}): Promise<TicketsListResponse> => {
    try {
      const queryParams = new URLSearchParams()
      if (params.status) queryParams.append('status', params.status)
      if (params.tags && params.tags.length > 0) {
        queryParams.append('tags', params.tags.join(','))
      }
      if (params.q) queryParams.append('q', params.q)
      if (params.limit) queryParams.append('limit', params.limit.toString())
      if (params.offset) queryParams.append('offset', params.offset.toString())

      const response = await apiClient.get<TicketsListResponse>(
        `/tickets?${queryParams.toString()}`
      )
      return response.data
    } catch (error) {
      const parsedError = handleError(error)
      const errorWithType = new Error(parsedError.message) as Error & { type: ErrorType; code?: string; details?: Record<string, unknown> }
      errorWithType.type = parsedError.type
      errorWithType.code = parsedError.code
      errorWithType.details = parsedError.details
      throw errorWithType
    }
  },

  get: async (id: string): Promise<Ticket> => {
    try {
      const response = await apiClient.get<Ticket>(`/tickets/${id}`)
      return response.data
    } catch (error) {
      const parsedError = handleError(error)
      const errorWithType = new Error(parsedError.message) as Error & { type: ErrorType; code?: string; details?: Record<string, unknown> }
      errorWithType.type = parsedError.type
      errorWithType.code = parsedError.code
      errorWithType.details = parsedError.details
      throw errorWithType
    }
  },

  create: async (data: TicketCreate): Promise<Ticket> => {
    try {
      const response = await apiClient.post<Ticket>('/tickets', data)
      return response.data
    } catch (error) {
      const parsedError = handleError(error)
      const errorWithType = new Error(parsedError.message) as Error & { type: ErrorType; code?: string; details?: Record<string, unknown> }
      errorWithType.type = parsedError.type
      errorWithType.code = parsedError.code
      errorWithType.details = parsedError.details
      throw errorWithType
    }
  },

  update: async (id: string, data: TicketUpdate): Promise<Ticket> => {
    try {
      const response = await apiClient.patch<Ticket>(`/tickets/${id}`, data)
      return response.data
    } catch (error) {
      const parsedError = handleError(error)
      const errorWithType = new Error(parsedError.message) as Error & { type: ErrorType; code?: string; details?: Record<string, unknown> }
      errorWithType.type = parsedError.type
      errorWithType.code = parsedError.code
      errorWithType.details = parsedError.details
      throw errorWithType
    }
  },

  delete: async (id: string): Promise<void> => {
    try {
      await apiClient.delete(`/tickets/${id}`)
    } catch (error) {
      const parsedError = handleError(error)
      const errorWithType = new Error(parsedError.message) as Error & { type: ErrorType; code?: string; details?: Record<string, unknown> }
      errorWithType.type = parsedError.type
      errorWithType.code = parsedError.code
      errorWithType.details = parsedError.details
      throw errorWithType
    }
  },
}

// Tags API
export const tagsApi = {
  list: async (params: ListTagsParams = {}): Promise<Tag[]> => {
    try {
      const queryParams = new URLSearchParams()
      if (params.q) queryParams.append('q', params.q)

      const response = await apiClient.get<Tag[]>(
        `/tags?${queryParams.toString()}`
      )
      return response.data
    } catch (error) {
      const parsedError = handleError(error)
      const errorWithType = new Error(parsedError.message) as Error & { type: ErrorType; code?: string; details?: Record<string, unknown> }
      errorWithType.type = parsedError.type
      errorWithType.code = parsedError.code
      errorWithType.details = parsedError.details
      throw errorWithType
    }
  },

  create: async (data: TagCreate): Promise<Tag> => {
    try {
      const response = await apiClient.post<Tag>('/tags', data)
      return response.data
    } catch (error) {
      const parsedError = handleError(error)
      const errorWithType = new Error(parsedError.message) as Error & { type: ErrorType; code?: string; details?: Record<string, unknown> }
      errorWithType.type = parsedError.type
      errorWithType.code = parsedError.code
      errorWithType.details = parsedError.details
      throw errorWithType
    }
  },

  delete: async (id: string): Promise<void> => {
    try {
      await apiClient.delete(`/tags/${id}`)
    } catch (error) {
      const parsedError = handleError(error)
      const errorWithType = new Error(parsedError.message) as Error & { type: ErrorType; code?: string; details?: Record<string, unknown> }
      errorWithType.type = parsedError.type
      errorWithType.code = parsedError.code
      errorWithType.details = parsedError.details
      throw errorWithType
    }
  },
}
