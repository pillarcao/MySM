<template>
  <div class="login-container">
    <div class="login-box">
      <div class="login-header">
        <div class="login-title">SM SYSTEM</div>
        <div class="login-subtitle">Factory Modeling Platform</div>
      </div>
      <el-form :model="form" label-position="top" class="login-form">
        <el-form-item label="USER ID">
          <el-input v-model="form.userId" placeholder="Enter user ID" />
        </el-form-item>
        <el-form-item label="PASSWORD">
          <el-input v-model="form.passwd" type="password" placeholder="Enter password" @keyup.enter="handleLogin" />
        </el-form-item>
        <el-button type="primary" class="login-btn" @click="handleLogin" :loading="loading">LOGIN</el-button>
      </el-form>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import axios from 'axios'
import { ElMessage } from 'element-plus'

const emit = defineEmits(['login-success'])

const form = ref({ userId: '', passwd: '' })
const loading = ref(false)

const handleLogin = async () => {
  if (!form.value.userId || !form.value.passwd) {
    ElMessage.warning('请输入用户名和密码')
    return
  }
  loading.value = true
  try {
    const res = await axios.post('/api/auth/login', {
      userId: form.value.userId,
      passwd: form.value.passwd
    })
    const token = res.data.token
    localStorage.setItem('sm_token', token)
    axios.defaults.headers.common['Authorization'] = 'Bearer ' + token
    ElMessage.success('登录成功')
    emit('login-success')
  } catch (err) {
    ElMessage.error('登录失败: ' + (err.response?.data?.error || err.message))
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-container {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100vh;
  background: #0D1B2A;
  background-image:
    linear-gradient(rgba(43,92,230,0.03) 1px, transparent 1px),
    linear-gradient(90deg, rgba(43,92,230,0.03) 1px, transparent 1px);
  background-size: 40px 40px;
}
.login-box {
  width: 360px;
  background: #fff;
  border: 1px solid #D0D5DC;
  box-shadow: 0 4px 24px rgba(0,0,0,0.3);
}
.login-header {
  background: #0D1B2A;
  padding: 24px 28px 18px;
  border-bottom: 3px solid #2B5CE6;
}
.login-title {
  color: #fff;
  font-size: 20px;
  font-weight: 700;
  letter-spacing: 3px;
}
.login-subtitle {
  color: rgba(255,255,255,0.5);
  font-size: 11px;
  margin-top: 4px;
  letter-spacing: 1px;
  text-transform: uppercase;
}
.login-form {
  padding: 24px 28px;
}
.login-form :deep(.el-form-item__label) {
  font-size: 11px;
  font-weight: 700;
  color: #5C6B7A;
  letter-spacing: 0.5px;
}
.login-form :deep(.el-input__wrapper) {
  border-radius: 1px;
  box-shadow: 0 0 0 1px #D0D5DC inset;
}
.login-form :deep(.el-input__wrapper:hover) {
  box-shadow: 0 0 0 1px #2B5CE6 inset;
}
.login-btn {
  width: 100%;
  margin-top: 8px;
  border-radius: 1px;
  font-weight: 700;
  letter-spacing: 2px;
  height: 36px;
  background: #2B5CE6;
  border-color: #2B5CE6;
}
.login-btn:hover {
  background: #1E44B3;
  border-color: #1E44B3;
}
</style>
