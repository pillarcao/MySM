<template>
  <div class="sm-poc">
    <LoginView v-if="!isLoggedIn" @login-success="onLoginSuccess" />
    <div v-else class="layout">
      <el-header class="top-header">
        <span class="logo">SM System</span>
        <el-menu mode="horizontal" class="top-menu" background-color="#001529" text-color="rgba(255,255,255,0.7)" @select="onMenuSelect" :key="'menu_' + tables.length">
          <el-sub-menu index="File">
            <template #title>File</template>
            <el-sub-menu v-for="grp in menuFlat" :key="grp.label" :index="grp.label">
              <template #title>{{ grp.label }}</template>
              <el-menu-item v-for="t in grp.children" :key="t.tableId" :index="t.tableId">{{ t.label }}</el-menu-item>
            </el-sub-menu>
          </el-sub-menu>
        </el-menu>
        <el-button size="small" class="logout-btn" @click="handleLogout">退出</el-button>
      </el-header>

      <div class="toolbar-strip">
        <el-button size="small" @click="toolbar.add()">新增</el-button>
        <el-button size="small" @click="toolbar.update()" :disabled="!toolbar.hasSelection">Update</el-button>
        <el-button size="small" type="primary" @click="toolbar.save()" :disabled="!toolbar.isEditMode">保存</el-button>
        <el-button size="small" type="warning" @click="toolbar.editComp()" :disabled="!toolbar.canEditComp">编辑完成</el-button>
        <el-button size="small" type="success" @click="toolbar.release()" :disabled="!toolbar.canRelease">Release</el-button>
        <el-button size="small" type="danger" @click="toolbar.delete()" :disabled="!toolbar.hasSelection">删除</el-button>
        <el-button size="small" @click="toolbar.undo()">Undo</el-button>
      </div>

      <div class="body-area">
        <div class="left-panel">
          <RecordList :table-id="activeTabId" :records="recordKeys" @select="onRecordSelect" />
        </div>
        <div class="center-panel">
          <div class="tab-strip" v-if="openTabs.length > 0">
            <div v-for="tab in openTabs" :key="tab.tableId" class="tab-item" :class="{ active: activeTabId === tab.tableId }" @click="switchTab(tab.tableId)">
              <span>{{ tab.title }}</span><span class="tab-close" @click.stop="closeTab(tab.tableId)">×</span>
            </div>
          </div>
          <DynamicTableManager v-if="activeTabId" :key="activeTabId" :table-id="activeTabId" :drill-query="drillQueries[activeTabId] || {}" :show-search="!tabInitialized[activeTabId]" @row-select="onRowSelect" @records-change="onRecordsChange" @edit-state="onEditState" @searched="onTabSearched(activeTabId)" />
          <div v-else class="empty-center">Select a table from the File menu</div>
        </div>
        <div class="right-panel">
          <RecordDetail :table-id="activeTabId" :record="selectedRecord" :fields="currentFields" :is-new="isNewRecord" @drill-down="onDrillDown" />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed, provide, reactive } from 'vue'
import axios from 'axios'
import { ElMessage } from 'element-plus'
import LoginView from './components/LoginView.vue'
import RecordDetail from './components/RecordDetail.vue'
import RecordList from './components/RecordList.vue'
import DynamicTableManager from './components/DynamicTableManager.vue'

const isLoggedIn = ref(false)
const selectedRecord = ref(null)
const currentFields = ref([])
const refreshKey = ref(0)
const isNewRecord = ref(false)
const recordKeys = ref([])
const tables = ref([])
const openTabs = ref([])
const activeTabId = ref('')
const drillQueries = ref({})
const tabInitialized = reactive({})

const onTabSearched = (tableId) => { tabInitialized[tableId] = true }

const toolbar = reactive({
  hasSelection: false, canEditComp: false, canRelease: false, isEditMode: false,
  add: () => {}, update: () => {}, editComp: () => {}, release: () => {}, save: () => {}, delete: () => {}, undo: () => {},
})
provide('toolbar', toolbar)

const menuFlat = computed(() => {
  const groups = {}
  ;(tables.value || []).forEach(t => {
    const g = t.menuGroup || 'Others'
    if (!groups[g]) groups[g] = []
    groups[g].push({ label: t.usTitle || t.jpTitle || t.tableId.replace('TBLID_B',''), tableId: t.tableId })
  })
  const order = ['Route','Product','Measurement','ProcessData','Equipment','Stocker','Cassette','User','Stage','Compile','Others']
  return order.filter(g => groups[g]).map(g => ({ label: g, children: groups[g] }))
})

