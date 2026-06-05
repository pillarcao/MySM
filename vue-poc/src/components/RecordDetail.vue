<template>
  <div class="record-detail">
    <div class="panel-title">记录详情</div>
    <el-tabs v-model="activeTab" v-if="record">
      <el-tab-pane label="Data" name="data">
        <div class="kv-list">
          <div class="kv-row" v-for="f in dataFields" :key="f.fieldName">
            <span class="kv-key">{{ f.usTitle || f.jpTitle || f.fieldName }}</span>
            <div class="kv-input-wrap">
              <el-date-picker
                v-if="f.calendarButton === 'Y'"
                v-model="record[f.fieldName]"
                type="date"
                value-format="YYYYMMDD"
                size="small"
                style="width:100%"
                :disabled="isKeyField(f) && !isNew"
              />
              <el-input
                v-else
                v-model="record[f.fieldName]"
                size="small"
                :disabled="isKeyField(f) && !isNew"
                :maxlength="f.fieldLength || 100"
              />
            </div>
            <el-button
              v-if="f.refTableId && record[f.fieldName]"
              size="small"
              class="ref-btn"
              title="Jump to referenced table"
              @click="jumpToRef(f)"
            >→</el-button>
            <el-button
              v-if="f.refTableId"
              size="small"
              class="ref-btn"
              title="Select from reference"
              @click="openRefPicker(f)"
            >…</el-button>
            <span v-else-if="!f.refTableId" class="ref-placeholder"></span>
          </div>
        </div>
        <div class="drilldown-section" v-if="drillTargets.length > 0">
          <div class="section-title">Related</div>
          <div class="drilldown-btns">
            <el-button
              v-for="dd in drillTargets" :key="dd.targetTableId"
              size="small"
              @click="drillDown(dd)"
            >{{ dd.label }}</el-button>
          </div>
        </div>
      </el-tab-pane>
      <el-tab-pane label="Property" name="property">
        <div class="kv-list">
          <div class="kv-row" v-for="p in propertyFields" :key="p.key">
            <span class="kv-key">{{ p.label }}</span>
            <span class="kv-val">{{ formatVal(record[p.key]) }}</span>
          </div>
        </div>
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
import { ref, computed, watch } from 'vue'
import axios from 'axios'
import RefPicker from './RefPicker.vue'

const props = defineProps({
  tableId: { type: String, default: '' },
  record: { type: Object, default: null },
  fields: { type: Array, default: () => [] },
  isNew: { type: Boolean, default: false }
})

const emit = defineEmits(['drill-down'])

const activeTab = ref('data')
const refPickerVisible = ref(false)
const refPickerConfig = ref({ tableId: '', refField: '', targetField: '' })

// Drill-down: from SM_DRILL_DEF (table-level)
const drillTargets = ref([])
const fetchDrills = async () => {
  if (!props.tableId) { drillTargets.value = []; return }
  try { drillTargets.value = (await axios.get('/api/meta/drills/' + props.tableId)).data }
  catch(e) { drillTargets.value = [] }
}
watch(() => props.tableId, fetchDrills, { immediate: true })

const jumpToRef = (f) => {
  if (!props.record) return
  emit('drill-down', { tableId: f.refTableId, label: f.usTitle || f.jpTitle || f.refTableId, query: buildKeyQuery() })
}

const drillDown = (dd) => {
  const query = {}
  if (props.record) {
    const keyFields = props.fields.filter(f => f.isKey === 'Y' && f.fieldName !== 'REL_FLG')
    keyFields.forEach(f => {
      query[f.fieldName] = (props.record[f.fieldName] || '').toString().trim()
    })
  }
  emit('drill-down', { tableId: dd.targetTableId, label: dd.label, query })
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
  return props.fields.filter(f => f.isDummy === 'N')
})

const propertyLabels = [
  { key: 'REL_FLG', label: '状态' },
  { key: 'COMP_FLG', label: '编辑完成' },
  { key: 'CRE_DATE', label: '创建日时' },
  { key: 'CRE_USER', label: '创建者' },
  { key: 'OWNER', label: '所有者' },
  { key: 'OWNERG', label: '所有组' },
  { key: 'PERMISSION', label: '权限' },
  { key: 'LOCK_USER', label: '锁定者' },
  { key: 'LOCK_TIME', label: '锁定时间' },
  { key: 'LAST_DATE1', label: 'Release时间' },
  { key: 'LAST_ACT1', label: 'Release操作' },
  { key: 'LAST_USER1', label: 'Release人员' },
  { key: 'LAST_DATE2', label: 'EditComp时间' },
  { key: 'LAST_ACT2', label: 'EditComp操作' },
  { key: 'LAST_USER2', label: 'EditComp人员' },
  { key: 'LAST_DATE3', label: 'Create时间' },
  { key: 'LAST_ACT3', label: 'Create操作' },
  { key: 'LAST_USER3', label: 'Create人员' },
  { key: 'LAST_DATE4', label: 'Save时间' },
  { key: 'LAST_ACT4', label: 'Save操作' },
  { key: 'LAST_USER4', label: 'Save人员' },
  { key: 'LAST_DATE5', label: '历史5时间' },
  { key: 'LAST_ACT5', label: '历史5操作' },
  { key: 'LAST_USER5', label: '历史5人员' },
]

const propertyFields = computed(() => propertyLabels.filter(p => props.record && p.key in props.record))

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
.panel-title { font-weight: 600; padding: 0 12px; height: 30px; line-height: 30px; border-bottom: 1px solid #e8e8e8; color: #333; }
.tab-toolbar { padding: 4px 0 8px; text-align: right; }
.kv-list { padding: 4px 8px; }
.kv-row {
  display: flex; align-items: center; padding: 3px 0; gap: 6px;
}
.kv-key { width: 72px; color: #999; flex-shrink: 0; text-align: right; font-size: 11px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.kv-input-wrap { flex: 1; min-width: 0; }
.kv-input-wrap :deep(.el-input__inner) { padding: 2px 6px; font-size: 12px; }
.kv-input-wrap :deep(.el-input__wrapper) { box-shadow: none; }
.kv-input-wrap :deep(.el-input__wrapper:hover) { box-shadow: 0 0 0 1px #dcdfe6 inset; }
.ref-btn { flex-shrink: 0; padding: 0 6px; font-size: 11px; min-height: 22px; }
.ref-placeholder { width: 28px; flex-shrink: 0; }
.kv-val { flex: 1; word-break: break-all; padding: 2px 6px; color: #333; }
.empty-hint { color: #999; text-align: center; padding: 40px 0; font-size: 13px; }
.drilldown-section { margin: 0 8px 8px; padding-top: 6px; border-top: 1px solid #e8e8e8; }
.section-title { font-size: 11px; color: #999; margin-bottom: 4px; font-weight: 600; padding: 0 4px; }
.drilldown-btns { display: flex; flex-direction: column; gap: 2px; padding: 0 4px; }
.drilldown-btns .el-button { width: 100%; justify-content: center; margin-left: 0; }
</style>
