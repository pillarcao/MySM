<template>
  <div v-if="visible" ref="menuRef" class="ctx-menu" :style="{ left: x + 'px', top: y + 'px' }" @click.stop @mouseleave="emit('close')">
    <div class="ctx-item" @click="emit('action', 'add')"><el-icon><Plus /></el-icon> New</div>
    <div class="ctx-item" :class="{ disabled: disabled.edit }" @click="emit('action', 'update')"><el-icon><Edit /></el-icon> Edit</div>
    <div class="ctx-item" :class="{ disabled: disabled.save }" @click="emit('action', 'save')"><el-icon><Check /></el-icon> Save</div>
    <div class="ctx-divider"></div>
    <div class="ctx-item" :class="{ disabled: disabled.editcomp }" @click="emit('action', 'editcomp')"><el-icon><Finished /></el-icon> Edit Comp</div>
    <div class="ctx-item" :class="{ disabled: disabled.release }" @click="emit('action', 'release')"><el-icon><Promotion /></el-icon> Release</div>
    <div class="ctx-divider"></div>
    <div class="ctx-item" @click="emit('action', 'undo')"><el-icon><RefreshLeft /></el-icon> Undo</div>
    <div class="ctx-divider"></div>
    <div class="ctx-item" :class="{ disabled: disabled.clear }" @click="emit('action', 'clear')"><el-icon><CircleClose /></el-icon> Clear</div>
    <div class="ctx-item" :class="{ disabled: disabled.copy }" @click="emit('action', 'copy')"><el-icon><CopyDocument /></el-icon> Copy</div>
    <div class="ctx-item" :class="{ disabled: disabled.paste }" @click="emit('action', 'paste')"><el-icon><Document /></el-icon> Paste</div>
    <div class="ctx-item" :class="{ disabled: disabled.find }" @click="emit('action', 'find')"><el-icon><Search /></el-icon> Find</div>
    <div class="ctx-divider"></div>
    <div class="ctx-item" :class="{ disabled: disabled.delete }" @click="emit('action', 'delete')"><el-icon><Delete /></el-icon> Delete</div>
    <div class="ctx-divider"></div>
    <div class="ctx-item" :class="{ disabled: disabled.rollback }" @click="emit('action', 'rollback')"><el-icon><Refresh /></el-icon> Rollback</div>
    <div class="ctx-item" :class="{ disabled: disabled.forceUnlock }" @click="emit('action', 'forceUnlock')"><el-icon><Unlock /></el-icon> Force Unlock</div>
    <div class="ctx-divider"></div>
    <div class="ctx-item" :class="{ disabled: disabled.sort }" @click="emit('action', 'sort-asc')"><el-icon><SortUp /></el-icon> Sort Asc</div>
    <div class="ctx-item" :class="{ disabled: disabled.sort }" @click="emit('action', 'sort-desc')"><el-icon><SortDown /></el-icon> Sort Desc</div>
    <div class="ctx-divider"></div>
    <div class="ctx-item" :class="{ disabled: disabled.hideCol }" @click="emit('action', 'hide-col')"><el-icon><Hide /></el-icon> Hide Column</div>
    <div class="ctx-item" @click="emit('action', 'show-all')"><el-icon><View /></el-icon> Show All Columns</div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import {
  Plus, Edit, Check, Finished, Promotion, Delete, RefreshLeft,
  SortUp, SortDown, Hide, View,
  CircleClose, CopyDocument, Document, Search, Refresh, Unlock
} from '@element-plus/icons-vue'

defineProps({
  visible: { type: Boolean, default: false },
  x: { type: Number, default: 0 },
  y: { type: Number, default: 0 },
  col: { type: Object, default: null },
  disabled: {
    type: Object,
    default: () => ({
      edit: true,
      save: true,
      editcomp: true,
      release: true,
      delete: true,
      clear: true,
      copy: true,
      paste: true,
      find: true,
      rollback: true,
      forceUnlock: true,
      sort: true,
      hideCol: true
    })
  }
})

const emit = defineEmits(['action', 'close'])

const menuRef = ref(null)

function onDocumentClick(e) {
  if (menuRef.value && !menuRef.value.contains(e.target)) {
    emit('close')
  }
}

function onDocumentKeydown(e) {
  if (e.key === 'Escape') {
    emit('close')
  }
}

onMounted(() => {
  document.addEventListener('click', onDocumentClick)
  document.addEventListener('keydown', onDocumentKeydown)
})

onUnmounted(() => {
  document.removeEventListener('click', onDocumentClick)
  document.removeEventListener('keydown', onDocumentKeydown)
})
</script>

<style scoped>
.ctx-menu { position: fixed; z-index: 9999; background: #fff; border: 1px solid #e0e0e0; border-radius: 6px; box-shadow: 0 4px 12px rgba(0,0,0,.12); padding: 4px 0; min-width: 180px; font-size: 13px; }
.ctx-item { display: flex; align-items: center; gap: 8px; padding: 6px 14px; cursor: pointer; color: #333; }
.ctx-item:hover { background: #e6f7ff; color: #1890ff; }
.ctx-item.disabled { color: #ccc; cursor: default; pointer-events: none; }
.ctx-item .el-icon { font-size: 14px; }
.ctx-divider { height: 1px; background: #f0f0f0; margin: 4px 0; }
</style>
