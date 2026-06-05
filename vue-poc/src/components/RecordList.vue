<template>
  <div class="record-list">
    <div class="panel-title">{{ tableTitle }} ({{ totalCount }})</div>
    <div class="tree-body">
      <el-tree
        ref="treeRef"
        :data="treeData"
        :props="{ children: 'children', label: 'label' }"
        node-key="id"
        highlight-current
        :expand-on-click-node="false"
        @node-click="onNodeClick"
        empty-text="无记录"
        size="small"
      >
        <template #default="{ node, data }">
          <span class="tree-node" :class="{ 'is-record': !!data.record }">
            <span v-if="!data.record" class="group-icon">&#9679;</span>
            <span v-else class="leaf-icon">&#9670;</span>
            <span class="node-label">{{ data.label }}</span>
            <span v-if="!data.record && data.children" class="node-count">({{ data.children.length }})</span>
          </span>
        </template>
      </el-tree>
      <div v-if="treeData.length === 0" class="empty-hint">无记录</div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, computed } from 'vue'
import axios from 'axios'

const props = defineProps({
  tableId: { type: String, default: '' },
  records: { type: Array, default: () => [] }
})

const emit = defineEmits(['select', 'group-filter'])

const treeRef = ref(null)
const treeData = ref([])
const tableTitle = ref('记录一览')
const treeField = ref('')

const fetchTableTitle = async () => {
  if (!props.tableId) { tableTitle.value = '记录一览'; return }
  try {
    const res = await axios.get(`/api/meta/${props.tableId}`)
    tableTitle.value = res.data.table?.usTitle || res.data.table?.jpTitle || props.tableId
  } catch (e) {
    tableTitle.value = props.tableId
  }
}

const totalCount = computed(() => {
  let count = 0
  const walk = (nodes) => {
    for (const n of nodes) {
      if (n.record) count++
      if (n.children) walk(n.children)
    }
  }
  walk(treeData.value)
  return count
})

const fetchTree = async () => {
  if (!props.tableId) { treeData.value = []; return }
  try {
    const res = await axios.get(`/api/meta/${props.tableId}/tree?status=ALL`)
    treeData.value = res.data.tree || []
    treeField.value = res.data.treeField || ''
  } catch (e) {
    console.error('fetchTree failed:', e)
    treeData.value = []
  }
}

const onNodeClick = (data) => {
  if (data.record) {
    // Leaf click: filter center table by record key values
    emit('select', data.record)
    emit('group-filter', { field: '', value: '', record: data.record })
  } else if (treeField.value) {
    // Group click: filter center table by group value
    emit('group-filter', { field: treeField.value, value: data.label })
  }
}

// Reload tree when table changes
watch(() => props.tableId, () => { fetchTableTitle(); fetchTree(); }, { immediate: true })

// Also reload when records change (after save/delete etc.)
watch(() => props.records, () => {
  // Refresh tree data when records prop changes
  fetchTree()
})
</script>

<style scoped>
.record-list { font-size: 12px; }
.panel-title { font-weight: 700; padding: 0 12px; height: 28px; line-height: 28px; border-bottom: 2px solid var(--c-primary, #2B5CE6); color: var(--c-text, #1A2233); font-size: 11px; text-transform: uppercase; letter-spacing: 0.3px; background: var(--c-border-light, #E2E6EC); }
.tree-body { padding: 2px 0; }
.tree-node { display: flex; align-items: center; gap: 4px; font-size: 12px; }
.group-icon { color: var(--c-primary, #2B5CE6); font-size: 10px; flex-shrink: 0; }
.leaf-icon { color: var(--c-text-secondary, #5C6B7A); font-size: 8px; flex-shrink: 0; }
.node-label { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; color: var(--c-text, #1A2233); }
.node-count { color: var(--c-text-secondary, #5C6B7A); font-size: 10px; flex-shrink: 0; }
.tree-node.is-record { cursor: pointer; }
.empty-hint { color: var(--c-text-secondary, #5C6B7A); text-align: center; padding: 30px 0; font-size: 12px; }
:deep(.el-tree) { background: transparent; border-radius: 0; }
:deep(.el-tree-node__expand-icon) { font-size: 12px; color: #999; }
:deep(.el-tree-node__content) { height: 26px; border-radius: 0; }
:deep(.el-tree-node__content:hover) { background: var(--c-row-selected, #E8EDF5); }
:deep(.el-tree-node.is-current > .el-tree-node__content) { background: var(--c-row-selected, #E8EDF5); color: var(--c-primary, #2B5CE6); font-weight: 600; border-left: 3px solid var(--c-primary, #2B5CE6); }
</style>
