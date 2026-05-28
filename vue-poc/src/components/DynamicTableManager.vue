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
        style="width: 100%; font-size: 12px;"
        :row-class-name="tableRowClassName"
        highlight-current-row
        @row-click="onRowClick"
      >
        <el-table-column
          v-for="col in displayColumns"
          :key="col.fieldName"
          :prop="col.fieldName"
          :label="col.usTitle || col.jpTitle"
          :width="(col.usTitle || col.jpTitle || col.fieldName).length * 10 + 20"
        >
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
              >...</el-button>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="Comp" width="60" prop="COMP_FLG">
          <template #default="{ row }">{{ (row.COMP_FLG||'').trim() }}</template>
        </el-table-column>
        <el-table-column label="Rel" width="60" prop="REL_FLG">
          <template #default="{ row }">{{ (row.REL_FLG||'').trim() }}</template>
        </el-table-column>
      </el-table>
    </el-card>

    <RefPicker v-model="refPickerVisible" :table-id="refPickerConfig.tableId" :ref-field="refPickerConfig.refField" @select="onRefSelect" />
  </div>
</template>

<script setup>
import { ref, onMounted, computed, watch, inject } from 'vue'
import axios from 'axios'
import { ElMessage, ElMessageBox } from 'element-plus'
import RefPicker from './RefPicker.vue'
import SearchDialog from './SearchDialog.vue'

const props = defineProps({ tableId: { type: String, required: true }, drillQuery: { type: Object, default: () => ({}) }, showSearch: { type: Boolean, default: true } })
const emit = defineEmits(['row-select', 'records-change', 'edit-state', 'searched'])
const toolbar = inject('toolbar')
const selectedLeftKey = inject('selectedLeftKey', ref(null))
const tableRef = ref(null)

const loading = ref(false)
const list = ref([])
const config = ref({ table: null, fields: [] })
const queryForm = ref({})
const dropdownOptions = ref({})
const refPickerVisible = ref(false)
const refPickerConfig = ref({ tableId: '', refField: '', targetField: '', targetRow: null })
const queryStatus = ref('EDIT')
const currentRow = ref(null)
const searchDialogVisible = ref(false)
const editingRow = ref(null)
const isNewRow = ref(false)

const tableTitle = computed(() => config.value.table?.usTitle || config.value.table?.jpTitle || props.tableId)
const keyFields = computed(() => config.value.fields.filter(f => f.isKey==='Y' && f.fieldName!=='REL_FLG'))
const displayColumns = computed(() => config.value.fields.filter(f => f.isDummy==='N'))
const formFields = computed(() => config.value.fields.filter(f => f.isDummy==='N'))

const canEditComp = computed(() => {
  if (!currentRow.value) return false
  return (currentRow.value.REL_FLG||'').trim()==='N' && (currentRow.value.COMP_FLG||'').trim()==='N'
})
const canRelease = computed(() => currentRow.value && (currentRow.value.REL_FLG||'').trim()==='N')

const isKeyField = (f) => f.isKey==='Y'
const formatCell = (v) => v ? String(v).trim() : ''

const tableRowClassName = ({ row }) => {
  const r = (row.REL_FLG||'').trim(); const c = (row.COMP_FLG||'').trim()
  if (r==='Y') return 'row-released'
  if (r==='N' && c==='Y') return 'row-editcomp'
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
    list.value = res.data; emitRecordsChange(res.data)
  } catch (err) { ElMessage.error('查询失败: '+(err.response?.data?.error||err.message)) }
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
    await axios.post(`/api/dynamic/${props.tableId}/save`, editingRow.value)
    ElMessage.success('保存成功')
    editingRow.value = null; isNewRow.value = false; updateToolbarState()
    doSearch()
  } catch (err) { ElMessage.error('保存失败: '+(err.response?.data?.error||err.message)) }
}

const handleUndo = () => {
  if (!isNewRow.value || !editingRow.value) { ElMessage.warning('只能撤销新增的行'); return }
  const idx = list.value.indexOf(editingRow.value)
  if (idx >= 0) list.value.splice(idx, 1)
  editingRow.value = null; isNewRow.value = false; currentRow.value = null
  updateToolbarState()
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
    await axios.post(`/api/dynamic/${props.tableId}/delete`, currentRow.value)
    ElMessage.success('删除成功'); doSearch()
  } catch (err) { if (err!=='cancel') ElMessage.error('删除失败: '+(err.response?.data?.error||err.message)) }
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
    tableRef.value.setCurrentRow(list.value[idx])
    // Scroll to row
    const body = tableRef.value.$el.querySelector('.el-table__body-wrapper')
    if (body) {
      const row = body.querySelectorAll('.el-table__row')[idx]
      if (row) row.scrollIntoView({ behavior: 'smooth', block: 'center' })
    }
  }
})
</script>

<style scoped>
.card-header { display: flex; justify-content: space-between; align-items: center; }
.input-with-btn { display: flex; align-items: center; gap: 8px; }
.cell-text { font-size: 12px; }
.cell-wrap { display: flex; align-items: center; gap: 2px; }
.cell-ref-btn { padding: 2px 4px; font-size: 10px; min-height: 20px; flex-shrink: 0; }
:deep(.row-editcomp) { background-color: #f6ffed !important; }
:deep(.row-released) { background-color: #e6f7ff !important; }
:deep(.el-input__inner) { padding: 0 4px; font-size: 12px; }
</style>
