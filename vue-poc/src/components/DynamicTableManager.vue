<template>
  <div>
    <SearchDialog
      v-model="searchDialogVisible"
      :table-id="props.tableId"
      @search="onSearchDialog"
    />

    <el-card v-loading="loading">
      <template #header>
        <div class="card-header">
          <span>{{ tableTitle }} <el-tag v-if="editingRow" type="warning" size="small">{{ isNewRow ? '新增中' : '编辑中' }}</el-tag></span>
          <el-button size="small" @click="searchDialogVisible = true">查找</el-button>
        </div>
      </template>

      <!-- 动态表格：editMode 时单元格可编辑 -->
      <el-table
        ref="tableRef"
        :data="list"
        border
        size="small"
        max-height="calc(100vh - 155px)"
        style="width: 100%; font-size: 12px;"
        :row-class-name="tableRowClassName"
        highlight-current-row
        @row-click="onRowClick"
        @row-contextmenu="onContextMenu"
      >
        <el-table-column type="index" width="50">
          <template #header>
            <div class="header-cell">
              <span>#</span>
              <div class="header-placeholder"></div>
            </div>
          </template>
        </el-table-column>
        <el-table-column
          v-for="col in displayColumns"
          :key="col.fieldName"
          :width="(col.usTitle || col.jpTitle || col.fieldName).length * 10 + 20"
        >
          <template #header>
            <div class="header-cell">
              <span>{{ col.usTitle || col.jpTitle }}</span>
              <el-button
                v-if="col.refTableId && col.jumpButton === 'Y'"
                size="small"
                class="header-jump-btn"
                title="Jump to {{ col.refTableId }}"
                @click.stop="colJump(col)"
              >→</el-button>
              <div v-else class="header-placeholder"></div>
            </div>
          </template>
          <template #default="{ row }">
            <div class="cell-wrap">
              <el-date-picker
                v-if="row === editingRow && (!isKeyField(col) || isNewRow) && col.calendarButton === 'Y'"
                v-model="row[col.fieldName]"
                type="date"
                value-format="YYYYMMDD"
                size="small"
                style="width:100%"
                @click.stop
              />
              <el-input
                v-else-if="row === editingRow && (!isKeyField(col) || isNewRow)"
                v-model="row[col.fieldName]"
                size="small"
                @click.stop
              />
              <span v-else class="cell-text">{{ formatCell(row[col.fieldName]) }}</span>
              <el-button
                v-if="col.refTableId && (col === displayColumns[0] || row === editingRow)"
                size="small"
                class="cell-ref-btn"
                @click.stop="openRefPicker(col, row)"
              >…</el-button>
            </div>
          </template>
        </el-table-column>
        <el-table-column width="60" prop="COMP_FLG">
          <template #header>
            <div class="header-cell">
              <span>Comp</span>
              <div class="header-placeholder"></div>
            </div>
          </template>
          <template #default="{ row }">{{ (row.COMP_FLG||'').trim() }}</template>
        </el-table-column>
        <el-table-column width="60" prop="REL_FLG">
          <template #header>
            <div class="header-cell">
              <span>Rel</span>
              <div class="header-placeholder"></div>
            </div>
          </template>
          <template #default="{ row }">{{ (row.REL_FLG||'').trim() }}</template>
        </el-table-column>
        <el-table-column width="80" prop="OWNER">
          <template #header>
            <div class="header-cell">
              <span>Owner</span>
              <div class="header-placeholder"></div>
            </div>
          </template>
          <template #default="{ row }">{{ formatCell(row.OWNER) }}</template>
        </el-table-column>
        <el-table-column width="140" prop="CRE_DATE">
          <template #header>
            <div class="header-cell">
              <span>Created</span>
              <div class="header-placeholder"></div>
            </div>
          </template>
          <template #default="{ row }">{{ formatCell(row.CRE_DATE) }}</template>
        </el-table-column>
      </el-table>
    </el-card>

    <ContextMenu
      :visible="ctxMenu.visible"
      :x="ctxMenu.x"
      :y="ctxMenu.y"
      :col="ctxMenu.col"
      :table-id="props.tableId"
      :disabled="ctxDisabled"
      @action="ctxAction"
      @close="ctxMenu.visible = false"
    />

    <RouteCopyDialog v-model="routeCopyVisible" :route-id="currentRow?.ROUTE_ID || ''" :route-ver="currentRow?.ROUTE_VER || ''" @confirm="onRouteCopyConfirm" />

    <RefPicker v-model="refPickerVisible" :table-id="refPickerConfig.tableId" :ref-field="refPickerConfig.refField" @select="onRefSelect" />
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed, watch, inject } from 'vue'
import axios from 'axios'
import { ElMessage, ElMessageBox } from 'element-plus'
import RefPicker from './RefPicker.vue'
import SearchDialog from './SearchDialog.vue'
import ContextMenu from './ContextMenu.vue'
import RouteCopyDialog from './RouteCopyDialog.vue'

