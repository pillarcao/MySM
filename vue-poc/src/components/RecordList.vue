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
.record-list { font-size: 12px; }
.panel-title { font-weight: 600; padding: 0 12px; height: 30px; line-height: 30px; border-bottom: 1px solid #e8e8e8; color: #333; }
.list-body { padding: 2px 0; }
.list-item {
  padding: 5px 12px; cursor: pointer; border-bottom: 1px solid #f0f0f0;
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis; transition: background .15s;
}
.list-item:hover { background: #e6f7ff; }
.list-item.active { background: #bae7ff; color: #1890ff; font-weight: 500; }
.item-text { color: #555; }
.empty-hint { color: #bbb; text-align: center; padding: 30px 0; font-size: 12px; }
</style>
