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
              v-if="f.refTableId"
              size="small"
              class="ref-btn"
              @click="openRefPicker(f)"
            >...</el-button>
            <span v-else class="ref-placeholder"></span>
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

// Drill-down: fetch from /api/meta/drills/{tableId}
const drillTargets = ref([])
const fetchDrills = async () => {
  if (!props.tableId) { drillTargets.value = []; return }
  try { drillTargets.value = (await axios.get('/api/meta/drills/' + props.tableId)).data }
  catch(e) { drillTargets.value = [] }
}
watch(() => props.tableId, fetchDrills, { immediate: true })

const drillDown = (dd) => {
  if (!props.record) return
  // Build query params from current record's key fields
  const keyFields = props.fields.filter(f => f.isKey === 'Y' && f.fieldName !== 'REL_FLG')
  const query = {}
  keyFields.forEach(f => {
    query[f.fieldName] = (props.record[f.fieldName] || '').toString().trim()
  })
  emit('drill-down', { tableId: dd.targetTableId, label: dd.label, query })
}

const dataFields = computed(() => {
  return props.fields.filter(f => f.isDummy === 'N')
})

const propertyLabels = [
  { key: 'REL_FLG', label: '状态' },
  { key: 'COMP_FLG', label: '编辑完成' },
  { key: 'CRE_DATE', label: '创建日时' },
  { key: 'CRE_USER', label: '创建者' },
  { key: 'LAST_DATE1', label: '最终更新日时' },
  { key: 'LAST_ACT1', label: '最终更新操作' },
  { key: 'LAST_USER1', label: '最终更新者' },
  { key: 'OWNER', label: '所有者' },
  { key: 'OWNERG', label: '所有组' },
  { key: 'PERMISSION', label: '权限' },
  { key: 'LOCK_USER', label: '锁定者' },
  { key: 'LOCK_TIME', label: '锁定时间' },
]

const propertyFields = computed(() => propertyLabels)

const isKeyField = (f) => f.isKey === 'Y'

const formatVal = (val) => {
  if (val === null || val === undefined) return ''
  if (typeof val === 'string') return val.trim()
  return val
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
.record-detail { padding: 8px; font-size: 12px; }
.panel-title { font-weight: bold; padding: 8px; border-bottom: 1px solid #e8e8e8; margin-bottom: 4px; }
.tab-toolbar { padding: 4px 0 8px; text-align: right; }
.kv-list { }
.kv-row {
  display: flex; align-items: center; padding: 2px 0;
  border-bottom: 1px solid #f5f5f5; gap: 4px;
}
.kv-key { width: 80px; color: #888; flex-shrink: 0; text-align: right; font-size: 11px; }
.kv-input-wrap { flex: 1; min-width: 0; }
.kv-input-wrap :deep(.el-input__inner) { padding: 0 4px; font-size: 12px; }
.ref-btn { flex-shrink: 0; padding: 2px 6px; font-size: 11px; min-width: 24px; }
.ref-placeholder { width: 24px; flex-shrink: 0; }
.kv-val { flex: 1; word-break: break-all; }
.empty-hint { color: #999; text-align: center; padding: 40px 0; font-size: 13px; }
.drilldown-section { margin-top: 12px; padding-top: 8px; border-top: 1px solid #e8e8e8; }
.section-title { font-size: 12px; color: #666; margin-bottom: 6px; }
.drilldown-btns { display: flex; flex-wrap: wrap; gap: 4px; }
</style>
