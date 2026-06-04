<template>
  <el-dialog
    v-model="visible"
    :title="'Search - ' + title"
    width="620px"
    :close-on-click-modal="false"
    :close-on-press-escape="false"
    @close="handleClose"
  >
    <!-- 状态过滤 -->
    <div class="search-section">
      <div class="section-title">状态</div>
      <el-radio-group v-model="searchStatus" class="status-group">
        <el-radio value="ALL">全部</el-radio>
        <el-radio value="EDIT">编辑中</el-radio>
        <el-radio value="EDITCOMP">编辑完成</el-radio>
        <el-radio value="RELEASE">已发布</el-radio>
        <el-radio value="LOCK">已锁定</el-radio>
      </el-radio-group>
    </div>

    <!-- 检索字段 (2列布局) -->
    <div class="search-section">
      <div class="section-title">检索条件</div>
      <div class="search-grid">
        <div
          v-for="field in searchFields"
          :key="field.fieldName"
          class="search-item"
        >
          <label class="search-label">{{ field.usTitle || field.jpTitle || field.fieldName }}</label>
          <el-input
            v-model="searchForm[field.fieldName]"
            size="small"
            :placeholder="field.usTitle || field.jpTitle || field.fieldName"
            clearable
            @keyup.enter="handleSearch"
          />
        </div>
      </div>
    </div>

    <template #footer>
      <div class="dialog-footer">
        <el-button @click="handleSearch" type="primary">检索</el-button>
        <el-button @click="handleClear">取消</el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, reactive, computed, watch } from 'vue'
import axios from 'axios'
import { ElMessage } from 'element-plus'

const props = defineProps({
  modelValue: { type: Boolean, default: false },
  tableId: { type: String, required: true }
})

const emit = defineEmits(['update:modelValue', 'search'])

const visible = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val)
})

const loading = ref(false)
const config = ref({ table: null, fields: [] })
const searchForm = reactive({})
const searchStatus = ref('ALL')

const title = computed(() => config.value.table?.usTitle || config.value.table?.jpTitle || props.tableId)

const searchFields = computed(() => {
  return config.value.fields.filter(f => f.isSearchItem === 'Y' && f.isDummy === 'N')
})

const fetchConfig = async () => {
  try {
    const res = await axios.get(`/api/meta/${props.tableId}`)
    config.value = res.data
    // Reset form
    searchFields.value.forEach(f => { searchForm[f.fieldName] = '' })
  } catch (err) {
    ElMessage.error('加载配置失败')
  }
}

const handleSearch = () => {
  // Build conditions from non-empty fields
  const conditions = {}
  searchFields.value.forEach(f => {
    const val = searchForm[f.fieldName]
    if (val && val.trim()) {
      conditions[f.fieldName] = val.trim()
    }
  })
  emit('search', { status: searchStatus.value, conditions })
  visible.value = false
}

const handleClear = () => {
  searchFields.value.forEach(f => { searchForm[f.fieldName] = '' })
  searchStatus.value = 'ALL'
  emit('search', { status: 'ALL', conditions: {} })
  visible.value = false
}

const handleClose = () => {
  // Treat close same as clear
  handleClear()
}

const load = async () => {
  if (props.modelValue && props.tableId) {
    loading.value = true
    await fetchConfig()
    searchStatus.value = 'ALL'
    searchFields.value.forEach(f => { searchForm[f.fieldName] = '' })
    loading.value = false
  }
}

watch(() => props.modelValue, load)
watch(() => props.tableId, () => { if (props.modelValue) load() })
</script>

<style scoped>
.search-section { margin-bottom: 12px; }
.section-title { font-weight: bold; font-size: 13px; margin-bottom: 8px; color: #333; }
.status-group { display: flex; flex-wrap: wrap; gap: 4px; }
.status-group :deep(.el-radio) { margin-right: 12px; }

.search-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px 16px;
}
.search-item { display: flex; align-items: center; gap: 8px; }
.search-label {
  width: 80px; text-align: right; font-size: 12px; color: #666;
  flex-shrink: 0; white-space: nowrap;
}

.dialog-footer { text-align: center; }
</style>
