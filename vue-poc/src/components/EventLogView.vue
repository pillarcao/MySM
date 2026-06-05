<template>
  <div class="evtlog-view">
    <div class="evtlog-filter">
      <el-date-picker
        v-model="dateRange"
        type="datetimerange"
        range-separator="~"
        start-placeholder="Start"
        end-placeholder="End"
        size="small"
        value-format="YYYY-MM-DD HH:mm:ss"
        style="width: 340px"
      />
      <el-select v-model="filterTable" placeholder="Table" clearable size="small" style="width: 140px" filterable>
        <el-option v-for="t in tableOptions" :key="t" :label="t" :value="t" />
      </el-select>
      <el-select v-model="filterUser" placeholder="User" clearable size="small" style="width: 120px" filterable>
        <el-option v-for="u in userOptions" :key="u" :label="u" :value="u" />
      </el-select>
      <el-button type="primary" size="small" @click="doSearch">Search</el-button>
      <span class="evtlog-count" v-if="rows.length > 0">{{ rows.length }} records</span>
    </div>
    <div class="evtlog-table">
      <el-table :data="rows" size="small" border stripe height="100%" style="width: 100%"
                :show-overflow-tooltip="true"
                :default-sort="{ prop: 'EVT_TIME', order: 'descending' }">
        <el-table-column prop="EVT_TIME" label="Time" width="170" sortable>
          <template #default="{ row }">{{ formatTime(row.EVT_TIME) }}</template>
        </el-table-column>
        <el-table-column prop="EVT_CODE" label="Event" width="100" sortable>
          <template #default="{ row }">
            <el-tag :type="tagType(row.EVT_CODE)" size="small">{{ row.EVT_CODE.trim() }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="USER_ID" label="User" width="120" sortable>
          <template #default="{ row }">{{ row.USER_ID && row.USER_ID.trim() }}</template>
        </el-table-column>
        <el-table-column prop="TBL_NAME" label="Table" width="140" sortable>
          <template #default="{ row }">{{ row.TBL_NAME && row.TBL_NAME.trim() }}</template>
        </el-table-column>
        <el-table-column prop="TBL_KEY" label="Key" min-width="180">
          <template #default="{ row }">{{ row.TBL_KEY && row.TBL_KEY.trim() }}</template>
        </el-table-column>
        <el-table-column prop="COMMENT" label="Comment" min-width="140">
          <template #default="{ row }">{{ row.COMMENT && row.COMMENT.trim() }}</template>
        </el-table-column>
      </el-table>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'

const dateRange = ref(null)
const filterTable = ref('')
const filterUser = ref('')
const rows = ref([])
const tableOptions = ref([])
const userOptions = ref([])

const doSearch = async () => {
  const params = { limit: 500 }
  if (dateRange.value && dateRange.value[0]) params.startDate = dateRange.value[0]
  if (dateRange.value && dateRange.value[1]) params.endDate = dateRange.value[1]
  if (filterTable.value) params.tableName = filterTable.value
  if (filterUser.value) params.userId = filterUser.value
  try {
    const res = await axios.post('/api/evtlog/search', params)
    rows.value = res.data
  } catch (e) {
    console.error('evtlog search failed:', e)
  }
}

const loadOptions = async () => {
  try {
    const [t, u] = await Promise.all([
      axios.get('/api/evtlog/tables'),
      axios.get('/api/evtlog/users')
    ])
    tableOptions.value = t.data
    userOptions.value = u.data
  } catch (e) { /* ignore */ }
}

const formatTime = (val) => {
  if (!val) return ''
  const d = typeof val === 'string' ? new Date(val) : new Date(val)
  if (isNaN(d.getTime())) return String(val)
  const pad = (n, len = 2) => String(n).padStart(len, '0')
  return `${d.getFullYear()}-${pad(d.getMonth()+1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}.${pad(d.getMilliseconds(),3)}000`
}

const tagType = (code) => {
  if (!code) return ''
  const c = code.trim()
  if (c === 'Release') return 'success'
  if (c === 'Delete') return 'danger'
  if (c === 'Rollback') return 'warning'
  if (c === 'Login' || c === 'Logoff') return 'info'
  return ''
}

onMounted(() => {
  loadOptions()
  doSearch()
})
</script>

<style scoped>
.evtlog-view { display: flex; flex-direction: column; height: 100%; padding: 6px; }
.evtlog-filter { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; margin-bottom: 6px; padding: 6px 8px; background: var(--c-panel, #F7F8FA); border: 1px solid var(--c-border, #D0D5DC); }
.evtlog-filter :deep(.el-input__wrapper) { border-radius: 1px; }
.evtlog-filter :deep(.el-button) { border-radius: 1px; }
.evtlog-count { font-size: 11px; color: var(--c-text-secondary, #5C6B7A); margin-left: 8px; }
.evtlog-table { flex: 1; min-height: 0; overflow: hidden; }
.evtlog-table :deep(.el-table) { border: 1px solid var(--c-border, #D0D5DC); border-radius: 0 !important; }
.evtlog-table :deep(.el-table__header th) { background: #E8ECF2 !important; border-bottom: 2px solid var(--c-primary, #2B5CE6) !important; font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.3px; }
.evtlog-table :deep(.el-table__body td) { border-color: var(--c-border-light, #E2E6EC) !important; }
.evtlog-table :deep(.el-table .cell) { white-space: nowrap !important; overflow: hidden; text-overflow: ellipsis; padding: 0 4px !important; }
.evtlog-table :deep(.el-table__body tr:hover > td) { background: var(--c-row-selected, #E8EDF5) !important; }
</style>
