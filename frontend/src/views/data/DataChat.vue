<template>
  <div class="data-chat">
    <!-- Sidebar: DB-GPT 数据源 -->
    <aside class="chat-sidebar">
      <div class="sidebar-header">
        <h3>数据源</h3>
        <button class="btn-icon" @click="$router.push('/platform/data-sources')" title="管理数据源">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/></svg>
        </button>
      </div>

      <div class="db-list" v-if="dbList.length > 0">
        <div
          v-for="db in dbList"
          :key="db.id"
          class="db-item"
          :class="{ active: activeDb?.id === db.id }"
          @click="selectDB(db)"
        >
          <div class="db-icon">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
              <ellipse cx="12" cy="6" rx="8" ry="3"/><path d="M4 6v6c0 1.66 3.58 3 8 3s8-1.34 8-3V6"/><path d="M4 12v6c0 1.66 3.58 3 8 3s8-1.34 8-3v-6"/>
            </svg>
          </div>
          <div class="db-info">
            <span class="db-name">{{ db.db_name }}</span>
            <span class="db-type">{{ db.db_type }}</span>
          </div>
        </div>
      </div>
      <div class="db-empty" v-else-if="!loadingDbs">
        <p>暂无数据源</p>
        <button class="btn-link-sm" @click="$router.push('/platform/data-sources')">去添加</button>
      </div>
      <div class="db-loading" v-else>加载中...</div>
    </aside>

    <!-- Main -->
    <main class="chat-main">
      <!-- Active DB badge -->
      <div class="active-db-badge" v-if="activeDb">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><ellipse cx="12" cy="6" rx="8" ry="3"/><path d="M4 6v6c0 1.66 3.58 3 8 3s8-1.34 8-3V6"/><path d="M4 12v6c0 1.66 3.58 3 8 3s8-1.34 8-3v-6"/></svg>
        <span>{{ activeDb.db_name }}</span>
        <span class="badge-type">{{ activeDb.db_type }}</span>
      </div>

      <!-- Messages -->
      <div class="messages-container" ref="msgContainer">
        <div class="welcome" v-if="messages.length === 0">
          <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1" opacity="0.2">
            <ellipse cx="12" cy="6" rx="8" ry="3"/><path d="M4 6v6c0 1.66 3.58 3 8 3s8-1.34 8-3V6"/><path d="M4 12v6c0 1.66 3.58 3 8 3s8-1.34 8-3v-6"/>
          </svg>
          <p>选择左侧数据源，输入自然语言问题开始分析</p>
          <p class="welcome-hint">例：上个月销售额最高的 5 个产品是什么？</p>
        </div>

        <div v-for="msg in messages" :key="msg.id" class="message" :class="msg.role">
          <div class="msg-content">
            <template v-if="msg.type === 'sql'">
              <div class="sql-block">
                <div class="sql-label">生成的 SQL</div>
                <pre class="sql-code">{{ msg.sql }}</pre>
              </div>
            </template>
            <template v-else-if="msg.type === 'table' && msg.tableData">
              <DataTable
                :columns="msg.tableData.columns"
                :rows="msg.tableData.rows"
                :total-rows="msg.tableData.row_count"
              />
            </template>
            <template v-else-if="msg.type === 'error'">
              <div class="msg-error">{{ msg.content }}</div>
            </template>
            <template v-else-if="msg.type === 'status'">
              <div class="msg-status">{{ msg.content }}</div>
            </template>
            <template v-else>
              <div class="msg-text">{{ msg.content }}</div>
            </template>
          </div>
        </div>
      </div>

      <!-- Input -->
      <div class="input-area">
        <textarea
          v-model="question"
          class="question-input"
          :placeholder="activeDb ? '输入自然语言问题，如：本月订单总金额是多少？' : '请先选择左侧数据源'"
          :disabled="!activeDb || streaming"
          rows="2"
          @keydown.enter.exact.prevent="handleSend"
        />
        <button class="btn-send" :disabled="!activeDb || !question.trim() || streaming" @click="handleSend">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/></svg>
        </button>
      </div>
    </main>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, nextTick } from 'vue'
import { useRoute } from 'vue-router'
import { fetchDBGPTDatabases, buildChatStreamUrl, type DBGPTDatabase } from '@/api/data'
import DataTable from '@/components/data/DataTable.vue'

const route = useRoute()
const msgContainer = ref<HTMLElement>()

const dbList = ref<DBGPTDatabase[]>([])
const loadingDbs = ref(true)
const activeDb = ref<DBGPTDatabase | null>(null)
const question = ref('')
const streaming = ref(false)

