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
  <div class="login-page">
    <form class="login-card" @submit.prevent="handleSubmit">
      <h1>LPA System</h1>
      <p class="subtitle">Iniciar Sesión</p>

      <div v-if="error" class="alert" role="alert">{{ error }}</div>

      <div class="field">
        <label for="correo">Correo</label>
        <input
          id="correo"
          v-model="correo"
          type="email"
          required
          autocomplete="email"
        />
      </div>

      <div class="field">
        <label for="contrasena">Contraseña</label>
        <input
          id="contrasena"
          v-model="contrasena"
          type="password"
          required
          autocomplete="current-password"
        />
      </div>

      <button class="btn-primary" type="submit" :disabled="cargando">
        {{ cargando ? 'Iniciando…' : 'Iniciar sesión' }}
      </button>
    </form>
  </div>
</template>

<style scoped>
.login-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f1f5f9;
}

.login-card {
  background: #fff;
  padding: 2.5rem 2rem;
  border-radius: 0.5rem;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  width: 100%;
  max-width: 400px;
}

h1 {
  margin: 0 0 0.25rem;
  font-size: 1.5rem;
  color: #1e293b;
  text-align: center;
}

.subtitle {
  margin: 0 0 1.5rem;
  color: #64748b;
  font-size: 0.875rem;
  text-align: center;
}

.alert {
  background: #fef2f2;
  color: #dc2626;
  padding: 0.625rem 0.75rem;
  border-radius: 0.375rem;
  margin-bottom: 1rem;
  font-size: 0.875rem;
}

.field {
  margin-bottom: 1rem;
}

.field label {
  display: block;
  margin-bottom: 0.25rem;
  font-size: 0.875rem;
  color: #334155;
}

.field input {
  width: 100%;
  padding: 0.5rem 0.75rem;
  border: 1px solid #e2e8f0;
  border-radius: 0.375rem;
  font-size: 0.875rem;
  box-sizing: border-box;
}

.field input:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 1px #3b82f6;
}

.btn-primary {
  width: 100%;
  padding: 0.625rem;
  background: #1e293b;
  color: #fff;
  border: none;
  border-radius: 0.375rem;
  font-size: 0.875rem;
  font-weight: 600;
  cursor: pointer;
  margin-top: 0.5rem;
}

.btn-primary:hover {
  background: #334155;
}

.btn-primary:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}
</style>