const props = defineProps({ tableId: { type: String, required: true }, drillQuery: { type: Object, default: () => ({}) }, showSearch: { type: Boolean, default: true } })
const emit = defineEmits(['row-select', 'records-change', 'edit-state', 'searched', 'cell-jump'])
const toolbar = inject('toolbar')
const selectedLeftKey = inject('selectedLeftKey', ref(null))
const tableRef = ref(null)

const loading = ref(false)
const list = ref([])
const config = ref({ table: null, fields: [] })
const queryForm = ref({})
const dropdownOptions = ref({})
const refPickerVisible = ref(false)
const routeCopyVisible = ref(false)
const refPickerConfig = ref({ tableId: '', refField: '', targetField: '', targetRow: null })
const queryStatus = ref('ALL')
const currentRow = ref(null)
const searchDialogVisible = ref(false)
const ctxMenu = reactive({ visible: false, x: 0, y: 0, col: null })
const hiddenCols = ref(new Set())
const editingRow = ref(null)
const isNewRow = ref(false)

const tableTitle = computed(() => config.value.table?.usTitle || config.value.table?.jpTitle || props.tableId)
const keyFields = computed(() => config.value.fields.filter(f => f.isKey==='Y' && f.fieldName!=='REL_FLG'))
const displayColumns = computed(() => config.value.fields.filter(f => f.isDummy==='N' && !hiddenCols.value.has(f.fieldName)))
const formFields = computed(() => config.value.fields.filter(f => f.isDummy==='N'))

const canEditComp = computed(() => {
  if (!currentRow.value) return false
  return (currentRow.value.REL_FLG||'').trim()==='N' && (currentRow.value.COMP_FLG||'').trim()==='N'
})
const canRelease = computed(() => currentRow.value && (currentRow.value.REL_FLG||'').trim()==='N')

const ctxDisabled = computed(() => ({
  edit: !currentRow.value,
  save: !editingRow.value,
  editcomp: !canEditComp.value,
  release: !canRelease.value,
  delete: !currentRow.value,
  clear: !currentRow.value,
  copy: !currentRow.value,
  paste: !editingRow.value,
  find: list.value.length === 0,
  rollback: !currentRow.value || ((currentRow.value.REL_FLG || '').trim() !== 'N' && editingRow.value !== currentRow.value) || isNewRow.value,
  forceUnlock: !currentRow.value || !(currentRow.value.LOCK_USER && currentRow.value.LOCK_USER.trim()),
  routeCopy: !currentRow.value,
  routeVerUp: !currentRow.value || (currentRow.value.REL_FLG || '').trim() !== 'Y',
  routeRelease: !currentRow.value || (currentRow.value.REL_FLG || '').trim() !== 'N',
  sort: !ctxMenu.col,
  hideCol: !ctxMenu.col
}))

const isKeyField = (f) => f.isKey==='Y'
const formatCell = (v) => v ? String(v).trim() : ''

const tableRowClassName = ({ row }) => {
  const r = (row.REL_FLG||'').trim(); const c = (row.COMP_FLG||'').trim()
  if (r==='Y') return 'row-released'
  if (r==='N' && c==='Y') return 'row-editcomp'
  if (r==='N' && c==='N') return 'row-editing'
  return ''
}

