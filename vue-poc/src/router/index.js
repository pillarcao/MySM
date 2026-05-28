import { createRouter, createWebHashHistory } from 'vue-router'
import DynamicTableManager from '../components/DynamicTableManager.vue'

const routes = [
  { path: '/', redirect: '/table/TBLID_BCODE' },
  { path: '/table/:tableId', component: DynamicTableManager, props: true }
]

const router = createRouter({
  history: createWebHashHistory(),
  routes
})

export default router
