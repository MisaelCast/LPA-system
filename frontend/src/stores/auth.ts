import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

const LOCAL_STORAGE_KEY = 'access_token'

export const useAuthStore = defineStore('auth', () => {
  const token = ref<string | null>(localStorage.getItem(LOCAL_STORAGE_KEY))

  const isAuthenticated = computed(() => token.value !== null)

  function setToken(value: string) {
    token.value = value
    localStorage.setItem(LOCAL_STORAGE_KEY, value)
  }

  function clearToken() {
    token.value = null
    localStorage.removeItem(LOCAL_STORAGE_KEY)
  }

  return { token, isAuthenticated, setToken, clearToken }
})
