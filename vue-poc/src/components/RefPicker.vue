<template>
  <el-dialog
    v-model="dialogVisible"
    :title="title"
    width="700px"
    @close="handleClose"
  >
    <div v-loading="loading">
      <!-- 查询栏 -->
      <el-form :inline="true" :model="queryForm" class="query-bar">
        <el-form-item
          v-for="field in queryFields"
          :key="field.fieldName"
          :label="field.jpTitle"
        >
          <el-input v-model="queryForm[field.fieldName]" :placeholder="field.jpTitle" clearable size="small" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" size="small" @click="handleSearch">查询</el-button>
          <el-button size="small" @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>

      <!-- 数据列表 -->
      <el-table
        :data="list"
        border
        highlight-current-row
        @current-change="handleRowChange"
        style="width: 100%"
      >
        <el-table-column
          v-for="col in displayColumns"
          :key="col.fieldName"
          :prop="col.fieldName"
          :label="col.jpTitle"
          :width="col.dbLength * 8 + 40"
        />
      </el-table>
    </div>

    <template #footer>
      <el-button @click="handleClose">取消</el-button>
      <el-button type="primary" :disabled="!selectedRow" @click="handleConfirm">确认</el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import axios from 'axios'
import { ElMessage } from 'element-plus'

const props = defineProps({
  modelValue: { type: Boolean, default: false },
  tableId: { type: String, required: true },
  refField: { type: String, required: true }
})

const emit = defineEmits(['update:modelValue', 'select'])

const dialogVisible = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val)
})

const loading = ref(false)
const config = ref({ table: null, fields: [] })
const list = ref([])
const queryForm = ref({})
const selectedRow = ref(null)

const title = computed(() => {
  return (config.value.table?.jpTitle || props.tableId) + ' 参照'
})

const displayColumns = computed(() => {
  return config.value.fields.filter(f => f.isSearchItem === 'Y' && f.isDummy === 'N')
})

const queryFields = computed(() => {
  return config.value.fields.filter(f => f.isSearchItem === 'Y' && f.isDummy === 'N').slice(0, 3)
})

const fetchConfig = async () => {
  try {
    const res = await axios.get(`/api/meta/${props.tableId}`)
    config.value = res.data
  } catch (err) {
    ElMessage.error('加载参照配置失败: ' + err.message)
  }
}

const fetchList = async () => {
  try {
    const res = await axios.get(`/api/dynamic/${props.tableId}/list`)
    list.value = res.data
  } catch (err) {
    ElMessage.error('加载参照数据失败: ' + err.message)
  }
}

const handleSearch = async () => {
  try {
    const res = await axios.post(`/api/dynamic/${props.tableId}/search`, queryForm.value)
    list.value = res.data
  } catch (err) {
    ElMessage.error('查询失败: ' + (err.response?.data?.error || err.message))
  }
}

const handleReset = () => {
  queryForm.value = {}
  fetchList()
}

const handleRowChange = (row) => {
  selectedRow.value = row
}

const handleConfirm = () => {
  if (selectedRow.value) {
    emit('select', selectedRow.value[props.refField])
    dialogVisible.value = false
  }
}

const handleClose = () => {
  selectedRow.value = null
  dialogVisible.value = false
}

const load = async () => {
  if (!props.modelValue) return
  loading.value = true
  selectedRow.value = null
  queryForm.value = {}
  await fetchConfig()
  await fetchList()
  loading.value = false
}

watch(() => props.modelValue, load)
</script>

<style scoped>
.query-bar {
  margin-bottom: 12px;
}
</style>