const onCellChanged = (row) => { changedRows.value.add(row) }

const fetchConfig = async () => {
  try {
    const res = await axios.get(`/api/meta/${props.tableId}`)
    config.value = res.data
    const opts = {}
    const sf = config.value.fields.filter(f => f.fieldType==='SELECT' && f.retrievalTable && f.retrievalTable!=='NONE')
    for (const f of sf) {
      try { opts[f.fieldName] = (await axios.get(`/api/meta/dropdown/${f.retrievalTable}/${f.format}`)).data }
      catch(e) { opts[f.fieldName] = [] }
    }
    dropdownOptions.value = opts
  } catch (err) { ElMessage.error('加载配置失败: '+err.message) }
}

const emitRecordsChange = (data) => {
  const keys = data.map(row => { const k={}; keyFields.value.forEach(f=>{k[f.fieldName]=row[f.fieldName]}); return k })
  emit('records-change', keys, props.tableId)
}

const doSearch = async () => {
  const hasQ = Object.values(queryForm.value).some(v => v && String(v).trim())
  try {
    const res = hasQ
      ? await axios.post(`/api/dynamic/${props.tableId}/search`, queryForm.value, { params: { status: queryStatus.value } })
      : await axios.get(`/api/dynamic/${props.tableId}/list`, { params: { status: queryStatus.value } })
    list.value = dedupByBizKey(res.data); emitRecordsChange(res.data)
  } catch (err) { ElMessage.error('查询失败: '+(err.response?.data?.error||err.message)) }
}

// Deduplicate: for same biz key, prefer REL_FLG='N' over 'Y'
const dedupByBizKey = (rows) => {
  if (!rows || rows.length === 0) return rows
  const bizKeys = keyFields.value.map(f => f.fieldName)
  if (bizKeys.length === 0) return rows
  const groups = {}
  for (const row of rows) {
    const k = bizKeys.map(f => (row[f] || '').toString().trim()).join('|')
    const existing = groups[k]
    if (!existing) {
      groups[k] = row
    } else {
      const curFlg = (row.REL_FLG || '').trim()
      const extFlg = (existing.REL_FLG || '').trim()
      if (curFlg === 'N' && extFlg === 'Y') groups[k] = row
    }
  }
  return Object.values(groups)
}

const onSearchDialog = ({ status, conditions }) => {
  queryStatus.value = status
  Object.keys(queryForm.value).forEach(k => { queryForm.value[k] = '' })
  Object.keys(conditions||{}).forEach(k => { queryForm.value[k] = conditions[k] })
  doSearch()
  emit('searched')
}

// --- Toolbar actions ---
const updateToolbarState = () => {
  emit('edit-state', { editingRow: editingRow.value, isNewRow: isNewRow.value })
  if (toolbar) {
    toolbar.hasSelection = !!currentRow.value
    toolbar.canEditComp = canEditComp.value
    toolbar.canRelease = canRelease.value
    toolbar.isEditMode = !!editingRow.value
  }
}

const onRowClick = (row) => {
  currentRow.value = row; updateToolbarState()
  emit('row-select', row, config.value.fields, props.tableId)
}

const onContextMenu = (row, col, evt) => {
  evt.preventDefault()
  if (row) { currentRow.value = row; updateToolbarState() }
  ctxMenu.visible = true
  // Clamp position to keep menu within viewport (menu ~200x520px)
  ctxMenu.x = Math.min(evt.clientX, window.innerWidth - 200)
  ctxMenu.y = Math.min(evt.clientY, window.innerHeight - 520)
  ctxMenu.col = col
}

