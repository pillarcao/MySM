<template>
  <el-dialog v-model="visible" title="Copy All Objects in Route" width="480px" :close-on-click-modal="false">
    <el-form label-width="140px" size="small">
      <el-form-item label="Source Route ID">
        <span class="form-text">{{ routeId }} / {{ routeVer }}</span>
      </el-form-item>
      <el-form-item label="Target Route ID" required>
        <el-input v-model="newRouteId" placeholder="Input target Route ID" maxlength="12" />
      </el-form-item>
    </el-form>
    <div class="copy-hint">
      Route batch copy will process related tables: Route, Route Module, Route Connection.
    </div>
    <template #footer>
      <el-button @click="handleConfirm" type="primary" :disabled="!newRouteId.trim()">Copy</el-button>
      <el-button @click="handleCancel">Cancel</el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, computed, watch } from 'vue'

const props = defineProps({
  modelValue: { type: Boolean, default: false },
  routeId: { type: String, default: '' },
  routeVer: { type: String, default: '' }
})

const emit = defineEmits(['update:modelValue', 'confirm'])

const visible = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val)
})

const newRouteId = ref('')

watch(visible, (val) => { if (val) newRouteId.value = '' })

const handleConfirm = () => {
  if (!newRouteId.value.trim()) return
  emit('confirm', newRouteId.value.trim())
  visible.value = false
}

const handleCancel = () => {
  visible.value = false
}
</script>

<style scoped>
.form-text { color: #333; font-weight: 500; }
.copy-hint { font-size: 12px; color: #999; padding: 0 0 12px 12px; }
</style>
