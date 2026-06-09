<template>
  <div class="record-detail">
    <div class="panel-title">记录详情</div>
    <el-tabs v-model="activeTab" v-if="record" tab-position="bottom" class="bottom-tabs">
      <el-tab-pane label="Data" name="data">
        <el-table :data="allDataRows" size="small" border height="100%" class="detail-table" :show-overflow-tooltip="true">
          <el-table-column prop="label" label="Item name" width="120">
            <template #default="{ row }">
              <span :class="{ 'key-field': row.isKey, 'dummy-field': row.isDummy }">{{ row.isDummy ? '(' + row.label + ')' : (row.isKey ? '*' + row.label : row.label) }}</span>
            </template>
          </el-table-column>
          <el-table-column label="Value" min-width="150">
            <template #default="{ row }">
              <template v-if="row.isDummy">
                <el-button size="small" type="primary" class="open-btn" @click="openDummyTable(row.field)">OPEN</el-button>
              </template>
              <template v-else-if="isEditing">
                <el-date-picker
                  v-if="row.field.calendarButton === 'Y'"
                  v-model="record[row.field.fieldName]"
                  type="date"
                  value-format="YYYYMMDD"
                  size="small"
                  style="width:100%"
                  :disabled="row.isKey && !isNew"
                />
                <el-select
                  v-else-if="row.field.fieldType === 'SELECT' && dropdownOptions[row.field.fieldName]"
                  v-model="record[row.field.fieldName]"
                  size="small"
                  filterable
                  clearable
                  style="width:100%"
                  :disabled="row.isKey && !isNew"
                >
                  <el-option v-for="opt in dropdownOptions[row.field.fieldName]" :key="opt.FLD_VAL || opt.value" :label="(opt.FLD_VAL || opt.value) + ' - ' + (opt.FLD_STR || opt.label || '')" :value="opt.FLD_VAL || opt.value" />
                </el-select>
                <el-input
                  v-else
                  v-model="record[row.field.fieldName]"
                  size="small"
                  :disabled="row.isKey && !isNew"
                  :maxlength="row.field.fieldLength || 100"
                />
              </template>
              <span v-else class="cell-val">{{ row.value }}</span>
            </template>
          </el-table-column>
          <el-table-column width="30">
            <template #default="{ row }">
              <span v-if="row.field.refTableId && !row.isDummy" class="jump-cell" @click="openRefPicker(row.field)">J</span>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>
      <el-tab-pane label="Property" name="property">
        <el-table :data="propertyRows" size="small" border height="100%" class="detail-table" :show-overflow-tooltip="true">
          <el-table-column prop="label" label="Item name" width="120" />
          <el-table-column label="Value" min-width="150">
            <template #default="{ row }">
              <span class="cell-val">{{ row.value }}</span>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>
    </el-tabs>
    <div v-else class="empty-hint">请选择一条记录</div>

    <RefPicker
      v-model="refPickerVisible"
      :table-id="refPickerConfig.tableId"
      :ref-field="refPickerConfig.refField"
      @select="onRefSelect"
    />
  </div>
</template>

<script setup>
import { ref, computed, watch, inject } from 'vue'
import axios from 'axios'
import RefPicker from './RefPicker.vue'

const props = defineProps({
  tableId: { type: String, default: '' },
  record: { type: Object, default: null },
  fields: { type: Array, default: () => [] },
  isNew: { type: Boolean, default: false }
})

const emit = defineEmits(['drill-down'])

const toolbar = inject('toolbar', { isEditMode: false })
const isEditing = computed(() => toolbar.isEditMode)
const activeTab = ref('data')
const dropdownOptions = ref({})

const loadDropdowns = async () => {
  const opts = {}
  const selectFields = props.fields.filter(f => f.fieldType === 'SELECT' && f.retrievalTable && f.retrievalTable !== 'NONE')
  for (const f of selectFields) {
    try { opts[f.fieldName] = (await axios.get(`/api/meta/dropdown/${f.retrievalTable}/${f.format}`)).data }
    catch(e) { opts[f.fieldName] = [] }
  }
  dropdownOptions.value = opts
}
watch(() => props.fields, loadDropdowns, { immediate: true })
const refPickerVisible = ref(false)
const refPickerConfig = ref({ tableId: '', refField: '', targetField: '' })

const openDummyTable = (f) => {
  const query = buildKeyQuery()
  emit('drill-down', { tableId: f.refTableId, label: f.usTitle || f.jpTitle || f.fieldName, query })
}

const buildKeyQuery = () => {
  const keyFields = props.fields.filter(f => f.isKey === 'Y' && f.fieldName !== 'REL_FLG')
  const query = {}
  keyFields.forEach(f => {
    query[f.fieldName] = (props.record[f.fieldName] || '').toString().trim()
  })
  return query
}

