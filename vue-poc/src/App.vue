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
          <el-menu-item index="__EVTLOG__">Logging</el-menu-item>
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
        <template v-if="viewMode === 'evtlog'">
          <div class="center-panel" style="width: 100%;">
            <EventLogView />
          </div>
        </template>
        <template v-else>
          <div class="left-panel" :style="{ width: leftWidth + 'px' }">
            <RecordList :table-id="activeTabId" :records="recordKeys" @select="onRecordSelect" @group-filter="onGroupFilter" />
          </div>
          <div class="splitter" @mousedown="startResize('left', $event)"></div>
          <div class="center-panel">
            <div class="tab-strip" v-if="openTabs.length > 0">
              <div v-for="tab in openTabs" :key="tab.tableId" class="tab-item" :class="{ active: activeTabId === tab.tableId }" @click="switchTab(tab.tableId)">
                <span>{{ tab.title }}</span><span class="tab-close" @click.stop="closeTab(tab.tableId)">×</span>
              </div>
            </div>
            <DynamicTableManager v-if="activeTabId" :key="activeTabId" :table-id="activeTabId" :drill-query="drillQueries[activeTabId] || {}" :show-search="!tabInitialized[activeTabId]" @row-select="onRowSelect" @records-change="onRecordsChange" @edit-state="onEditState" @searched="onTabSearched(activeTabId)" @cell-jump="onDrillDown" />
            <div v-else class="empty-center">Select a table from the File menu</div>
          </div>
          <div class="splitter" @mousedown="startResize('right', $event)"></div>
          <div class="right-panel" :style="{ width: rightWidth + 'px' }">
            <RecordDetail :table-id="activeTabId" :record="selectedRecord" :fields="currentFields" :is-new="isNewRecord" @drill-down="onDrillDown" />
          </div>
        </template>
      </div>
      <div class="status-bar">
        <span class="status-item">USER: {{ currentUser }}</span>
        <span class="status-item">| ENV: {{ envInfo.env }}</span>
        <span class="status-spacer"></span>
        <span class="status-item">SM System v{{ envInfo.version }}</span>
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
import EventLogView from './components/EventLogView.vue'

const isLoggedIn = ref(false)
const viewMode = ref('table')
const leftWidth = ref(200)
const rightWidth = ref(300)

const startResize = (side, e) => {
  e.preventDefault()
  const startX = e.clientX
  const startLeft = leftWidth.value
  const startRight = rightWidth.value
  const onMove = (ev) => {
    const dx = ev.clientX - startX
    if (side === 'left') {
      leftWidth.value = Math.max(100, Math.min(500, startLeft + dx))
    } else {
      rightWidth.value = Math.max(100, Math.min(600, startRight - dx))
    }
  }
  const onUp = () => {
    document.removeEventListener('mousemove', onMove)
    document.removeEventListener('mouseup', onUp)
    document.body.style.cursor = ''
    document.body.style.userSelect = ''
  }
  document.body.style.cursor = 'col-resize'
  document.body.style.userSelect = 'none'
  document.addEventListener('mousemove', onMove)
  document.addEventListener('mouseup', onUp)
}
const currentUser = ref('')
const envInfo = ref({ env: '', dbUrl: '', version: '' })
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
const selectedLeftKey = ref(null)
provide('toolbar', toolbar)
provide('selectedLeftKey', selectedLeftKey)

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

const activeTabTitle = computed(() => {
  const tab = openTabs.value.find(t => t.tableId === activeTabId.value)
  return tab ? tab.title : ''
})
const selectedKeyStr = computed(() => {
  if (!selectedRecord.value || !currentFields.value.length) return ''
  const keys = currentFields.value.filter(f => f.isKey === 'Y' && f.fieldName !== 'REL_FLG')
  return keys.map(f => (selectedRecord.value[f.fieldName] || '').toString().trim()).join(' | ')
})