const ctxAction = (action) => {
  ctxMenu.visible = false
  switch (action) {
    case 'add': toolbar.add(); break
    case 'update': if (toolbar.hasSelection) toolbar.update(); break
    case 'save': if (toolbar.isEditMode) toolbar.save(); break
    case 'editcomp': if (toolbar.canEditComp) toolbar.editComp(); break
    case 'release': if (toolbar.canRelease) toolbar.release(); break
    case 'delete': if (toolbar.hasSelection) toolbar.delete(); break
    case 'undo': toolbar.undo(); break
    case 'clear': handleClear(); break
    case 'copy': handleCopy(); break
    case 'paste': handlePaste(); break
    case 'find': handleFind(); break
    case 'rollback': handleRollback(); break
    case 'forceUnlock': handleForceUnlock(); break
    case 'routeCopy': handleRouteCopy(); break
    case 'routeVerUp': handleRouteVerUp(); break
    case 'routeRelease': handleRouteRelease(); break
    case 'sort-asc': list.value.sort((a,b) => String(a[ctxMenu.col?.property]||'').localeCompare(String(b[ctxMenu.col?.property]||''))); break
    case 'sort-desc': list.value.sort((a,b) => String(b[ctxMenu.col?.property]||'').localeCompare(String(a[ctxMenu.col?.property]||''))); break
    case 'hide-col': if (ctxMenu.col?.property) hiddenCols.value.add(ctxMenu.col.property); break
    case 'show-all': hiddenCols.value.clear(); break
  }
}

const handleAdd = () => {
  const blank = {}
  formFields.value.forEach(f => {
    blank[f.fieldName] = f.fieldType === 'NUMBER' ? 0 : (f.defaultValue || '')
  })
  blank.REL_FLG = 'N'
  blank.COMP_FLG = 'N'
  list.value.unshift(blank)
  editingRow.value = blank
  isNewRow.value = true
  currentRow.value = blank
  updateToolbarState()
  emit('row-select', blank, config.value.fields, props.tableId)
}

const toggleUpdate = () => {
  if (!currentRow.value) return
  if (editingRow.value === currentRow.value) {
    // Toggle off
    editingRow.value = null
    isNewRow.value = false
  } else {
    // Enter edit mode for selected row
    editingRow.value = currentRow.value
    isNewRow.value = false
    editingRow.value.COMP_FLG = 'N'
    editingRow.value.REL_FLG = 'N'
  }
  updateToolbarState()
}

// Save inline edits
const saveInline = async () => {
  if (!editingRow.value) { ElMessage.warning('没有正在编辑的行'); return }
  try {
    const wasNew = isNewRow.value
    // Snapshot original data before save (for UNDO)
    const snapshot = wasNew ? null : { ...currentRow.value }
    // Build payload: only SM_FIELD_DEF business fields + REL_FLG
    const payload = {}
    formFields.value.forEach(f => {
      payload[f.fieldName] = editingRow.value[f.fieldName]
    })
    payload.REL_FLG = editingRow.value.REL_FLG
    await axios.post(`/api/dynamic/${props.tableId}/save`, payload)
    // Push to undo stack
    if (wasNew) {
      const keys = {}
      keyFields.value.forEach(f => { keys[f.fieldName] = editingRow.value[f.fieldName] })
      undoStack.value.push({ type: 'add', keys })
    } else if (snapshot) {
      undoStack.value.push({ type: 'update', row: snapshot })
    }
    ElMessage.success('保存成功')
    editingRow.value = null; isNewRow.value = false; updateToolbarState()
    doSearch()
  } catch (err) { ElMessage.error('保存失败: '+(err.response?.data?.error||err.message)) }
}

// UNDO stack: records actions (delete/add/update) for reversal
const undoStack = ref([])

