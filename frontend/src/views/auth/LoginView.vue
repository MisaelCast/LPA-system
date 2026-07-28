<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { login } from '@/services/auth.service'

const router = useRouter()
const authStore = useAuthStore()

const correo = ref('')
const contrasena = ref('')
const error = ref('')
const cargando = ref(false)

async function handleSubmit() {
  error.value = ''
  cargando.value = true

  try {
    const token = await login({
      correo: correo.value,
      contrasena: contrasena.value,
    })
    authStore.setToken(token.access_token)
    router.push('/dashboard')
  } catch (err: unknown) {
    if (err && typeof err === 'object' && 'response' in err) {
      const axiosErr = err as { response: { status: number; data?: { detail?: string } } }
      if (axiosErr.response.status === 401) {
        error.value = 'Correo o contraseña incorrectos.'
      } else if (axiosErr.response.status === 403) {
        error.value = axiosErr.response.data?.detail || 'Usuario inactivo.'
      } else {
        error.value = 'Error inesperado. Intente nuevamente.'
      }
    } else {
      error.value = 'No se pudo conectar con el servidor.'
    }
  } finally {
    cargando.value = false
  }
}
</script>

<template>
  <form @submit.prevent="handleSubmit">
    <h1>Iniciar Sesión</h1>

    <p v-if="error" role="alert">{{ error }}</p>

    <label>
      Correo
      <input v-model="correo" type="email" required autocomplete="email" />
    </label>

    <label>
      Contraseña
      <input v-model="contrasena" type="password" required autocomplete="current-password" />
    </label>

    <button type="submit" :disabled="cargando">
      {{ cargando ? 'Iniciando…' : 'Iniciar sesión' }}
    </button>
  </form>
</template>