const fetchEnv = async () => {
  try { envInfo.value = (await axios.get('/api/meta/env')).data } catch(e) {}
}

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
const onLoginSuccess = () => {
  isLoggedIn.value = true
  try { currentUser.value = JSON.parse(atob(localStorage.getItem('sm_token').split('.')[1])).sub } catch(e) { currentUser.value = '' }
  fetchEnv()
  fetchTables().then(() => { if (tables.value[0]) { const t = tables.value[0]; openTable(t.tableId, t.usTitle || t.jpTitle || t.tableId) } })
}
const handleLogout = async () => {
  try { await axios.post('/api/auth/logout') } catch(e) { /* ignore */ }
  localStorage.removeItem('sm_token'); delete axios.defaults.headers.common['Authorization']; isLoggedIn.value = false; viewMode.value = 'table'
}
const onRowSelect = (row, fields, tableId) => { selectedRecord.value = row; currentFields.value = fields || [] }
const onRecordsChange = (keys) => { recordKeys.value = keys || [] }
const onRecordSelect = (rec) => {
  selectedLeftKey.value = rec
  selectedRecord.value = rec
  // Update currentFields if available
  if (rec && currentFields.value.length === 0) {
    axios.get('/api/meta/' + activeTabId.value).then(r => { currentFields.value = r.data.fields || [] }).catch(() => {})
  }
}
const onGroupFilter = ({ field, value, record }) => {
  if (record) {
    // Leaf click: filter by all key-value pairs from the record (exclude internal fields)
    const query = {}
    const skipFields = ['REL_FLG','COMP_FLG','CRE_DATE','CRE_USER','OWNER','OWNERG','PERMISSION','LOCK_USER','LOCK_TIME','COMMENT']
    for (const k of Object.keys(record)) {
      if (k.startsWith('LAST_')) continue
      if (skipFields.includes(k)) continue
      const v = record[k]
      if (v != null && String(v).trim()) {
        // Only include fields that look like key/identifying fields
        if (currentFields.value.length > 0) {
          const fieldDef = currentFields.value.find(f => f.fieldName === k)
          if (fieldDef && fieldDef.isKey === 'Y') {
            query[k] = String(v).trim()
          }
        }
      }
    }
    drillQueries.value[activeTabId.value] = Object.keys(query).length > 0 ? query : { [field]: value }
  } else if (field) {
    drillQueries.value[activeTabId.value] = { [field]: value }
  }
}
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
const onMenuSelect = (index) => {
  if (index === '__EVTLOG__') { viewMode.value = 'evtlog'; return }
  viewMode.value = 'table'
  if (index && tables.value.find(t => t.tableId === index)) { const t = tables.value.find(x => x.tableId === index); openTable(index, t.usTitle || t.jpTitle || index) }
}

onMounted(() => {
  const token = localStorage.getItem('sm_token')
  if (token) {
    axios.defaults.headers.common['Authorization'] = 'Bearer ' + token
    isLoggedIn.value = true
    try { currentUser.value = JSON.parse(atob(token.split('.')[1])).sub } catch(e) {}
    fetchEnv()
    fetchTables().then(() => { if (tables.value[0]) openTable(tables.value[0].tableId, tables.value[0].usTitle || tables.value[0].jpTitle || tables.value[0].tableId) })
  }
})
</script>

