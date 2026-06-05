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
    <!-- Route-specific actions (only for BROUTE table) -->
    <template v-if="tableId === 'TBLID_BROUTE'">
      <div class="ctx-divider"></div>
      <div class="ctx-item" :class="{ disabled: disabled.routeCopy }" @click="emit('action', 'routeCopy')"><el-icon><CopyDocument /></el-icon> Copy All Objects in Route</div>
      <div class="ctx-item" :class="{ disabled: disabled.routeVerUp }" @click="emit('action', 'routeVerUp')"><el-icon><Top /></el-icon> Revise Version All Objects</div>
      <div class="ctx-item" :class="{ disabled: disabled.routeRelease }" @click="emit('action', 'routeRelease')"><el-icon><Promotion /></el-icon> Release All Objects In Route</div>
    </template>
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
  CircleClose, CopyDocument, Document, Search, Refresh, Unlock, Top
} from '@element-plus/icons-vue'

defineProps({
  visible: { type: Boolean, default: false },
  x: { type: Number, default: 0 },
  y: { type: Number, default: 0 },
  col: { type: Object, default: null },
  tableId: { type: String, default: '' },
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
      hideCol: true,
      routeCopy: true,
      routeVerUp: true,
      routeRelease: true
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
  // Delay listener registration to avoid right-click event closing the menu immediately
  setTimeout(() => {
    document.addEventListener('click', onDocumentClick)
  }, 0)
  document.addEventListener('keydown', onDocumentKeydown)
})

onUnmounted(() => {
  document.removeEventListener('click', onDocumentClick)
  document.removeEventListener('keydown', onDocumentKeydown)
})
</script>

<style scoped>
.ctx-menu { position: fixed; z-index: 9999; background: #fff; border: 1px solid var(--c-border, #D0D5DC); border-radius: 0; box-shadow: 2px 2px 8px rgba(13,27,42,.15); padding: 2px 0; min-width: 200px; font-size: 12px; }
.ctx-item { display: flex; align-items: center; gap: 8px; padding: 5px 12px; cursor: pointer; color: var(--c-text, #1A2233); }
.ctx-item:hover { background: var(--c-row-selected, #E8EDF5); color: var(--c-primary, #2B5CE6); }
.ctx-item.disabled { color: #bbb; cursor: default; pointer-events: none; }
.ctx-item .el-icon { font-size: 13px; }
.ctx-divider { height: 1px; background: var(--c-border-light, #E2E6EC); margin: 2px 0; }
</style>
