<template>
  <div class="sql-editor" :class="{ focused: isFocused }">
    <div class="sql-editor-header">
      <span class="sql-label">SQL</span>
      <div class="sql-actions">
        <button class="btn-action" @click="$emit('format')" title="格式化">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="4 7 4 4 20 4 20 7"/><line x1="9" y1="20" x2="15" y2="20"/><line x1="12" y1="4" x2="12" y2="20"/></svg>
        </button>
        <button class="btn-action" @click="$emit('copy')" title="复制">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="9" y="9" width="13" height="13" rx="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>
        </button>
      </div>
    </div>
    <textarea
      ref="textareaRef"
      v-model="localValue"
      class="sql-textarea"
      :placeholder="placeholder"
      :readonly="readonly"
      spellcheck="false"
      @focus="isFocused = true"
      @blur="isFocused = false"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'

const props = withDefaults(defineProps<{
  modelValue: string
  placeholder?: string
  readonly?: boolean
}>(), {
  placeholder: '输入 SQL 查询...',
  readonly: false,
})

const emit = defineEmits<{
  'update:modelValue': [value: string]
  format: []
  copy: []
}>()

const textareaRef = ref<HTMLTextAreaElement>()
const isFocused = ref(false)

const localValue = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val),
})

// Tab 键插入 2 空格
function handleKeydown(e: KeyboardEvent) {
  if (e.key === 'Tab') {
    e.preventDefault()
    const ta = textareaRef.value
    if (!ta) return
    const start = ta.selectionStart
    const end = ta.selectionEnd
    const before = localValue.value.slice(0, start)
    const after = localValue.value.slice(end)
    emit('update:modelValue', before + '  ' + after)
    requestAnimationFrame(() => {
      ta.selectionStart = ta.selectionEnd = start + 2
    })
  }
}

// Expose
defineExpose({ textareaRef })
</script>

<style scoped>
.sql-editor {
  border: 1px solid var(--color-border, #d9d9d9);
  border-radius: 8px;
  overflow: hidden;
  background: var(--color-bg-container, #fafafa);
  transition: border-color 0.2s;
}
.sql-editor.focused {
  border-color: var(--color-primary, #1677ff);
}
.sql-editor-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 6px 12px;
  background: var(--color-bg-elevated, #f5f5f5);
  border-bottom: 1px solid var(--color-border, #d9d9d9);
}
.sql-label {
  font-size: 11px;
  font-weight: 600;
  color: var(--color-text-tertiary, #999);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}
.sql-actions {
  display: flex;
  gap: 4px;
}
.btn-action {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border: none;
  border-radius: 4px;
  background: transparent;
  color: var(--color-text-tertiary, #999);
  cursor: pointer;
  transition: all 0.15s;
}
.btn-action:hover {
  background: var(--color-fill, #e8e8e8);
  color: var(--color-text, #333);
}
.sql-textarea {
  width: 100%;
  min-height: 80px;
  max-height: 300px;
  padding: 12px;
  border: none;
  outline: none;
  resize: vertical;
  font-family: 'SF Mono', 'Fira Code', 'Cascadia Code', monospace;
  font-size: 13px;
  line-height: 1.6;
  color: var(--color-text, #1a1a2e);
  background: var(--color-bg-container, #fff);
  tab-size: 2;
}
.sql-textarea:read-only {
  background: var(--color-bg-elevated, #f9f9f9);
  cursor: default;
}
</style>
