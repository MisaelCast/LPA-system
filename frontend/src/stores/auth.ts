import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { Usuario } from '@/types/auth'
import { obtenerUsuarioActual } from '@/services/auth.service'

const LOCAL_STORAGE_KEY = 'access_token'

export const useAuthStore = defineStore('auth', () => {
  const token = ref<string | null>(localStorage.getItem(LOCAL_STORAGE_KEY))
  const usuario = ref<Usuario | null>(null)

  const isAuthenticated = computed(() => token.value !== null)

  const isAdmin = computed(
    () => usuario.value?.rol_nombre === 'Administrador',
  )

  const isSupervisor = computed(
    () => usuario.value?.rol_nombre === 'Supervisor',
  )

  function setToken(value: string) {
    token.value = value
    localStorage.setItem(LOCAL_STORAGE_KEY, value)
  }

  function clearToken() {
    token.value = null
    usuario.value = null
    localStorage.removeItem(LOCAL_STORAGE_KEY)
  }

  async function cargarUsuario() {
    usuario.value = await obtenerUsuarioActual()
  }

  return { token, usuario, isAuthenticated, isAdmin, isSupervisor, setToken, clearToken, cargarUsuario }
})
