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
  return props.fields.filter(f => f.isDummy === 'N' && f.isAuto !== 'Y')
})

const propertyFields = computed(() => {
  if (!props.record) return []
  return props.fields
    .filter(f => f.isAuto === 'Y' && f.fieldName in props.record)
    .sort((a, b) => (a.propertyNo || 0) - (b.propertyNo || 0))
    .map(f => ({ key: f.fieldName, label: f.usTitle || f.jpTitle || f.fieldName }))
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
.kv-list { padding: 6px 12px; }
.kv-row {
  display: flex; align-items: center; padding: 2px 0; gap: 6px; border-bottom: 1px solid var(--c-border-light, #E2E6EC);
}
.kv-key { width: 72px; color: var(--c-text-secondary, #5C6B7A); flex-shrink: 0; text-align: left; font-size: 11px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; font-weight: 600; }
.kv-input-wrap { flex: 1; min-width: 0; }
.kv-input-wrap :deep(.el-input__inner) { padding: 2px 6px; font-size: 12px; border-radius: 1px; }
.kv-input-wrap :deep(.el-input__wrapper) { box-shadow: none; border-radius: 1px; }
.kv-input-wrap :deep(.el-input__wrapper:hover) { box-shadow: 0 0 0 1px var(--c-border, #D0D5DC) inset; }
.ref-btn { flex-shrink: 0; padding: 0 6px; font-size: 11px; min-height: 20px; border-radius: 1px; }
.ref-placeholder { width: 28px; flex-shrink: 0; }
.kv-val { flex: 1; word-break: break-all; padding: 2px 6px; color: var(--c-text, #1A2233); font-family: 'Consolas', 'Monaco', monospace; font-size: 11px; }
.empty-hint { color: var(--c-text-secondary, #5C6B7A); text-align: center; padding: 40px 0; font-size: 13px; }
.drilldown-section { margin: 0 8px 8px; padding-top: 6px; border-top: 2px solid var(--c-border, #D0D5DC); }
.section-title { font-size: 10px; color: var(--c-text-secondary, #5C6B7A); margin-bottom: 4px; font-weight: 700; padding: 0 4px; text-transform: uppercase; letter-spacing: 0.5px; }
.drilldown-btns { display: flex; flex-direction: column; gap: 2px; padding: 0 4px; }
.drilldown-btns .el-button { width: 100%; justify-content: center; margin-left: 0; border-radius: 1px; }
</style>
