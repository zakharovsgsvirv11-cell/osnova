<template>
  <header class="app-header">
    <div class="header-brand">Finance Tracker</div>
    <nav class="header-nav">
      <router-link to="/">Dashboard</router-link>
      <router-link to="/transactions">Transactions</router-link>
      <router-link to="/statistics">Statistics</router-link>
      <router-link to="/project">Project</router-link>
    </nav>
    <button class="btn-logout" @click="handleLogout">Logout</button>
  </header>
</template>

<script setup>
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const router = useRouter()
const authStore = useAuthStore()

async function handleLogout() {
  await authStore.logout()
  router.push('/login')
}
</script>
