<template>
  <div class="db-page">
    <!-- Header -->
    <div class="db-header">
      <h2 class="db-title">{{ $t('database') || '数据库' }}</h2>
      <button class="db-btn-add" @click="openAddModal">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
          <line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/>
        </svg>
        {{ $t('Add_Datasource') || '添加数据源' }}
      </button>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="db-loading">
      <div class="db-spinner"></div>
      <p>加载中...</p>
    </div>

    <!-- Card Grid -->
    <div v-else class="db-grid">
      <div
        v-for="ct in connectorTypes"
        :key="ct.name"
        class="db-card"
        :class="{ 'db-card-disabled': isDisabled(ct) }"
        @click="onCardClick(ct)"
      >
        <div class="db-card-top">
          <img :src="getIcon(ct.name)" class="db-card-icon" @error="onImgError" :alt="ct.label" />
          <span v-if="getCount(ct.name) > 0" class="db-card-badge">{{ getCount(ct.name) }}</span>
        </div>
        <div class="db-card-body">
          <h3 class="db-card-title">{{ ct.label || ct.name }}</h3>
          <p class="db-card-desc">{{ getDesc(ct.name) || ct.description || '' }}</p>
        </div>
      </div>
    </div>

    <!-- Drawer -->
    <div class="db-drawer-overlay" v-if="drawerVisible" @click.self="closeDrawer"></div>
    <div class="db-drawer" :class="{ open: drawerVisible }">
      <div class="db-drawer-header">
        <h3 class="db-drawer-title">
          <img :src="getIcon(selectedType?.name || '')" class="db-drawer-title-icon" @error="onImgError" />
          {{ selectedType?.label || selectedType?.name }}
        </h3>
        <button class="db-drawer-close" @click="closeDrawer">&times;</button>
      </div>

      <div class="db-drawer-body">
        <!-- 刷新/添加按钮 -->
        <div class="db-drawer-actions" v-if="typeConnections.length > 0">
          <button class="db-btn-create" @click="openAddConnModal">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
              <line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/>
            </svg>
            Create
          </button>
        </div>

        <!-- Empty -->
        <div v-if="typeConnections.length === 0" class="db-drawer-empty">
          <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1" opacity="0.25">
            <ellipse cx="12" cy="6" rx="8" ry="3"/><path d="M4 6v6c0 1.66 3.58 3 8 3s8-1.34 8-3V6"/><path d="M4 12v6c0 1.66 3.58 3 8 3s8-1.34 8-3v-6"/>
          </svg>
          <p>暂无连接</p>
          <button class="db-btn-primary" @click="openAddConnModal">Create Now</button>
        </div>

        <!-- Connection List -->
        <div v-else class="db-conn-list">
          <div v-for="conn in typeConnections" :key="conn.id" class="db-conn-card">
            <div class="db-conn-card-header">
              <span class="db-conn-name">
                {{ conn.params?.database || getFileName(conn.params?.path || conn.params?.db_path) || conn.description || '未命名' }}
              </span>
              <div class="db-conn-card-actions">
                <button class="db-icon-btn" title="刷新" @click="onRefresh(conn)">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="23 4 23 10 17 10"/><path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"/></svg>
                </button>
                <button class="db-icon-btn db-icon-edit" title="编辑" @click="editConnection(conn)">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 1 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>
                </button>
                <button class="db-icon-btn db-icon-delete" title="删除" @click="deleteConn(conn)">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"/><path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6"/><line x1="10" y1="11" x2="10" y2="17"/><line x1="14" y1="11" x2="14" y2="17"/></svg>
                </button>
              </div>
            </div>
            <div class="db-conn-card-info">
              <p v-if="conn.params?.host">host: {{ conn.params.host }}</p>
              <p v-if="conn.params?.port">port: {{ conn.params.port }}</p>
              <p v-if="conn.params?.path">path: {{ getFileName(conn.params.path) }}</p>
              <p v-if="conn.params?.user">user: {{ conn.params.user }}</p>
              <p v-if="conn.params?.database">database: {{ conn.params.database }}</p>
              <p v-if="conn.params?.schema">schema: {{ conn.params.schema }}</p>
            </div>
            <p class="db-conn-card-desc" v-if="conn.description">
              {{ $t('description') || '描述' }}: {{ conn.description }}
            </p>
          </div>
        </div>
      </div>
    </div>

    <!-- Form Modal -->
    <div class="db-modal-overlay" v-if="formVisible" @click.self="closeForm">
      <div class="db-modal">
        <h3 class="db-modal-title">
          {{ editingConnection ? ($t('edit_database') || '编辑连接') : ($t('add_database') || '添加连接') }}
        </h3>

        <!-- 连接类型选择（新增时） -->
        <div class="db-form-group" v-if="!editingConnection && formConnectorTypes.length > 0">
          <label>{{ $t('database_type') || '数据库类型' }} <span class="req">*</span></label>
          <select v-model="form.type" @change="onTypeChange" class="db-form-select">
            <option v-for="t in formConnectorTypes" :key="t.value" :value="t.value" :disabled="t.disabled">
              {{ t.label }}
            </option>
          </select>
        </div>

        <!-- 动态参数 -->
        <div class="db-form-group" v-for="p in formParams" :key="p.param_name">
          <label>{{ p.label || p.param_name }} <span class="req" v-if="p.required">*</span></label>
          <!-- 下拉选择 -->
          <select v-if="hasValidValues(p)" v-model="formValues[p.param_name]" class="db-form-select">
            <option v-for="v in getValidValues(p)" :key="v.key || v" :value="v.key || v">
              {{ v.label || v }}
            </option>
          </select>
          <!-- 密码 -->
          <input
            v-else-if="isPrivacy(p)"
            type="password"
            v-model="formValues[p.param_name]"
            class="db-form-input"
            autocomplete="new-password"
            placeholder="请输入密码"
          />
          <!-- 数字 -->
          <input
            v-else-if="isNumber(p)"
            type="number"
            v-model.number="formValues[p.param_name]"
            class="db-form-input"
          />
          <!-- 布尔 -->
          <label v-else-if="isBool(p)" class="db-form-checkbox">
            <input type="checkbox" v-model="formValues[p.param_name]" />
            <span>{{ p.label || p.param_name }}</span>
          </label>
          <!-- 文本 -->
          <input v-else type="text" v-model="formValues[p.param_name]" class="db-form-input" />
        </div>

        <!-- 描述 -->
        <div class="db-form-group">
          <label>{{ $t('description') || '描述' }}</label>
          <textarea v-model="form.description" rows="3" class="db-form-textarea" :placeholder="$t('input_description') || '简要描述'" />
        </div>

        <div v-if="formError" class="db-form-error">{{ formError }}</div>

        <div class="db-modal-actions">
          <button class="db-btn-cancel" @click="closeForm">{{ $t('cancel') || '取消' }}</button>
          <button class="db-btn-primary" @click="submitForm" :disabled="submitting">
            {{ submitting ? '提交中...' : ($t('submit') || '提交') }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import {
  fetchConnectorTypes,
  fetchDatabaseConnections,
  createDatabaseConnection,
  updateDatabaseConnection,
  deleteDatabaseConnection,
  refreshDatabaseConnection,
  type ConnectorType,
  type DatabaseConnection,
} from '@/api/data'

// ── DB-GPT dbMapper (exact copy from DB-GPT constants.ts) ──
const dbMapper: Record<string, { label: string; icon: string; desc: string }> = {
  mysql      : { label: 'MySQL',       icon: '/icons/db/mysql.png',      desc: 'Fast, reliable, scalable open-source relational database management system.' },
  oceanbase  : { label: 'OceanBase',    icon: '/icons/db/oceanbase.png',  desc: 'An Ultra-Fast & Cost-Effective Distributed SQL Database.' },
  mssql      : { label: 'MSSQL',       icon: '/icons/db/mssql.png',      desc: 'Powerful, scalable, secure relational database system by Microsoft.' },
  duckdb     : { label: 'DuckDB',      icon: '/icons/db/duckdb.png',     desc: 'In-memory analytical database with efficient query processing.' },
  sqlite     : { label: 'Sqlite',      icon: '/icons/db/sqlite.png',     desc: 'Lightweight embedded relational database with simplicity and portability.' },
  clickhouse : { label: 'ClickHouse',  icon: '/icons/db/clickhouse.png', desc: 'Columnar database for high-performance analytics and real-time queries.' },
  oracle     : { label: 'Oracle',      icon: '/icons/db/oracle.png',     desc: 'Robust, scalable, secure relational database widely used in enterprises.' },
  access     : { label: 'Access',      icon: '/icons/db/access.png',     desc: 'Easy-to-use relational database for small-scale applications by Microsoft.' },
  mongodb    : { label: 'MongoDB',     icon: '/icons/db/mongodb.png',    desc: 'Flexible, scalable NoSQL document database for web and mobile apps.' },
  doris      : { label: 'ApacheDoris', icon: '/icons/db/doris.png',      desc: 'A new-generation open-source real-time data warehouse.' },
  starrocks  : { label: 'StarRocks',   icon: '/icons/db/starrocks.png',  desc: 'An Open-Source, High-Performance Analytical Database.' },
  db2        : { label: 'DB2',         icon: '/icons/db/db2.png',        desc: 'Scalable, secure relational database system developed by IBM.' },
  hbase      : { label: 'HBase',       icon: '/icons/db/hbase.png',      desc: 'Distributed, scalable NoSQL database for large structured/semi-structured data.' },
  redis      : { label: 'Redis',       icon: '/icons/db/redis.png',      desc: 'Fast, versatile in-memory data structure store as cache, DB, or broker.' },
  cassandra  : { label: 'Cassandra',   icon: '/icons/db/cassandra.png',  desc: 'Scalable, fault-tolerant distributed NoSQL database for large data.' },
  couchbase  : { label: 'Couchbase',   icon: '/icons/db/couchbase.png',  desc: 'High-performance NoSQL document database with distributed architecture.' },
  omc        : { label: 'Omc',         icon: '/icons/db/odc.png',        desc: 'Omc meta data.' },
  postgresql : { label: 'PostgreSQL',  icon: '/icons/db/postgresql.png', desc: 'Powerful open-source relational database with extensibility and SQL standards.' },
  gaussdb    : { label: 'GaussDB',     icon: '/icons/db/gaussdb.png',    desc: "Huawei's distributed database with PostgreSQL compatibility" },
  openGauss  : { label: 'openGauss',   icon: '/icons/db/opengauss.png',  desc: 'Open-source relational database with PostgreSQL compatibility.' },
  vertica    : { label: 'Vertica',     icon: '/icons/db/vertica.png',    desc: 'Vertica is a strongly consistent, ACID-compliant, SQL data warehouse, built for the scale and complexity of today\'s data-driven world.' },
  spark      : { label: 'Spark',       icon: '/icons/db/spark.png',      desc: 'Unified engine for large-scale data analytics.' },
  hive       : { label: 'Hive',        icon: '/icons/db/hive.png',       desc: 'A distributed fault-tolerant data warehouse system.' },
  space      : { label: 'Space',       icon: '/icons/db/knowledge.png',  desc: 'knowledge analytics.' },
  tugraph    : { label: 'TuGraph',     icon: '/icons/db/tugraph.png',    desc: 'TuGraph is a high-performance graph database jointly developed by Ant Group and Tsinghua University.' },
  neo4j      : { label: 'Neo4j',       icon: '/icons/db/neo4j.png',      desc: 'Neo4j is a highly scalable native graph database, purpose-built to leverage data relationships.' },
}

// ── State ──
const loading = ref(true)
const connectorTypes = ref<ConnectorType[]>([])
const connections = ref<DatabaseConnection[]>([])

const drawerVisible = ref(false)
const selectedType = ref<ConnectorType | null>(null)

const formVisible = ref(false)
const editingConnection = ref<DatabaseConnection | null>(null)
const submitting = ref(false)
const formError = ref('')

const form = ref({
  type: '',
  description: '',
})
const formValues = ref<Record<string, any>>({})
const formParams = ref<any[]>([])

// ── Computed ──
const typeConnections = computed(() => {
  if (!selectedType.value) return []
  return connections.value.filter(
    (c) => (c.type || '').toLowerCase() === (selectedType.value?.name || '').toLowerCase()
  )
})

const formConnectorTypes = computed(() => {
  const supported = connectorTypes.value
    .filter(ct => dbMapper[ct.name])
    .map(ct => ({
      value: ct.name,
      label: dbMapper[ct.name]?.label || ct.label || ct.name,
      disabled: false,
      parameters: ct.parameters,
    }))
  const unsupported = Object.keys(dbMapper)
    .filter(k => !supported.some(s => s.value === k))
    .map(k => ({ value: k, label: dbMapper[k].label, disabled: true, parameters: [] }))
  return [...supported, ...unsupported]
})

// ── Helpers ──
function getIcon(name: string): string {
  return dbMapper[name]?.icon || `/icons/db/${name}.png`
}
function getDesc(name: string): string {
  return dbMapper[name]?.desc || ''
}
function getCount(name: string): number {
  return connections.value.filter(
    (c) => (c.type || '').toLowerCase() === name.toLowerCase()
  ).length
}
function isDisabled(ct: ConnectorType): boolean {
  return !dbMapper[ct.name]
}
function getFileName(path: string): string {
  if (!path) return ''
  const parts = path.split(/[/\\]/)
  return parts[parts.length - 1]
}

// Form param helpers
function hasValidValues(p: any): boolean {
  return Array.isArray(p.valid_values) && p.valid_values.length > 0
}
function getValidValues(p: any): any[] {
  if (!p.valid_values?.length) return []
  if (typeof p.valid_values[0] === 'object' && 'key' in p.valid_values[0]) {
    return p.valid_values
  }
  return p.valid_values.map((v: string) => ({ key: v, label: v }))
}
function isPrivacy(p: any): boolean {
  return p.ext_metadata?.tags?.includes?.('privacy') || p.param_name?.toLowerCase().includes('password') || p.param_name?.toLowerCase().includes('pwd')
}
function isNumber(p: any): boolean {
  const t = (p.param_type || '').toLowerCase()
  return ['int', 'integer', 'number', 'float'].includes(t)
}
function isBool(p: any): boolean {
  return (p.param_type || '').toLowerCase() === 'bool' || (p.param_type || '').toLowerCase() === 'boolean'
}
function onImgError(e: Event) {
  const img = e.target as HTMLImageElement
  img.style.display = 'none'
}

// ── Data Loading ──
async function loadData() {
  loading.value = true
  try {
    const [types, conns] = await Promise.all([
      fetchConnectorTypes(),
      fetchDatabaseConnections(),
    ])
    // DB-GPT returns: { success: true, data: { types: [...] } }
    // Our API unwraps to types array
    connectorTypes.value = Array.isArray(types) ? types : []
    connections.value = Array.isArray(conns) ? conns : (conns as any)?.data ?? []
  } catch (e) {
    console.error('Failed to load data sources', e)
  } finally {
    loading.value = false
  }
}

async function refreshConnections() {
  try {
    const conns = await fetchDatabaseConnections()
    connections.value = Array.isArray(conns) ? conns : (conns as any)?.data ?? []
  } catch (e) {
    console.error('Failed to refresh connections', e)
  }
}

// ── Card / Drawer ──
function onCardClick(ct: ConnectorType) {
  if (isDisabled(ct)) return
  selectedType.value = ct
  drawerVisible.value = true
}
function closeDrawer() {
  drawerVisible.value = false
  selectedType.value = null
}

// ── Form ──
function openAddModal() {
  editingConnection.value = null
  formError.value = ''
  form.value = { type: connectorTypes.value[0]?.name || '', description: '' }
  formValues.value = {}
  formParams.value = connectorTypes.value[0]?.parameters || []
  formVisible.value = true
}

function openAddConnModal() {
  editingConnection.value = null
  formError.value = ''
  form.value = { type: selectedType.value?.name || '', description: '' }
  formValues.value = {}
  formParams.value = selectedType.value?.parameters || []
  formVisible.value = true
}

function onTypeChange() {
  const ct = formConnectorTypes.value.find(t => t.value === form.value.type)
  formParams.value = ct?.parameters || []
  formValues.value = {}
  // 设置默认值
  for (const p of formParams.value) {
    if (p.default_value !== undefined && p.default_value !== null) {
      formValues.value[p.param_name] = p.default_value
    }
  }
}

function editConnection(conn: DatabaseConnection) {
  editingConnection.value = conn
  formError.value = ''
  form.value = {
    type: conn.type,
    description: conn.description || '',
  }
  formValues.value = { ...(conn.params || {}) }
  formParams.value = selectedType.value?.parameters || []

  // 回填 formParams 的 default_value
  if (conn.params) {
    for (const p of formParams.value) {
      if (conn.params[p.param_name] !== undefined) {
        formValues.value[p.param_name] = conn.params[p.param_name]
      }
    }
  }

  formVisible.value = true
}

function closeForm() {
  formVisible.value = false
  editingConnection.value = null
  formError.value = ''
  formValues.value = {}
  formParams.value = []
}

async function submitForm() {
  formError.value = ''

  // 合并 type 和 params
  const params: Record<string, any> = {
    db_type: form.value.type,
    ...formValues.value,
  }
  if (form.value.description) {
    params.comment = form.value.description
  }

  if (editingConnection.value) {
    params.id = editingConnection.value.id
  }

  submitting.value = true
  try {
    if (editingConnection.value) {
      await updateDatabaseConnection(params)
    } else {
      await createDatabaseConnection(params)
    }
    closeForm()
    await refreshConnections()
  } catch (e: any) {
    formError.value = '操作失败: ' + (e?.response?.data?.err_msg || e?.message || '未知错误')
  } finally {
    submitting.value = false
  }
}

// ── Connection Actions ──
async function onRefresh(conn: DatabaseConnection) {
  try {
    await refreshDatabaseConnection(conn.id)
    await refreshConnections()
    alert('刷新成功')
  } catch (e: any) {
    alert('刷新失败: ' + (e?.response?.data?.err_msg || e?.message || ''))
  }
}

async function deleteConn(conn: DatabaseConnection) {
  const name = conn.description || conn.params?.database || conn.params?.db_name || conn.id
  if (!confirm(`确定删除连接「${name}」？`)) return
  try {
    await deleteDatabaseConnection(conn.id)
    await refreshConnections()
  } catch (e: any) {
    alert('删除失败: ' + (e?.response?.data?.err_msg || e?.message || ''))
  }
}

// ── Init ──
onMounted(() => loadData())
</script>

<style scoped>
/* ── Page ── */
.db-page {
  padding: 24px 28px;
  max-width: 1100px;
  margin: 0 auto;
  min-height: 90vh;
  overflow-y: auto;
}

/* ── Header ── */
.db-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}
.db-title {
  margin: 0;
  font-size: 20px;
  font-weight: 700;
  color: #1f2937;
}

