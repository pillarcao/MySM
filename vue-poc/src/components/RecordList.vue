<template>
  <div class="record-list">
    <div class="panel-title">记录一览 ({{ records.length }})</div>
    <div class="list-body">
      <div
        v-for="(rec, idx) in records"
        :key="idx"
        class="list-item"
        :class="{ active: idx === selectedIdx }"
        @click="onClick(rec, idx)"
      >
        <span class="item-text">{{ formatKey(rec) }}</span>
      </div>
      <div v-if="records.length === 0" class="empty-hint">无记录</div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const props = defineProps({
  tableId: { type: String, default: '' },
  records: { type: Array, default: () => [] }
})

const emit = defineEmits(['select'])
const selectedIdx = ref(-1)

const formatKey = (rec) => {
  // 显示前两个 key 字段的值
  const vals = Object.values(rec).slice(0, 2)
  return vals.map(v => typeof v === 'string' ? v.trim() : v).join(' / ')
}

const onClick = (rec, idx) => {
  selectedIdx.value = idx
  emit('select', rec)
}
</script>

<style scoped>
.record-list { font-size: 13px; }
.panel-title { font-weight: bold; padding: 8px; border-bottom: 1px solid #e8e8e8; }
.list-body { padding: 4px 0; }
.list-item {
  padding: 4px 8px; cursor: pointer; border-bottom: 1px solid #f5f5f5;
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}
.list-item:hover { background: #e6f7ff; }
.list-item.active { background: #bae7ff; }
.item-text { color: #333; }
.empty-hint { color: #999; text-align: center; padding: 20px; }
</style>
