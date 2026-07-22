/**
 * DB-GPT Data Intelligence API
 * - 数据源管理：直接调用 DB-GPT 原生 API (port 5670)
 * - 对话/SQL：调用 dbgpt-data-service 微服务 (port 8100)
 */

import axios from 'axios'
import { generateRandomString } from '@/utils'

const dbgptApi = axios.create({
  baseURL: '',
  timeout: 30000,
  headers: { 'Content-Type': 'application/json' },
})

const dataApi = axios.create({
  baseURL: '',
  timeout: 120000,
  headers: {
    'Content-Type': 'application/json',
    'X-Request-ID': generateRandomString(12),
  },
})

// ============ Types ============

/** DB-GPT 原生数据源 */
export interface DBGPTDatabase {
  id: number
  db_name: string
  db_type: string
  db_path: string
  db_host: string
  db_port: number
  db_user: string
  comment: string
}

/** 微服务数据源（兼容旧接口） */
export interface DatabaseInfo {
  id: string
  name: string
  db_type: string
  description: string
}

export interface TableInfo {
  name: string
  columns: number
  rows: number
}

// ============ DB-GPT 原生数据源 API ============

/** 获取 DB-GPT 中所有数据源 */
export async function fetchDBGPTDatabases(): Promise<DBGPTDatabase[]> {
  const { data } = await dbgptApi.get('/api/v1/chat/db/list')
  if (data.success && Array.isArray(data.data)) {
    return data.data
  }
  return []
}

/** 在 DB-GPT 中添加数据源 */
export async function addDBGPTDatabase(params: {
  db_name: string
  db_type: string
  db_path?: string
  db_host?: string
  db_port?: number
  db_user?: string
  db_pwd?: string
  comment?: string
}): Promise<any> {
  const { data } = await dbgptApi.post('/api/v1/chat/db/add', params)
  return data
}

/** 删除 DB-GPT 数据源 */
export async function deleteDBGPTDatabase(id: number): Promise<any> {
  const { data } = await dbgptApi.post('/api/v1/chat/db/delete', { db_id: id })
  return data
}

/** 测试 DB-GPT 数据源连接 */
export async function testDBGPTConnection(id: number): Promise<any> {
  const { data } = await dbgptApi.post('/api/v1/chat/db/test', { db_id: id })
  return data
}

/** 获取数据源的表列表 — 通过微服务代理 */
export async function listDBGPTTables(dbId: number, dbPath?: string): Promise<TableInfo[]> {
  const { data } = await dataApi.get('/api/tables', { params: { db_path: dbPath || '', db_id: dbId } })
  return data.tables || []
}

// ============ Chat (via dbgpt-data-service) ============

export function buildChatStreamUrl(
  question: string,
  dbUrl: string,
  dialect = 'sqlite',
  dbName = ''
): string {
  const params = new URLSearchParams({ question, dialect })
  if (dbName) {
    params.set('db_name', dbName)
  } else {
    params.set('db_url', dbUrl || 'sqlite:///:memory:')
  }
  return `/api/chat/stream?${params.toString()}`
}

// ============ 微服务数据库 CRUD（保留兼容） ============

export interface QueryResult {
  columns: string[]
  rows: Record<string, any>[]
  row_count: number
}

export interface SchemaResult {
  schema: string
}

export async function listDatabases(): Promise<{ databases: DatabaseInfo[] }> {
  const { data } = await dataApi.get('/api/databases')
  return data
}

export async function listTables(id: string): Promise<{ tables: TableInfo[] }> {
  const { data } = await dataApi.get(`/api/databases/${id}/tables`)
  return data
}

export async function getTableSchema(id: string, table?: string): Promise<SchemaResult> {
  const params = table ? { table } : undefined
  const { data } = await dataApi.get(`/api/databases/${id}/schema`, { params })
  return data
}

export async function executeQuery(id: string, sql: string): Promise<QueryResult> {
  const { data } = await dataApi.post(`/api/databases/${id}/query`, { sql })
  return data
}

export async function createDatabase(req: {
  name: string
  db_type: string
  db_url: string
  description?: string
}): Promise<DatabaseInfo> {
  const { data } = await dataApi.post('/api/databases/connect', req)
  return data
}

export async function deleteDatabase(id: string): Promise<void> {
  await dataApi.delete(`/api/databases/${id}`)
}

export async function testConnection(id: string): Promise<{ status: string; message: string }> {
  const { data } = await dataApi.post(`/api/databases/${id}/test`)
  return data
}

// ============ Connector Types API ============

export interface ConnectorType {
  name: string
  label: string
  icon: string
  desc: string
  parameters: any[]
}

export interface DatabaseConnection {
  id: string
  type: string
  params: Record<string, any>
  description: string
}

export async function fetchConnectorTypes(): Promise<ConnectorType[]> {
  const { data } = await dataApi.get('/api/connectors/types')
  if (data.data?.types) return data.data.types
  if (data.types) return data.types
  return []
}

export async function fetchDatabaseConnections(): Promise<DatabaseConnection[]> {
  const { data } = await dataApi.get('/api/connectors')
  if (data.data) return data.data
  return []
}

export async function createDatabaseConnection(params: Record<string, any>): Promise<any> {
  const { data } = await dataApi.post('/api/connectors', params)
  return data
}

export async function updateDatabaseConnection(params: Record<string, any>): Promise<any> {
  const { data } = await dataApi.put(`/api/connectors/${params.id}`, params)
  return data
}

export async function deleteDatabaseConnection(id: string): Promise<any> {
  const { data } = await dataApi.delete(`/api/connectors/${id}`)
  return data
}

export async function testDatabaseConnection(params: Record<string, any>): Promise<any> {
  const { data } = await dataApi.post('/api/connectors/test', params)
  return data
}

export async function refreshDatabaseConnection(id: string): Promise<any> {
  const { data } = await dataApi.post(`/api/connectors/${id}/refresh`)
  return data
}