/* gradient button matching DB-GPT */
.db-btn-add {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 20px;
  border: none;
  border-radius: 8px;
  background: linear-gradient(135deg, #1677ff, #0958d9);
  color: #fff;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: opacity 0.15s;
}
.db-btn-add:hover { opacity: 0.9; }

/* ── Loading ── */
.db-loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 100px 0;
  color: #9ca3af;
  font-size: 14px;
  gap: 12px;
}
.db-spinner {
  width: 32px; height: 32px;
  border: 3px solid #e5e7eb;
  border-top-color: #1677ff;
  border-radius: 50%;
  animation: spin 0.7s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }

/* ── Card Grid ── */
.db-grid {
  display: flex;
  flex-wrap: wrap;
  margin: 0 -8px;
  gap: 8px;
}
@media (min-width: 768px) {
  .db-grid { gap: 16px; }
}

.db-card {
  position: relative;
  width: 288px;
  border-radius: 12px;
  background: #fff;
  box-shadow: 0 8px 16px -10px rgba(100,100,100,0.08);
  cursor: pointer;
  transition: transform 0.3s, box-shadow 0.3s;
  display: flex;
  flex-direction: column;
  min-height: fit-content;
}
.db-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 14px 20px -10px rgba(100,100,100,0.15);
}
.db-card-disabled {
  filter: grayscale(1);
  cursor: not-allowed;
}

