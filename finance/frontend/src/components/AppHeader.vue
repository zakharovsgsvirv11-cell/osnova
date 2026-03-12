<template>
  <header class="app-header">
    <div class="header-brand">Финансовый трекер</div>
    <nav class="header-nav">
      <router-link to="/">Главная</router-link>
      <router-link to="/transactions">Транзакции</router-link>
      <router-link to="/statistics">Статистика</router-link>
      <router-link to="/project">Проект</router-link>
    </nav>
    <button class="btn-logout" @click="handleLogout">Выйти</button>
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
