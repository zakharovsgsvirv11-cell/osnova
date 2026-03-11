import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { authApi } from '../api/auth'

export const useAuthStore = defineStore('auth', () => {
  const user = ref(null)
  const accessToken = ref(null)

  const isAuthenticated = computed(() => !!accessToken.value)

  async function login(username, password) {
    const data = await authApi.login(username, password)
    accessToken.value = data.access_token
    await fetchUser()
  }

  async function fetchUser() {
    user.value = await authApi.me()
  }

  async function tryRefresh() {
    try {
      const data = await authApi.refresh()
      accessToken.value = data.access_token
      await fetchUser()
    } catch {
      accessToken.value = null
      user.value = null
    }
  }

  async function logout() {
    await authApi.logout()
    accessToken.value = null
    user.value = null
  }

  return { user, accessToken, isAuthenticated, login, logout, tryRefresh }
})