const fetchTables = async () => {
  try {
    tables.value = (await axios.get('/api/meta/tables')).data
  } catch(e) {
    console.error('fetchTables failed:', e)
    if (e.response && e.response.status === 403) {
      ElMessage.error('登录已过期，请重新登录')
      handleLogout()
    } else {
      ElMessage.error('加载表列表失败')
    }
  }
}
const onLoginSuccess = () => { isLoggedIn.value = true; fetchTables().then(() => { if (tables.value[0]) { const t = tables.value[0]; openTable(t.tableId, t.usTitle || t.jpTitle || t.tableId) } }) }
const handleLogout = () => { localStorage.removeItem('sm_token'); delete axios.defaults.headers.common['Authorization']; isLoggedIn.value = false }
const onRowSelect = (row, fields, tableId) => { selectedRecord.value = row; currentFields.value = fields || [] }
const onRecordsChange = (keys) => { recordKeys.value = keys || [] }
const onRecordSelect = () => {}
const onEditState = (state) => { isNewRecord.value = state.isNewRow }
const onDrillDown = ({ tableId, label, query }) => { openTable(tableId, label); drillQueries.value[tableId] = query }

const openTable = (tableId, title) => {
  if (!openTabs.value.find(t => t.tableId === tableId)) openTabs.value.push({ tableId, title })
  activeTabId.value = tableId
}
const switchTab = (id) => { activeTabId.value = id }
const closeTab = (id) => {
  openTabs.value = openTabs.value.filter(t => t.tableId !== id)
  delete drillQueries.value[id]
  if (activeTabId.value === id) activeTabId.value = openTabs.value.length > 0 ? openTabs.value[openTabs.value.length-1].tableId : ''
}
const onMenuSelect = (tableId) => { if (tableId && tables.value.find(t => t.tableId === tableId)) { const t = tables.value.find(x => x.tableId === tableId); openTable(tableId, t.usTitle || t.jpTitle || tableId) } }

onMounted(() => {
  const token = localStorage.getItem('sm_token')
  if (token) { axios.defaults.headers.common['Authorization'] = 'Bearer ' + token; isLoggedIn.value = true; fetchTables().then(() => { if (tables.value[0]) openTable(tables.value[0].tableId, tables.value[0].usTitle || tables.value[0].jpTitle || tables.value[0].tableId) }) }
})
</script>

<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
.sm-poc { height: 100vh; display: flex; flex-direction: column; }
.top-header { display: flex; align-items: center; background: #001529; height: 50px; padding: 0 16px; flex-shrink: 0; }
.logo { color: #fff; font-size: 16px; font-weight: bold; margin-right: 20px; white-space: nowrap; }
.top-menu { flex: 1; border: none; }
.top-menu .el-sub-menu .el-sub-menu__title { color: rgba(255,255,255,0.7); border-bottom: none; }
.top-menu .el-sub-menu .el-sub-menu__title:hover { color: #fff; background: rgba(255,255,255,0.1); }
.top-menu .el-menu-item { color: rgba(255,255,255,0.7); }
.top-menu .el-menu-item:hover, .top-menu .el-menu-item.is-active { color: #fff; background: #1890ff; }
.logout-btn { margin-left: auto; }
.toolbar-strip { display: flex; gap: 4px; padding: 4px 16px; background: #f0f2f5; border-bottom: 1px solid #d9d9d9; flex-shrink: 0; }
.body-area { flex: 1; display: flex; overflow: hidden; }
.left-panel { width: 200px; background: #fafafa; border-right: 1px solid #e8e8e8; overflow-y: auto; flex-shrink: 0; }
.center-panel { flex: 1; display: flex; flex-direction: column; overflow: hidden; background: #fff; }
.tab-strip { display: flex; background: #e8e8e8; border-bottom: 1px solid #d9d9d9; padding: 0 4px; flex-shrink: 0; overflow-x: auto; }
.tab-item { display: flex; align-items: center; padding: 4px 10px; cursor: pointer; font-size: 12px; border-right: 1px solid #d9d9d9; white-space: nowrap; }
.tab-item:hover { background: #f0f0f0; } .tab-item.active { background: #fff; border-bottom: 2px solid #1890ff; }
.tab-close { margin-left: 6px; font-size: 14px; color: #999; } .tab-close:hover { color: #f00; }
.empty-center { flex: 1; display: flex; align-items: center; justify-content: center; color: #999; font-size: 14px; }
.right-panel { width: 300px; background: #fafafa; border-left: 1px solid #e8e8e8; overflow-y: auto; flex-shrink: 0; }
</style>
