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
  if (typeof val === 'string') return val.substring(0, 19)
  return new Date(val).toISOString().substring(0, 19).replace('T', ' ')
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
.evtlog-view { display: flex; flex-direction: column; height: 100%; padding: 8px; }
.evtlog-filter { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; margin-bottom: 8px; }
.evtlog-count { font-size: 12px; color: #999; margin-left: 8px; }
.evtlog-table { flex: 1; min-height: 0; overflow: hidden; }
</style>