interface ChatMessage {
  id: number
  role: 'user' | 'assistant' | 'system'
  content: string
  type?: 'text' | 'sql' | 'table' | 'status' | 'error'
  sql?: string
  tableData?: { columns: string[]; rows: any[]; row_count: number }
}

const messages = ref<ChatMessage[]>([])
let msgId = 0

onMounted(async () => {
  try {
    dbList.value = await fetchDBGPTDatabases()
  } catch (e) {
    console.error(e)
  } finally {
    loadingDbs.value = false
  }

  // 从 URL query 中恢复选中的数据源
  const qDbId = route.query.db_id as string
  const qDbName = route.query.db_name as string
  const qDbType = route.query.db_type as string
  const qDbPath = route.query.db_path as string

  if (qDbId) {
    const found = dbList.value.find(d => String(d.id) === qDbId)
    if (found) {
      activeDb.value = found
    } else {
      // 构造一个临时对象（可能在 datasource 页面添加后还没刷新列表）
      activeDb.value = {
        id: Number(qDbId),
        db_name: qDbName,
        db_type: qDbType,
        db_path: qDbPath,
        db_host: '',
        db_port: 0,
        db_user: '',
        comment: '',
      }
    }
  }
})

function selectDB(db: DBGPTDatabase) {
  activeDb.value = db
}

function getDbUrl(db: DBGPTDatabase): string {
  if (db.db_type === 'sqlite') {
    return db.db_path
  }
  // MySQL/PostgreSQL: 如果有完整配置就构造 URL
  if (db.db_host && db.db_user) {
    const portPart = db.db_port ? `:${db.db_port}` : ''
    return `${db.db_type}://${db.db_user}@${db.db_host}${portPart}/${db.db_name}`
  }
  return db.db_path || ''
}

async function handleSend() {
  const q = question.value.trim()
  if (!q || !activeDb.value || streaming.value) return

  const db = activeDb.value
  question.value = ''

  messages.value.push({ id: ++msgId, role: 'user', content: q })
  streaming.value = true

  const url = buildChatStreamUrl(q, '', db.db_type, db.db_name)

  try {
    const eventSource = new EventSource(url)

    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)

        switch (data.type) {
          case 'status':
            messages.value.push({ id: ++msgId, role: 'assistant', content: data.content, type: 'status' })
            break
          case 'schema':
            // Schema info, skip display
            break
          case 'sql':
            messages.value.push({
              id: ++msgId,
              role: 'assistant',
              content: '生成的 SQL',
              type: 'sql',
              sql: data.content,
            })
            break
          case 'result':
            messages.value.push({
              id: ++msgId,
              role: 'assistant',
              content: `查询结果：${data.row_count} 行`,
              type: 'table',
              tableData: data,
            })
            scrollToBottom()
            break
          case 'error':
            messages.value.push({ id: ++msgId, role: 'system', content: data.content, type: 'error' })
            eventSource.close()
            streaming.value = false
            break
          case 'done':
            eventSource.close()
            streaming.value = false
            break
        }
        scrollToBottom()
      } catch { /* ignore non-JSON */ }
    }

    eventSource.onerror = () => {
      eventSource.close()
      streaming.value = false
      if (messages.value[messages.value.length - 1]?.type !== 'error') {
        messages.value.push({ id: ++msgId, role: 'system', content: '连接中断，请重试', type: 'error' })
      }
      scrollToBottom()
    }
  } catch (e: any) {
    messages.value.push({ id: ++msgId, role: 'system', content: `请求失败: ${e.message}`, type: 'error' })
    streaming.value = false
  }
}

function scrollToBottom() {
  nextTick(() => {
    if (msgContainer.value) {
      msgContainer.value.scrollTop = msgContainer.value.scrollHeight
    }
  })
}
</script>

