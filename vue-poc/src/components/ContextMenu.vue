<template>
  <div v-if="visible" class="ctx-menu" :style="{ left: x + 'px', top: y + 'px' }" @click.stop @mouseleave="emit('close')">
    <div class="ctx-item" @click="emit('action', 'add')"><el-icon><Plus /></el-icon> New</div>
    <div class="ctx-item" :class="{ disabled: disabled.hasSelection === false }" @click="emit('action', 'update')"><el-icon><Edit /></el-icon> Edit</div>
    <div class="ctx-item" :class="{ disabled: disabled.isEditMode === false }" @click="emit('action', 'save')"><el-icon><Check /></el-icon> Save</div>
    <div class="ctx-divider"></div>
    <div class="ctx-item" :class="{ disabled: disabled.canEditComp === false }" @click="emit('action', 'editcomp')"><el-icon><Finished /></el-icon> Edit Comp</div>
    <div class="ctx-item" :class="{ disabled: disabled.canRelease === false }" @click="emit('action', 'release')"><el-icon><Promotion /></el-icon> Release</div>
    <div class="ctx-divider"></div>
    <div class="ctx-item" @click="emit('action', 'undo')"><el-icon><RefreshLeft /></el-icon> Undo</div>
    <div class="ctx-divider"></div>
    <div class="ctx-item" :class="{ disabled: disabled.cannotClear }" @click="emit('action', 'clear')">Clear</div>
    <div class="ctx-item" :class="{ disabled: disabled.cannotCopy }" @click="emit('action', 'copy')">Copy</div>
    <div class="ctx-item" :class="{ disabled: disabled.cannotPaste }" @click="emit('action', 'paste')">Paste</div>
    <div class="ctx-item" :class="{ disabled: disabled.cannotFind }" @click="emit('action', 'find')">Find</div>
    <div class="ctx-divider"></div>
    <div class="ctx-item" :class="{ disabled: disabled.hasSelection === false }" @click="emit('action', 'delete')"><el-icon><Delete /></el-icon> Delete</div>
    <div class="ctx-divider"></div>
    <div class="ctx-item" :class="{ disabled: disabled.cannotRollback }" @click="emit('action', 'rollback')">Rollback</div>
    <div class="ctx-item" :class="{ disabled: disabled.cannotForceUnlock }" @click="emit('action', 'forceUnlock')">Force Unlock</div>
    <div class="ctx-divider"></div>
    <div class="ctx-item" :class="{ disabled: !col }" @click="emit('action', 'sort-asc')"><el-icon><SortUp /></el-icon> Sort Asc</div>
    <div class="ctx-item" :class="{ disabled: !col }" @click="emit('action', 'sort-desc')"><el-icon><SortDown /></el-icon> Sort Desc</div>
    <div class="ctx-divider"></div>
    <div class="ctx-item" :class="{ disabled: !col }" @click="emit('action', 'hide-col')"><el-icon><Hide /></el-icon> Hide Column</div>
    <div class="ctx-item" @click="emit('action', 'show-all')"><el-icon><View /></el-icon> Show All Columns</div>
  </div>
</template>

<script setup>
import { Plus, Edit, Check, Finished, Promotion, Delete, RefreshLeft, SortUp, SortDown, Hide, View } from '@element-plus/icons-vue'

const props = defineProps({
  visible: { type: Boolean, default: false },
  x: { type: Number, default: 0 },
  y: { type: Number, default: 0 },
  col: { type: Object, default: null },
  disabled: {
    type: Object,
    default: () => ({
      hasSelection: false,
      isEditMode: false,
      canEditComp: false,
      canRelease: false,
      cannotClear: true,
      cannotCopy: true,
      cannotPaste: true,
      cannotFind: true,
      cannotRollback: true,
      cannotForceUnlock: true
    })
  }
})

const emit = defineEmits(['action', 'close'])
</script>

<style scoped>
.ctx-menu { position: fixed; z-index: 9999; background: #fff; border: 1px solid #e0e0e0; border-radius: 6px; box-shadow: 0 4px 12px rgba(0,0,0,.12); padding: 4px 0; min-width: 180px; font-size: 13px; }
.ctx-item { display: flex; align-items: center; gap: 8px; padding: 6px 14px; cursor: pointer; color: #333; }
.ctx-item:hover { background: #e6f7ff; color: #1890ff; }
.ctx-item.disabled { color: #ccc; cursor: default; pointer-events: none; }
.ctx-item .el-icon { font-size: 14px; }
.ctx-divider { height: 1px; background: #f0f0f0; margin: 4px 0; }
</style>