<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
:root {
  --c-primary: #2B5CE6;
  --c-primary-dark: #1E44B3;
  --c-header: #0D1B2A;
  --c-bg: #F0F2F5;
  --c-panel: #F7F8FA;
  --c-border: #D0D5DC;
  --c-border-light: #E2E6EC;
  --c-text: #1A2233;
  --c-text-secondary: #5C6B7A;
  --c-row-selected: #E8EDF5;
  --c-row-edit: #FFFFFF;
  --c-row-editcomp: #FFF8E1;
  --c-row-released: #E3F2E8;
  --c-danger: #D63031;
}
.sm-poc { height: 100vh; display: flex; flex-direction: column; font-family: -apple-system, 'Segoe UI', Roboto, 'Helvetica Neue', monospace; }
.top-header { display: flex; align-items: center; background: var(--c-header); height: 34px !important; padding: 0 12px !important; flex-shrink: 0; box-sizing: border-box; }
.logo { color: #fff; font-size: 13px; font-weight: 700; white-space: nowrap; margin-right: 24px; letter-spacing: 1px; text-transform: uppercase; }
.top-menu { flex: 1; border: none !important; min-width: 0; height: 34px; }
.top-menu :deep(.el-sub-menu__title) { color: rgba(255,255,255,0.75) !important; border-bottom: none !important; font-size: 12px; height: 34px !important; line-height: 34px !important; padding: 0 14px !important; letter-spacing: 0.3px; }
.top-menu :deep(.el-sub-menu__title):hover { color: #fff !important; background: rgba(43,92,230,0.3) !important; }
.top-menu :deep(.el-menu-item) { color: rgba(255,255,255,0.75); font-size: 12px; height: 34px; line-height: 34px; }
.top-menu :deep(.el-menu-item):hover, .top-menu :deep(.el-menu-item.is-active) { color: #fff; background: var(--c-primary); }
.top-menu :deep(.el-menu--popup) { background: var(--c-header); border: 1px solid rgba(255,255,255,0.12); border-radius: 0 !important; }
.top-menu :deep(.el-menu--popup) { background: var(--c-header); min-width: 160px; }
.top-menu :deep(.el-menu--popup .el-menu-item) { background: var(--c-header); color: rgba(255,255,255,0.75); font-size: 12px; height: 32px; line-height: 32px; border-radius: 0; }
.top-menu :deep(.el-menu--popup .el-menu-item):hover { background: var(--c-primary); color: #fff; }
.top-menu :deep(.el-menu--popup .el-sub-menu__title) { color: rgba(255,255,255,0.75) !important; font-size: 12px; height: 32px; line-height: 32px; background: var(--c-header) !important; }
.top-menu :deep(.el-menu--popup .el-sub-menu__title):hover { background: var(--c-primary) !important; color: #fff !important; }
.logout-btn { margin-left: auto; height: 24px; font-size: 11px; flex-shrink: 0; border-radius: 1px; }
.toolbar-strip { display: flex; align-items: center; gap: 3px; height: 32px; padding: 0 12px; background: var(--c-panel); border-bottom: 2px solid var(--c-primary); flex-shrink: 0; }
.toolbar-divider { width: 1px; height: 18px; background: var(--c-border); margin: 0 8px; }
.body-area { flex: 1; display: flex; overflow: hidden; margin: 0; min-height: 0; }
.left-panel { height: calc(100vh - 88px); background: var(--c-panel); overflow-y: auto; flex-shrink: 0; }
.center-panel { flex: 1; display: flex; flex-direction: column; overflow: hidden; background: var(--c-bg); min-height: 0; }
.center-panel > :last-child { flex: 1; min-height: 0; overflow: hidden; }
.right-panel { height: calc(100vh - 88px); background: var(--c-panel); overflow-y: auto; flex-shrink: 0; }
.splitter { width: 4px; height: calc(100vh - 88px); background: var(--c-border); cursor: col-resize; flex-shrink: 0; transition: background .15s; }
.splitter:hover { background: var(--c-primary); }
.status-bar { display: flex; align-items: center; height: 22px; padding: 0 12px; background: var(--c-header); color: rgba(255,255,255,0.7); font-size: 11px; flex-shrink: 0; gap: 16px; border-top: 1px solid rgba(255,255,255,0.1); }
.status-item { white-space: nowrap; }
.status-spacer { flex: 1; }
.tab-strip { display: flex; align-items: stretch; background: var(--c-border-light); border-bottom: 1px solid var(--c-border); height: 28px; padding: 0; flex-shrink: 0; overflow-x: auto; gap: 0; }
.tab-item { display: flex; align-items: center; gap: 3px; padding: 0 12px; cursor: pointer; font-size: 11px; white-space: nowrap; color: var(--c-text-secondary); transition: all .1s; border-right: 1px solid var(--c-border); border-bottom: 2px solid transparent; }
.tab-item:hover { background: #fff; color: var(--c-text); }
.tab-item.active { background: #fff; color: var(--c-primary); font-weight: 600; border-bottom: 2px solid var(--c-primary); }
.tab-close { margin-left: 6px; font-size: 13px; color: #aaa; line-height: 1; }
.tab-close:hover { color: var(--c-danger); }
.empty-center { flex: 1; display: flex; align-items: center; justify-content: center; color: var(--c-text-secondary); font-size: 13px; }
</style>
