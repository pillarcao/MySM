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
            <el-icon v-if="!data.record" class="group-icon"><ArrowRight /></el-icon>
            <el-icon v-else class="leaf-icon"><CircleCheck /></el-icon>
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
import { ArrowRight, CircleCheck } from '@element-plus/icons-vue'

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
.panel-title { font-weight: 600; padding: 0 12px; height: 30px; line-height: 30px; border-bottom: 1px solid #e8e8e8; color: #333; }
.tree-body { padding: 4px 0; }
.tree-node { display: flex; align-items: center; gap: 4px; font-size: 12px; }
.group-icon { color: #e6a23c; font-size: 14px; flex-shrink: 0; }
.leaf-icon { color: #409eff; font-size: 14px; flex-shrink: 0; }
.node-label { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.node-count { color: #999; font-size: 11px; flex-shrink: 0; }
.tree-node.is-record { cursor: pointer; }
.empty-hint { color: #bbb; text-align: center; padding: 30px 0; font-size: 12px; }
:deep(.el-tree) { background: transparent; }
:deep(.el-tree-node__content) { height: 28px; }
:deep(.el-tree-node__content:hover) { background: #e6f7ff; }
:deep(.el-tree-node.is-current > .el-tree-node__content) { background: #bae7ff; color: #1890ff; font-weight: 500; }
</style>
