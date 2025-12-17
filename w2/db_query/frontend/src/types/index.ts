/** TypeScript type definitions for API responses */

export interface DatabaseConnection {
  name: string
  url: string
  databaseType: string
  createdAt: string
  updatedAt: string
}

export interface DatabaseListResponse {
  databases: DatabaseConnection[]
}

export interface DatabaseConnectionRequest {
  url: string
}

export interface MetadataResponse {
  name: string
  metadata: {
    tables: Array<{
      name: string
      schema?: string
      type: string
      columns?: Array<{
        name: string
        type: string
        nullable: boolean
        default: string | null
      }>
      rowCount?: number
    }>
  }
}

export interface SqlQueryRequest {
  sql: string
}

export interface SqlQueryResponse {
  columns: string[]
  rows: any[][]
  rowCount: number
}

export interface NaturalLanguageQueryRequest {
  prompt: string
}

export interface NaturalLanguageQueryResponse {
  sql: string
  explanation: string | null
}

export interface ErrorResponse {
  error: {
    code: string
    message: string
    details: any | null
  }
}