const handleUndo = async () => {
  // Phase 1: local edit undo (revert unsaved changes)
  if (editingRow.value) {
    if (isNewRow.value) {
      list.value = list.value.filter(r => r !== editingRow.value)
      ElMessage.info('已撤销新增')
    } else {
      ElMessage.info('已撤销编辑')
    }
    editingRow.value = null; isNewRow.value = false; currentRow.value = null
    updateToolbarState()
    doSearch()
    return
  }

  // Phase 2: DB-level undo (reverse last committed action)
  if (undoStack.value.length === 0) { ElMessage.warning('没有可撤销的操作'); return }
  const action = undoStack.value.pop()
  try {
    switch (action.type) {
      case 'add':
        await axios.post(`/api/dynamic/${props.tableId}/delete`, action.keys)
        ElMessage.success('已撤销新增')
        break
      case 'delete':
        await axios.post(`/api/dynamic/${props.tableId}/save`, action.row)
        ElMessage.success('已撤销删除')
        break
      case 'update':
        await axios.post(`/api/dynamic/${props.tableId}/save`, action.row)
        ElMessage.success('已撤销更新')
        break
    }
    editingRow.value = null; isNewRow.value = false; currentRow.value = null
    updateToolbarState()
    doSearch()
  } catch (err) {
    // Push back on failure so user can retry
    undoStack.value.push(action)
    ElMessage.error('撤销失败: ' + (err.response?.data?.error || err.message))
  }
}

const handleEditComp = async () => {
  if (!currentRow.value) return
  try {
    // Auto-save if this is a new unsaved row
    if (isNewRow.value && editingRow.value === currentRow.value) {
      await axios.post(`/api/dynamic/${props.tableId}/save`, currentRow.value)
      editingRow.value = null; isNewRow.value = false
    }
    const keys = {}; keyFields.value.forEach(f=>{keys[f.fieldName]=currentRow.value[f.fieldName]})
    await axios.post(`/api/editcomp/${props.tableId}`, keys)
    ElMessage.success('编辑完成'); doSearch()
  } catch (err) { ElMessage.error('编辑完成失败: '+(err.response?.data?.error||err.message)) }
}

const handleRelease = async () => {
  if (!currentRow.value) return
  try {
    if (isNewRow.value && editingRow.value === currentRow.value) {
      await axios.post(`/api/dynamic/${props.tableId}/save`, currentRow.value)
      editingRow.value = null; isNewRow.value = false
    }
    const keys = {}; keyFields.value.forEach(f=>{keys[f.fieldName]=currentRow.value[f.fieldName]})
    await axios.post(`/api/release/${props.tableId}`, keys)
    ElMessage.success('Release 成功'); doSearch()
  } catch (err) { ElMessage.error('Release 失败: '+(err.response?.data?.error||err.message)) }
}

const handleDelete = async () => {
  if (!currentRow.value) return
  try {
    await ElMessageBox.confirm('确认删除?','提示',{type:'warning'})
    const snapshot = { ...currentRow.value }
    await axios.post(`/api/dynamic/${props.tableId}/delete`, currentRow.value)
    undoStack.value.push({ type: 'delete', row: snapshot })
    ElMessage.success('删除成功'); doSearch()
  } catch (err) { if (err!=='cancel') ElMessage.error('删除失败: '+(err.response?.data?.error||err.message)) }
}

const handleClear = () => {
  if (editingRow.value) {
    formFields.value.forEach(f => {
      if (f.isKey !== 'Y' || isNewRow.value) {
        editingRow.value[f.fieldName] = f.fieldType === 'NUMBER' ? 0 : ''
      }
    })
    ElMessage.info('已清除')
  } else if (currentRow.value) {
    editingRow.value = currentRow.value
    isNewRow.value = false
    editingRow.value.COMP_FLG = 'N'
    editingRow.value.REL_FLG = 'N'
    formFields.value.forEach(f => {
      if (f.isKey !== 'Y') {
        editingRow.value[f.fieldName] = f.fieldType === 'NUMBER' ? 0 : ''
      }
    })
    updateToolbarState()
    ElMessage.info('已清除')
  }
}

const handleCopy = async () => {
  if (!currentRow.value) return
  const parts = formFields.value
    .filter(f => f.isDummy !== 'Y')
    .map(f => {
      const val = currentRow.value[f.fieldName]
      return (val != null ? String(val).trim() : '')
    })
  const text = parts.join('\t')
  try {
    await navigator.clipboard.writeText(text)
    ElMessage.success('已复制到剪贴板')
  } catch (e) {
    const textarea = document.createElement('textarea')
    textarea.value = text
    textarea.style.position = 'fixed'
    textarea.style.opacity = '0'
    document.body.appendChild(textarea)
    textarea.select()
    document.execCommand('copy')
    document.body.removeChild(textarea)
    ElMessage.success('已复制到剪贴板')
  }
}

