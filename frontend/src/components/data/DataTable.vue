<template>
  <div class="data-table-wrapper">
    <div class="table-toolbar">
      <span class="table-info">{{ columns.length }} 列 · {{ rows.length }} 行{{ totalRows > rows.length ? ` (共 ${totalRows})` : '' }}</span>
      <div class="table-actions">
        <button class="btn-table" @click="$emit('export-csv')" title="导出 CSV">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
          导出
        </button>
      </div>
    </div>
    <div class="table-scroll" v-if="rows.length > 0">
      <table>
        <thead>
          <tr>
            <th class="row-num">#</th>
            <th v-for="col in columns" :key="col">{{ col }}</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(row, ri) in rows" :key="ri">
            <td class="row-num">{{ ri + 1 }}</td>
            <td v-for="col in columns" :key="col" :title="formatCell(row[col])">
              <code v-if="isNumeric(row[col])">{{ formatCell(row[col]) }}</code>
              <span v-else>{{ formatCell(row[col]) }}</span>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
    <div class="table-empty" v-else>
      暂无数据
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  columns: string[]
  rows: Record<string, any>[]
  totalRows?: number
}>()

defineEmits<{
  'export-csv': []
}>()

function formatCell(val: any): string {
  if (val === null || val === undefined) return 'NULL'
  if (typeof val === 'object') return JSON.stringify(val)
  return String(val)
}

function isNumeric(val: any): boolean {
  return typeof val === 'number' || (typeof val === 'string' && !isNaN(Number(val)) && val.trim() !== '')
}
</script>

<style scoped>
.data-table-wrapper {
  border: 1px solid var(--color-border, #e5e7eb);
  border-radius: 8px;
  overflow: hidden;
  background: var(--color-bg-container, #fff);
}
.table-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  background: var(--color-bg-elevated, #f9fafb);
  border-bottom: 1px solid var(--color-border, #e5e7eb);
}
.table-info {
  font-size: 12px;
  color: var(--color-text-secondary, #6b7280);
}
.table-actions {
  display: flex;
  gap: 4px;
}
.btn-table {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 4px 10px;
  border: 1px solid var(--color-border, #d1d5db);
  border-radius: 4px;
  background: var(--color-bg-container, #fff);
  font-size: 12px;
  color: var(--color-text-secondary, #6b7280);
  cursor: pointer;
  transition: all 0.15s;
}
.btn-table:hover {
  background: var(--color-fill, #f3f4f6);
  color: var(--color-text, #111827);
}
.table-scroll {
  overflow-x: auto;
  max-height: 400px;
  overflow-y: auto;
}
table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}
thead {
  position: sticky;
  top: 0;
  z-index: 1;
}
th {
  padding: 8px 12px;
  background: var(--color-bg-elevated, #f9fafb);
  border-bottom: 2px solid var(--color-border, #e5e7eb);
  text-align: left;
  font-weight: 600;
  font-size: 12px;
  color: var(--color-text-secondary, #6b7280);
  white-space: nowrap;
}
td {
  padding: 6px 12px;
  border-bottom: 1px solid var(--color-border-light, #f3f4f6);
  max-width: 280px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
tr:hover td {
  background: var(--color-fill, #f9fafb);
}
.row-num {
  width: 40px;
  text-align: center;
  color: var(--color-text-tertiary, #9ca3af);
  font-size: 11px;
}
code {
  font-family: 'SF Mono', 'Fira Code', monospace;
  font-size: 12px;
  color: var(--color-primary, #1677ff);
}
.table-empty {
  padding: 32px;
  text-align: center;
  color: var(--color-text-tertiary, #9ca3af);
  font-size: 14px;
}
</style>