const dataFields = computed(() => {
  return props.fields.filter(f => f.isDummy === 'N' && f.isAuto !== 'Y')
})

const dummyOpenFields = computed(() => {
  return props.fields.filter(f => f.isDummy === 'Y' && f.openButton > 0 && f.refTableId)
})

const allDataRows = computed(() => {
  if (!props.record) return []
  const rows = []
  for (const f of dataFields.value) {
    rows.push({
      label: f.usTitle || f.jpTitle || f.fieldName,
      value: formatVal(props.record[f.fieldName]),
      isKey: f.isKey === 'Y',
      isDummy: false,
      field: f
    })
  }
  for (const f of dummyOpenFields.value) {
    rows.push({
      label: f.usTitle || f.jpTitle || f.fieldName,
      value: '',
      isKey: false,
      isDummy: true,
      field: f
    })
  }
  return rows
})

const propertyFields = computed(() => {
  if (!props.record) return []
  return props.fields
    .filter(f => f.isAuto === 'Y' && f.fieldName in props.record)
    .sort((a, b) => (a.propertyNo || 0) - (b.propertyNo || 0))
    .map(f => ({ key: f.fieldName, label: f.usTitle || f.jpTitle || f.fieldName }))
})

const propertyRows = computed(() => {
  return propertyFields.value.map(p => ({
    label: p.label,
    value: formatVal(props.record[p.key])
  }))
})

const isKeyField = (f) => f.isKey === 'Y'

const formatVal = (val) => {
  if (val === null || val === undefined) return ''
  if (typeof val === 'string') {
    // Detect ISO timestamp strings like "2026-06-05T08:32:40.634+00:00"
    if (/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}/.test(val)) {
      return formatTimestamp(val)
    }
    return val.trim()
  }
  if (typeof val === 'number' && val > 1000000000000) {
    // Epoch millis
    return formatTimestamp(val)
  }
  return val
}

const formatTimestamp = (val) => {
  const d = new Date(val)
  if (isNaN(d.getTime())) return String(val)
  const pad = (n, len = 2) => String(n).padStart(len, '0')
  return `${d.getFullYear()}-${pad(d.getMonth()+1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}.${pad(d.getMilliseconds(),3)}000`
}

const openRefPicker = (field) => {
  refPickerConfig.value = {
    tableId: field.refTableId,
    refField: field.refFieldName,
    targetField: field.fieldName
  }
  refPickerVisible.value = true
}

const onRefSelect = (val) => {
  if (props.record) {
    props.record[refPickerConfig.value.targetField] = val
  }
}
</script>

<style scoped>
.record-detail { padding: 0; font-size: 12px; }
.record-detail :deep(.el-tabs__header) { padding-left: 12px; }
.panel-title { font-weight: 700; padding: 0 12px; height: 28px; line-height: 28px; border-bottom: 2px solid var(--c-primary, #2B5CE6); color: var(--c-text, #1A2233); font-size: 11px; text-transform: uppercase; letter-spacing: 0.3px; background: var(--c-border-light, #E2E6EC); }
.tab-toolbar { padding: 4px 0 8px; text-align: right; }
.empty-hint { color: var(--c-text-secondary, #5C6B7A); text-align: center; padding: 40px 0; font-size: 13px; }
.detail-table { border-radius: 0 !important; }
.detail-table :deep(.el-table__header th) { background: #E8ECF2 !important; font-size: 11px; font-weight: 700; padding: 2px 0 !important; }
.detail-table :deep(.el-table__body td) { padding: 1px 0 !important; }
.detail-table :deep(.el-table .cell) { padding: 0 4px !important; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; font-size: 12px; }
.detail-table :deep(.el-input__inner) { padding: 0 4px; font-size: 12px; border-radius: 1px; }
.key-field { font-weight: 700; color: var(--c-text, #1A2233); }
.dummy-field { color: var(--c-text-secondary, #5C6B7A); }
.cell-val { font-size: 12px; color: var(--c-text, #1A2233); }
.jump-cell { cursor: pointer; color: var(--c-primary, #2B5CE6); font-weight: 700; font-size: 11px; }
.jump-cell:hover { text-decoration: underline; }
.open-btn { border-radius: 1px; font-size: 10px; padding: 2px 8px; min-height: 20px; }
.bottom-tabs { height: 100%; display: flex; flex-direction: column; }
.bottom-tabs :deep(.el-tabs__content) { flex: 1; min-height: 0; overflow: hidden; }
.bottom-tabs :deep(.el-tab-pane) { height: 100%; overflow: hidden; }
.bottom-tabs :deep(.el-tabs__header) { margin: 0; }
.record-detail :deep(.el-tabs__header) { padding-left: 0 !important; }
</style>