const handlePaste = async () => {
  if (!editingRow.value) {
    ElMessage.warning('请先进入编辑模式')
    return
  }
  try {
    const text = await navigator.clipboard.readText()
    const values = text.split('\t')
    const visibleFields = formFields.value.filter(f => f.isDummy !== 'Y')
    for (let i = 0; i < Math.min(values.length, visibleFields.length); i++) {
      const f = visibleFields[i]
      if (f.isKey === 'Y' && !isNewRow.value) continue
      const val = values[i].trim()
      if (f.fieldType === 'NUMBER') {
        const num = parseFloat(val)
        if (!isNaN(num)) editingRow.value[f.fieldName] = num
      } else {
        editingRow.value[f.fieldName] = val
      }
    }
    ElMessage.success('已粘贴')
  } catch (e) {
    ElMessage.warning('无法读取剪贴板')
  }
}

const handleFind = async () => {
  if (list.value.length === 0) return
  try {
    const { value: searchText } = await ElMessageBox.prompt('请输入搜索文本', '查找', {
      confirmButtonText: '查找下一个',
      cancelButtonText: '取消',
      inputPlaceholder: '输入要搜索的文本...'
    })
    if (!searchText || !searchText.trim()) return
    const text = searchText.trim().toLowerCase()
    const startIdx = currentRow.value
      ? Math.max(0, list.value.indexOf(currentRow.value))
      : -1
    for (let offset = 0; offset < list.value.length; offset++) {
      const idx = (startIdx + offset + 1) % list.value.length
      const row = list.value[idx]
      const match = formFields.value.some(f => {
        const val = row[f.fieldName]
        return val != null && String(val).toLowerCase().includes(text)
      })
      if (match) {
        currentRow.value = row
        updateToolbarState()
        tableRef.value.setCurrentRow(row)
        emit('row-select', row, config.value.fields, props.tableId)
        setTimeout(() => {
          const body = tableRef.value.$el.querySelector('.el-table__body-wrapper')
          if (body) {
            const rowEl = body.querySelectorAll('.el-table__row')[idx]
            if (rowEl) rowEl.scrollIntoView({ behavior: 'smooth', block: 'center' })
          }
        }, 50)
        return
      }
    }
    ElMessage.info('未找到匹配项')
  } catch (e) {
    // User cancelled
  }
}

const handleRollback = async () => {
  if (!currentRow.value) return
  try {
    // Local editing (not saved to DB yet): just cancel edit and reload
    if (editingRow.value === currentRow.value && !isNewRow.value) {
      await ElMessageBox.confirm('确认回滚？将撤销当前编辑并恢复原始数据。', '提示', { type: 'warning' })
      editingRow.value = null
      isNewRow.value = false
      currentRow.value = null
      updateToolbarState()
      doSearch()
      ElMessage.success('回滚成功')
      return
    }
    // DB-level rollback: overwrite B-table editable record with D-table released data
    await ElMessageBox.confirm('确认回滚？将用 D 表 Release 数据覆盖 B 表编辑记录。', '提示', { type: 'warning' })
    const keys = {}
    keyFields.value.forEach(f => { keys[f.fieldName] = currentRow.value[f.fieldName] })
    await axios.post(`/api/rollback/${props.tableId}`, keys)
    ElMessage.success('回滚成功')
    editingRow.value = null
    isNewRow.value = false
    currentRow.value = null
    updateToolbarState()
    doSearch()
  } catch (err) {
    if (err !== 'cancel') ElMessage.error('回滚失败: ' + (err.response?.data?.error || err.message))
  }
}

