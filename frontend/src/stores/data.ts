/**
 * Data Intelligence Store — 数据智能模块状态管理
 */

import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { DatabaseInfo, TableInfo, QueryResult } from '@/api/data'
import { listDatabases, listTables } from '@/api/data'

export interface DataChatMessage {
  id: string
  role: 'user' | 'assistant' | 'system'
  content: string
  type?: 'text' | 'sql' | 'table' | 'chart' | 'error' | 'status'
  sql?: string
  tableData?: QueryResult
  timestamp: number
}

export const useDataStore = defineStore('data', () => {
  // Database connections
  const databases = ref<DatabaseInfo[]>([])
  const databasesLoading = ref(false)

  // Current selected database
  const currentDbId = ref<string>('')
  const currentTables = ref<TableInfo[]>([])
  const currentSchema = ref<string>('')
  const tablesLoading = ref(false)

  // Chat messages
  const messages = ref<DataChatMessage[]>([])
  const streaming = ref(false)

  // Query results
  const queryResult = ref<QueryResult | null>(null)
  const queryLoading = ref(false)

  let messageCounter = 0

  function nextId(): string {
    return `data-msg-${++messageCounter}-${Date.now()}`
  }

  async function refreshDatabases() {
    databasesLoading.value = true
    try {
      const res = await listDatabases()
      databases.value = res.databases || []
    } catch (e) {
      console.error('Failed to load databases', e)
      databases.value = []
    } finally {
      databasesLoading.value = false
    }
  }

  async function refreshTables(dbId: string) {
    if (!dbId) return
    currentDbId.value = dbId
    tablesLoading.value = true
    try {
      const res = await listTables(dbId)
      currentTables.value = res.tables || []
    } catch (e) {
      console.error('Failed to load tables', e)
      currentTables.value = []
    } finally {
      tablesLoading.value = false
    }
  }

  function addMessage(msg: Omit<DataChatMessage, 'id' | 'timestamp'>) {
    messages.value.push({
      ...msg,
      id: nextId(),
      timestamp: Date.now(),
    })
  }

  function clearMessages() {
    messages.value = []
    messageCounter = 0
  }

  function setStreaming(v: boolean) {
    streaming.value = v
  }

  return {
    databases,
    databasesLoading,
    currentDbId,
    currentTables,
    currentSchema,
    tablesLoading,
    messages,
    streaming,
    queryResult,
    queryLoading,
    refreshDatabases,
    refreshTables,
    addMessage,
    clearMessages,
    setStreaming,
  }
})
