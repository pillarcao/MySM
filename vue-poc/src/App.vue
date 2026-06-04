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
        <el-tooltip content="新增 (New)" placement="bottom"><el-button circle size="small" @click="toolbar.add()"><el-icon><Plus /></el-icon></el-button></el-tooltip>
        <el-tooltip content="编辑 (Update)" placement="bottom"><el-button circle size="small" @click="toolbar.update()" :disabled="!toolbar.hasSelection" :type="toolbar.isEditMode ? 'warning' : 'default'"><el-icon><Edit /></el-icon></el-button></el-tooltip>
        <el-tooltip content="保存 (Save)" placement="bottom"><el-button circle size="small" type="primary" @click="toolbar.save()" :disabled="!toolbar.isEditMode"><el-icon><Check /></el-icon></el-button></el-tooltip>
        <div class="toolbar-divider" />
        <el-tooltip content="编辑完成 (EditComp)" placement="bottom"><el-button circle size="small" type="warning" @click="toolbar.editComp()" :disabled="!toolbar.canEditComp"><el-icon><Finished /></el-icon></el-button></el-tooltip>
        <el-tooltip content="发布 (Release)" placement="bottom"><el-button circle size="small" type="success" @click="toolbar.release()" :disabled="!toolbar.canRelease"><el-icon><Promotion /></el-icon></el-button></el-tooltip>
        <div class="toolbar-divider" />
        <div class="toolbar-divider" />
        <el-tooltip content="复制 (Copy)" placement="bottom"><el-button circle size="small" @click="toolbar.copy()" :disabled="!toolbar.hasSelection"><el-icon><CopyDocument /></el-icon></el-button></el-tooltip>
        <el-tooltip content="粘贴 (Paste)" placement="bottom"><el-button circle size="small" @click="toolbar.paste()" :disabled="!toolbar.isEditMode"><el-icon><Document /></el-icon></el-button></el-tooltip>
        <el-tooltip content="查找 (Find)" placement="bottom"><el-button circle size="small" @click="toolbar.find()"><el-icon><Search /></el-icon></el-button></el-tooltip>
        <div class="toolbar-divider" />
        <el-tooltip content="回滚 (Rollback)" placement="bottom"><el-button circle size="small" @click="toolbar.rollback()" :disabled="!toolbar.hasSelection"><el-icon><Refresh /></el-icon></el-button></el-tooltip>
        <div class="toolbar-divider" />
        <el-tooltip content="删除 (Delete)" placement="bottom"><el-button circle size="small" type="danger" @click="toolbar.delete()" :disabled="!toolbar.hasSelection"><el-icon><Delete /></el-icon></el-button></el-tooltip>
        <el-tooltip content="撤销 (Undo)" placement="bottom"><el-button circle size="small" @click="toolbar.undo()"><el-icon><RefreshLeft /></el-icon></el-button></el-tooltip>
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
          <DynamicTableManager v-if="activeTabId" :key="activeTabId" :table-id="activeTabId" :drill-query="drillQueries[activeTabId] || {}" :show-search="!tabInitialized[activeTabId]" @row-select="onRowSelect" @records-change="onRecordsChange" @edit-state="onEditState" @searched="onTabSearched(activeTabId)" @cell-jump="onDrillDown" />
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
import { Plus, Edit, Check, Finished, Promotion, Delete, RefreshLeft, CopyDocument, Document, Search, Refresh } from '@element-plus/icons-vue'
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
  copy: () => {}, paste: () => {}, find: () => {}, rollback: () => {},
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
.top-header { display: flex; align-items: center; background: #001529; height: 32px !important; padding: 0 12px !important; flex-shrink: 0; box-sizing: border-box; }
.logo { color: #fff; font-size: 13px; font-weight: 600; white-space: nowrap; margin-right: 20px; }
.top-menu { flex: 1; border: none !important; min-width: 0; height: 32px; }
.top-menu :deep(.el-sub-menu__title) { color: rgba(255,255,255,0.8) !important; border-bottom: none !important; font-size: 13px; height: 32px !important; line-height: 32px !important; padding: 0 12px !important; }
.top-menu :deep(.el-sub-menu__title):hover { color: #fff !important; background: rgba(255,255,255,0.08) !important; }
.top-menu :deep(.el-menu-item) { color: rgba(255,255,255,0.8); font-size: 13px; height: 40px; line-height: 40px; }
.top-menu :deep(.el-menu-item):hover, .top-menu :deep(.el-menu-item.is-active) { color: #fff; background: #1890ff; }
.top-menu :deep(.el-menu--popup) { background: #001529; border: 1px solid rgba(255,255,255,0.1); }
.top-menu :deep(.el-menu--popup) { background: #001529; min-width: 160px; }
.top-menu :deep(.el-menu--popup .el-menu-item) { background: #001529; color: rgba(255,255,255,0.8); font-size: 13px; height: 36px; line-height: 36px; }
.top-menu :deep(.el-menu--popup .el-menu-item):hover { background: #1890ff; color: #fff; }
.top-menu :deep(.el-menu--popup .el-sub-menu__title) { color: rgba(255,255,255,0.8) !important; font-size: 13px; height: 36px; line-height: 36px; background: #001529 !important; }
.top-menu :deep(.el-menu--popup .el-sub-menu__title):hover { background: #1890ff !important; color: #fff !important; }
.logout-btn { margin-left: auto; height: 28px; font-size: 12px; flex-shrink: 0; }
.toolbar-strip { display: flex; align-items: center; gap: 4px; height: 30px; padding: 0 12px; background: #f5f5f5; border-bottom: 1px solid #e0e0e0; flex-shrink: 0; }
.toolbar-divider { width: 1px; height: 20px; background: #ccc; margin: 0 4px; }
.body-area { flex: 1; display: flex; overflow: hidden; margin: 0; }
.left-panel { width: 200px; background: #fafafa; border-right: 1px solid #e8e8e8; overflow-y: auto; flex-shrink: 0; max-height: 100%; }
.center-panel { flex: 1; display: flex; flex-direction: column; overflow: hidden; background: #f5f5f5; }
.right-panel { width: 280px; background: #fafafa; border-left: 1px solid #e8e8e8; overflow-y: auto; flex-shrink: 0; max-height: 100%; }
.tab-strip { display: flex; align-items: center; background: #e8e8e8; border-bottom: 1px solid #ddd; height: 30px; padding: 0 4px; flex-shrink: 0; overflow-x: auto; gap: 0; }
.tab-item { display: flex; align-items: center; gap: 3px; padding: 3px 10px; cursor: pointer; font-size: 12px; white-space: nowrap; color: #666; transition: all .15s; border-radius: 4px; }
.tab-item:hover { background: #ddd; color: #333; }
.tab-item.active { background: #fff; color: #1890ff; font-weight: 500; box-shadow: 0 1px 2px rgba(0,0,0,.06); }
.tab-close { margin-left: 6px; font-size: 14px; color: #aaa; line-height: 1; }
.tab-close:hover { color: #f5222d; }
.tab-close { margin-left: 6px; font-size: 14px; color: #999; } .tab-close:hover { color: #f00; }
.empty-center { flex: 1; display: flex; align-items: center; justify-content: center; color: #999; font-size: 14px; }
.right-panel { width: 300px; background: #fafafa; border-left: 1px solid #e8e8e8; overflow-y: auto; flex-shrink: 0; }
</style>