const handleForceUnlock = async () => {
  if (!currentRow.value) return
  try {
    await ElMessageBox.confirm('确认强制解锁该记录？', '提示', { type: 'warning' })
    const keys = {}
    keyFields.value.forEach(f => {
      if (f.fieldName !== 'REL_FLG') {
        keys[f.fieldName] = currentRow.value[f.fieldName]
      }
    })
    await axios.post(`/api/force-unlock/${props.tableId}`, keys)
    ElMessage.success('解锁成功')
    doSearch()
  } catch (err) {
    if (err !== 'cancel') ElMessage.error('解锁失败: ' + (err.response?.data?.error || err.message))
  }
}

// --- Route batch operations ---

const onRouteCopyConfirm = async (newRouteId) => {
  try {
    await ElMessageBox.confirm(
      'Route batch copy will process related tables (Route, Route Module, Route Connection). Continue?',
      'Confirm', { type: 'warning' })
    const res = await axios.post('/api/route/copy', {
      routeId: (currentRow.value.ROUTE_ID || '').trim(),
      routeVer: (currentRow.value.ROUTE_VER || '').trim(),
      newRouteId
    })
    ElMessage.success('Route copy completed: ' + JSON.stringify(res.data))
    doSearch()
  } catch (err) {
    if (err !== 'cancel') ElMessage.error('Route copy failed: ' + (err.response?.data?.error || err.message))
  }
}

const handleRouteCopy = () => { routeCopyVisible.value = true }

const handleRouteVerUp = async () => {
  if (!currentRow.value) return
  try {
    await ElMessageBox.confirm(
      'Revise version for all objects in Route? This will increment ROUTE_VER for all related tables.',
      'Confirm', { type: 'warning' })
    const res = await axios.post('/api/route/verup', {
      routeId: (currentRow.value.ROUTE_ID || '').trim(),
      routeVer: (currentRow.value.ROUTE_VER || '').trim()
    })
    ElMessage.success('Route version up completed. New version: ' + res.data.newVersion)
    doSearch()
  } catch (err) {
    if (err !== 'cancel') ElMessage.error('Route verup failed: ' + (err.response?.data?.error || err.message))
  }
}

const handleRouteRelease = async () => {
  if (!currentRow.value) return
  try {
    await ElMessageBox.confirm(
      'Release all objects in Route? This will batch release all related tables.',
      'Confirm', { type: 'warning' })
    await axios.post('/api/route/release', {
      routeId: (currentRow.value.ROUTE_ID || '').trim(),
      routeVer: (currentRow.value.ROUTE_VER || '').trim()
    })
    ElMessage.success('Route batch release completed')
    doSearch()
  } catch (err) {
    if (err !== 'cancel') ElMessage.error('Route release failed: ' + (err.response?.data?.error || err.message))
  }
}

const colJump = (f) => {
  emit('cell-jump', { tableId: f.refTableId, label: f.usTitle || f.jpTitle || f.refTableId, query: {} })
}

const cellJump = (f, row) => {
  const query = {}
  keyFields.value.forEach(kf => {
    query[kf.fieldName] = (row[kf.fieldName] || '').toString().trim()
  })
  emit('cell-jump', { tableId: f.refTableId, label: f.usTitle || f.jpTitle || f.refTableId, query })
}

const openRefPicker = (f, row) => {
  refPickerConfig.value = { tableId: f.refTableId, refField: f.refFieldName, targetField: f.fieldName, targetRow: row }
  refPickerVisible.value = true
}
const onRefSelect = (val) => {
  const row = refPickerConfig.value.targetRow
  if (row) row[refPickerConfig.value.targetField] = val
}

// Wire toolbar (called immediately + on every action)
const wireToolbar = () => {
  if (!toolbar) return
  toolbar.add = handleAdd
  toolbar.edit = toggleUpdate
  toolbar.editComp = handleEditComp
  toolbar.release = handleRelease
  toolbar.delete = handleDelete
  toolbar.update = toggleUpdate
  toolbar.save = saveInline
  toolbar.undo = handleUndo
  toolbar.copy = handleCopy
  toolbar.paste = handlePaste
  toolbar.find = handleFind
  toolbar.rollback = handleRollback
  toolbar.routeCopy = handleRouteCopy
  toolbar.routeVerUp = handleRouteVerUp
  toolbar.routeRelease = handleRouteRelease
  updateToolbarState()
}
wireToolbar()

