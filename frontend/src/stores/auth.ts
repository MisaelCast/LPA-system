import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { Usuario } from '@/types/auth'
import { obtenerUsuarioActual } from '@/services/auth.service'

const ACCESS_TOKEN_KEY = 'access_token'
const REFRESH_TOKEN_KEY = 'refresh_token'

export const useAuthStore = defineStore('auth', () => {
  const token = ref<string | null>(localStorage.getItem(ACCESS_TOKEN_KEY))
  const refreshToken = ref<string | null>(
    localStorage.getItem(REFRESH_TOKEN_KEY),
  )
  const usuario = ref<Usuario | null>(null)

  const isAuthenticated = computed(
    () => token.value !== null,
  )

  const isAdmin = computed(
    () => usuario.value?.rol_nombre === 'Administrador',
  )

  const isSupervisor = computed(
    () => usuario.value?.rol_nombre === 'Supervisor',
  )

  const isGerente = computed(
    () => usuario.value?.rol_nombre === 'Gerente',
  )

  const isResponsable = computed(
    () => usuario.value?.rol_nombre === 'Responsable de Manufactura',
  )

  function setTokens(access: string, refresh?: string | null) {
    token.value = access
    localStorage.setItem(ACCESS_TOKEN_KEY, access)
    if (refresh) {
      refreshToken.value = refresh
      localStorage.setItem(REFRESH_TOKEN_KEY, refresh)
    }
  }

  function setAccessToken(access: string) {
    token.value = access
    localStorage.setItem(ACCESS_TOKEN_KEY, access)
  }

  function clearToken() {
    token.value = null
    refreshToken.value = null
    usuario.value = null
    localStorage.removeItem(ACCESS_TOKEN_KEY)
    localStorage.removeItem(REFRESH_TOKEN_KEY)
  }

  async function cargarUsuario() {
    usuario.value = await obtenerUsuarioActual()
  }

  return {
    token,
    refreshToken,
    usuario,
    isAuthenticated,
    isAdmin,
    isSupervisor,
    isGerente,
    isResponsable,
    setTokens,
    setAccessToken,
    clearToken,
    cargarUsuario,
  }
})