<style scoped>
.data-chat {
  display: flex;
  height: calc(100vh - 56px);
  background: var(--color-bg-layout, #f5f5f5);
}

/* Sidebar */
.chat-sidebar {
  width: 260px;
  min-width: 220px;
  background: var(--color-bg-container, #fff);
  border-right: 1px solid var(--color-border, #e5e7eb);
  display: flex;
  flex-direction: column;
  overflow-y: auto;
}
.sidebar-header {
  display: flex; justify-content: space-between; align-items: center;
  padding: 16px 16px 12px;
}
.sidebar-header h3 { margin: 0; font-size: 14px; font-weight: 600; }
.btn-icon {
  display: flex; align-items: center; justify-content: center;
  width: 30px; height: 30px; border: none; border-radius: 6px;
  background: transparent; color: var(--color-text-secondary, #6b7280);
  cursor: pointer; transition: all 0.15s;
}
.btn-icon:hover { background: var(--color-fill, #f3f4f6); }
.db-list { padding: 0 8px; }
.db-item {
  display: flex; align-items: center; gap: 10px; padding: 10px 12px;
  border-radius: 8px; cursor: pointer; transition: background 0.15s;
}
.db-item:hover { background: var(--color-fill, #f3f4f6); }
.db-item.active { background: var(--color-primary-bg, #eef2ff); }
.db-icon { color: var(--color-primary, #1677ff); flex-shrink: 0; }
.db-info { display: flex; flex-direction: column; min-width: 0; }
.db-name { font-size: 13px; font-weight: 500; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.db-type { font-size: 11px; color: var(--color-text-tertiary, #9ca3af); }
.db-empty, .db-loading { padding: 24px; text-align: center; color: var(--color-text-tertiary, #9ca3af); font-size: 13px; }
.btn-link-sm { margin-top: 6px; padding: 4px 12px; border: 1px solid var(--color-primary, #1677ff); border-radius: 6px; background: none; color: var(--color-primary, #1677ff); font-size: 12px; cursor: pointer; }

/* Main */
.chat-main { flex: 1; display: flex; flex-direction: column; min-width: 0; }

.active-db-badge {
  display: flex; align-items: center; gap: 6px;
  margin: 8px 16px 0; padding: 6px 12px;
  background: var(--color-bg-container, #fff);
  border: 1px solid var(--color-border, #e5e7eb);
  border-radius: 8px; font-size: 13px;
}
.active-db-badge svg { color: var(--color-primary, #1677ff); }
.badge-type {
  font-size: 11px; padding: 1px 6px; border-radius: 4px;
  background: var(--color-fill, #f3f4f6); color: var(--color-text-tertiary, #9ca3af);
  text-transform: uppercase;
}

/* Messages */
.messages-container { flex: 1; overflow-y: auto; padding: 16px; }
.welcome { text-align: center; padding: 60px 20px; color: var(--color-text-secondary, #6b7280); }
.welcome p { margin: 12px 0 0; font-size: 15px; }
.welcome-hint { font-size: 12px !important; color: var(--color-text-tertiary, #9ca3af) !important; }
.message { margin-bottom: 16px; display: flex; }
.message.user { justify-content: flex-end; }
.message.user .msg-content {
  background: var(--color-primary, #1677ff); color: #fff;
  border-radius: 12px 12px 4px 12px;
}
.message.assistant .msg-content,
.message.system .msg-content {
  background: var(--color-bg-container, #fff);
  border: 1px solid var(--color-border, #e5e7eb);
  border-radius: 12px 12px 12px 4px;
}
.msg-content { max-width: 85%; padding: 10px 14px; font-size: 14px; line-height: 1.5; overflow-x: auto; }
.msg-error { color: #dc2626; font-size: 13px; }
.msg-status { color: var(--color-text-tertiary, #9ca3af); font-size: 13px; font-style: italic; }
.msg-text { white-space: pre-wrap; word-break: break-word; }

.sql-block { margin: -10px -14px; }
.sql-label { padding: 6px 14px; font-size: 11px; font-weight: 600; color: var(--color-text-tertiary, #9ca3af); text-transform: uppercase; background: var(--color-fill, #f3f4f6); }
.sql-code { margin: 0; padding: 10px 14px; font-size: 12px; font-family: 'SF Mono', 'Fira Code', monospace; overflow-x: auto; white-space: pre; line-height: 1.6; }

/* Input */
.input-area {
  display: flex; gap: 8px; padding: 12px 16px;
  background: var(--color-bg-container, #fff);
  border-top: 1px solid var(--color-border, #e5e7eb);
}
.question-input {
  flex: 1; padding: 10px 14px; border: 1px solid var(--color-border, #d1d5db);
  border-radius: 10px; font-size: 14px; resize: none; outline: none;
  font-family: inherit; transition: border-color 0.2s;
}
.question-input:focus { border-color: var(--color-primary, #1677ff); }
.btn-send {
  display: flex; align-items: center; justify-content: center;
  width: 44px; height: 44px; border: none; border-radius: 10px;
  background: var(--color-primary, #1677ff); color: #fff;
  cursor: pointer; transition: opacity 0.15s; flex-shrink: 0;
}
.btn-send:disabled { opacity: 0.4; cursor: not-allowed; }
.btn-send:hover:not(:disabled) { opacity: 0.85; }
</style>