let initialLoadDone = false
const load = async () => {
  loading.value = true; await fetchConfig(); loading.value = false
  // Apply drill-down query params if present
  const q = props.drillQuery
  if (q && Object.keys(q).length > 0) {
    queryStatus.value = 'ALL'
    Object.keys(q).forEach(k => { queryForm.value[k] = q[k] })
    doSearch()
    emit('searched')
  } else if (props.showSearch) {
    searchDialogVisible.value = true
  } else {
    doSearch()
    emit('searched')
  }
  setTimeout(wireToolbar, 50)
}

onMounted(() => { initialLoadDone = true; load() })
watch(() => props.tableId, () => { if (initialLoadDone) load() })

// Group filter from left panel tree → re-query with filter
watch(() => props.drillQuery, (q) => {
  if (!initialLoadDone) return
  if (q && Object.keys(q).length > 0) {
    queryStatus.value = 'ALL'
    Object.keys(queryForm.value).forEach(k => { queryForm.value[k] = '' })
    Object.keys(q).forEach(k => { queryForm.value[k] = q[k] })
    doSearch()
    emit('searched')
  }
})

// Left panel selection → scroll center table
watch(selectedLeftKey, (key) => {
  if (!key || !tableRef.value) return
  const kf = keyFields.value
  // Find matching row by comparing key field values
  const idx = list.value.findIndex(row => {
    return kf.every(f => {
      const rv = (row[f.fieldName] || '').toString().trim()
      const kv = (key[f.fieldName] || '').toString().trim()
      return rv === kv
    })
  })
  if (idx >= 0) {
    const row = list.value[idx]
    currentRow.value = row
    updateToolbarState()
    emit('row-select', row, config.value.fields, props.tableId)
    tableRef.value.setCurrentRow(row)
    // Scroll to row
    const body = tableRef.value.$el.querySelector('.el-table__body-wrapper')
    if (body) {
      const rowEl = body.querySelectorAll('.el-table__row')[idx]
      if (rowEl) rowEl.scrollIntoView({ behavior: 'smooth', block: 'center' })
    }
  }
})
</script>

<style scoped>
.card-header { display: flex; justify-content: space-between; align-items: center; }
:deep(.el-card) { border-radius: 8px; overflow: hidden; margin: 8px; }
:deep(.el-card__header) { padding: 6px 12px !important; }
:deep(.el-card__body) { padding: 6px 12px !important; }
.input-with-btn { display: flex; align-items: center; gap: 8px; }
.cell-text { font-size: 12px; color: #333; }
.cell-wrap { display: flex; align-items: center; gap: 2px; }
.cell-ref-btn { padding: 0 4px; font-size: 10px; min-height: 20px; flex-shrink: 0; }
.header-cell { display: flex; flex-direction: column; align-items: stretch; }
.header-cell span { display: flex; align-items: flex-start; justify-content: center; padding: 4px 4px 2px; font-weight: 600; color: #333; font-size: 12px; height: 22px; }
.header-placeholder { height: 22px; border-top: 1px solid #d0d0d0; background: #e8e8e8; }
.header-jump-btn { font-size: 11px; border-radius: 0; border: none; border-top: 1px solid #d0d0d0; background: #e8e8e8; padding: 3px 0; height: 22px; width: 100%; justify-content: center; }
:deep(.el-table__header) th { background: linear-gradient(to bottom, #f0f0f0 50%, #e8e8e8 50%) !important; padding: 0 !important; }
:deep(.el-table__header) th .cell { padding: 0 !important; width: 100%; }
:deep(.el-table__header) th { background-color: #f0f0f0 !important; color: #333; font-weight: 600; }
:deep(.row-editing) { background-color: #f5f5f5 !important; }
:deep(.row-editcomp) { background-color: #fffbe6 !important; }
:deep(.row-released) { background-color: #f6ffed !important; }
:deep(.el-table__body tr.current-row) { background-color: #e6f7ff !important; }
:deep(.el-input__inner) { padding: 0 4px; font-size: 12px; }
</style>
