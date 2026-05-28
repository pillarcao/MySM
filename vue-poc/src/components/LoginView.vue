<template>
  <div class="login-container">
    <el-card class="login-box">
      <template #header>
        <h2>SM 系统登录</h2>
      </template>
      <el-form :model="form" label-width="80px">
        <el-form-item label="用户名">
          <el-input v-model="form.userId" placeholder="请输入用户ID" />
        </el-form-item>
        <el-form-item label="密码">
          <el-input v-model="form.passwd" type="password" placeholder="请输入密码" @keyup.enter="handleLogin" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleLogin" :loading="loading">登录</el-button>
        </el-form-item>
      </el-form>
    </el-card>
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
  background: #f5f7fa;
}
.login-box {
  width: 400px;
}
</style>