.db-card-top {
  position: relative;
  padding: 16px 16px 0 16px;
}
.db-card-badge {
  position: absolute;
  top: 8px;
  right: 8px;
  min-width: 20px;
  height: 20px;
  line-height: 20px;
  padding: 0 6px;
  border-radius: 10px;
  background: #ff4d4f;
  color: #fff;
  font-size: 12px;
  font-weight: 500;
  text-align: center;
}

.db-card-icon {
  width: 44px;
  height: 44px;
  border-radius: 50%;
  object-fit: contain;
  background: #fff;
  border: 1px solid #e5e7eb;
  flex-shrink: 0;
}
.db-card-body {
  padding: 12px 16px 16px 16px;
  display: flex;
  flex-direction: column;
  flex: 1;
}
.db-card-title {
  margin: 0 0 6px 0;
  font-size: 14px;
  font-weight: 600;
  color: #1f2937;
  line-height: 1.3;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.db-card-desc {
  margin: 0;
  font-size: 13px;
  color: #9ca3af;
  line-height: 1.45;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

/* ── Drawer ── */
.db-drawer-overlay {
  position: fixed; inset: 0;
  background: rgba(0,0,0,0.3);
  z-index: 90;
}
.db-drawer {
  position: fixed;
  top: 0; right: 0;
  width: 420px;
  max-width: 90vw;
  height: 100vh;
  background: #fff;
  box-shadow: -4px 0 24px rgba(0,0,0,0.1);
  z-index: 100;
  display: flex;
  flex-direction: column;
  transform: translateX(100%);
  transition: transform 0.25s ease;
}
.db-drawer.open { transform: translateX(0); }

.db-drawer-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 18px 24px;
  border-bottom: 1px solid #e5e7eb;
}
.db-drawer-title {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 10px;
}
.db-drawer-title-icon {
  width: 28px; height: 28px;
  border-radius: 6px;
  object-fit: contain;
  border: 1px solid #e5e7eb;
}
.db-drawer-close {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 30px; height: 30px;
  border: none;
  border-radius: 6px;
  background: transparent;
  font-size: 20px;
  color: #6b7280;
  cursor: pointer;
  transition: background 0.15s;
}
.db-drawer-close:hover { background: #f3f4f6; }

.db-drawer-body {
  flex: 1;
  overflow-y: auto;
  padding: 16px 24px;
}

.db-drawer-actions {
  margin-bottom: 16px;
}

.db-drawer-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 60px 0;
  color: #9ca3af;
  font-size: 14px;
  gap: 16px;
}

/* Connection list */
.db-conn-list {
  display: flex;
  flex-direction: column;
  gap: 14px;
}
.db-conn-card {
  padding: 14px 16px;
  border: 1px solid #e5e7eb;
  border-radius: 10px;
  background: #fafafa;
}
.db-conn-card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
}
.db-conn-name {
  font-size: 14px;
  font-weight: 600;
  color: #1f2937;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.db-conn-card-actions {
  display: flex;
  gap: 2px;
  flex-shrink: 0;
}
.db-icon-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px; height: 28px;
  border: none;
  border-radius: 6px;
  background: transparent;
  color: #9ca3af;
  cursor: pointer;
  transition: all 0.15s;
}
.db-icon-btn:hover { background: #f3f4f6; color: #1677ff; }
.db-icon-edit:hover { color: #1b7eff; }
.db-icon-delete:hover { background: #fef2f2; color: #ff1b2e; }

.db-conn-card-info p {
  margin: 2px 0;
  font-size: 13px;
  color: #6b7280;
  font-family: monospace;
}
.db-conn-card-desc {
  margin: 6px 0 0 0;
  font-size: 13px;
  color: #9ca3af;
}

/* ── Create Button ── */
.db-btn-create {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 20px;
  border: none;
  border-radius: 8px;
  background: #1677ff;
  color: #fff;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: background 0.15s;
}
.db-btn-create:hover { background: #0958d9; }

/* ── Modal ── */
.db-modal-overlay {
  position: fixed; inset: 0;
  background: rgba(0,0,0,0.4);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 200;
}
.db-modal {
  background: #fff;
  border-radius: 14px;
  padding: 28px;
  width: 600px;
  max-width: 94vw;
  max-height: 85vh;
  overflow-y: auto;
  box-shadow: 0 8px 32px rgba(0,0,0,0.12);
}
.db-modal-title {
  margin: 0 0 20px 0;
  font-size: 17px;
  font-weight: 600;
  color: #1f2937;
}

.db-form-group {
  margin-bottom: 16px;
}
.db-form-group label {
  display: block;
  font-size: 13px;
  font-weight: 500;
  margin-bottom: 5px;
  color: #374151;
}
.db-form-group label .req { color: #dc2626; }
.db-form-input,
.db-form-select,
.db-form-textarea {
  width: 100%;
  padding: 9px 12px;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  font-size: 14px;
  outline: none;
  box-sizing: border-box;
  transition: border-color 0.15s;
  font-family: inherit;
}
.db-form-input:focus,
.db-form-select:focus,
.db-form-textarea:focus { border-color: #1677ff; }
.db-form-select { background: #fff; cursor: pointer; }
.db-form-checkbox {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  font-size: 14px;
}
.db-form-checkbox input { accent-color: #1677ff; }
.db-form-error {
  padding: 10px 14px;
  border-radius: 8px;
  background: #fef2f2;
  color: #dc2626;
  font-size: 13px;
  margin-bottom: 14px;
}

.db-modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  margin-top: 20px;
}

/* ── Shared Buttons ── */
.db-btn-primary {
  padding: 9px 22px;
  border: none;
  border-radius: 8px;
  background: #1677ff;
  color: #fff;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: background 0.15s;
}
.db-btn-primary:hover { background: #0958d9; }
.db-btn-primary:disabled { opacity: 0.5; cursor: not-allowed; }
.db-btn-cancel {
  padding: 9px 18px;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  background: #fff;
  color: #374151;
  font-size: 14px;
  cursor: pointer;
  transition: background 0.15s;
}
.db-btn-cancel:hover { background: #f3f4f6; }
</style>
