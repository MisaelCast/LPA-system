import axios, { AxiosError } from 'axios'
import type { AxiosRequestConfig } from 'axios'
import { useAuthStore } from '@/stores/auth'
import type { Token } from '@/types/auth'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL,
})

api.interceptors.request.use((config) => {
  const authStore = useAuthStore()
  const token = authStore.token
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

let refreshing: Promise<string> | null = null

async function refreshAccessToken(): Promise<string> {
  const authStore = useAuthStore()
  const refresh = authStore.refreshToken
  if (!refresh) {
    throw new Error('Sin refresh token.')
  }
  const response = await axios.post<Token>(
    `${import.meta.env.VITE_API_BASE_URL}/auth/refresh`,
    { refresh_token: refresh },
  )
  const data = response.data
  authStore.setTokens(data.access_token, data.refresh_token ?? null)
  return data.access_token
}

function isAuthPath(url?: string): boolean {
  if (!url) return false
  return (
    url.includes('/auth/login') || url.includes('/auth/refresh')
  )
}

function redirectToLogin() {
  const authStore = useAuthStore()
  authStore.clearToken()
  if (
    window.location.pathname !== '/login' &&
    !window.location.pathname.startsWith('/login')
  ) {
    const motivo = 'expired'
    window.location.href = `/login?motivo=${motivo}`
  }
}

api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const status = error.response?.status
    const originalRequest = error.config as
      | (AxiosRequestConfig & { _retry?: boolean })
      | undefined

    if (status === 401) {
      console.warn('Sesión inválida o expirada.')
      const authStore = useAuthStore()
      if (!originalRequest || originalRequest._retry || isAuthPath(originalRequest.url)) {
        if (!isAuthPath(originalRequest?.url)) {
          redirectToLogin()
        }
        return Promise.reject(error)
      }

      if (!authStore.refreshToken) {
        redirectToLogin()
        return Promise.reject(error)
      }

      originalRequest._retry = true
      try {
        if (!refreshing) {
          refreshing = refreshAccessToken().finally(() => {
            refreshing = null
          })
        }
        const newAccess = await refreshing
        originalRequest.headers = {
          ...(originalRequest.headers ?? {}),
          Authorization: `Bearer ${newAccess}`,
        }
        return api(originalRequest)
      } catch (refreshError) {
        redirectToLogin()
        return Promise.reject(refreshError)
      }
    }

    if (status === 403) {
      console.warn('No tiene permisos para realizar esta acción.')
    }
    return Promise.reject(error)
  },
)

export default api
