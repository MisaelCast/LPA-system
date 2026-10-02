<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { login } from '@/services/auth.service'

const router = useRouter()
const authStore = useAuthStore()

const correo = ref('')
const contrasena = ref('')
const mostrarContrasena = ref(false)
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
    await authStore.cargarUsuario()
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
    <div class="login-glow" aria-hidden="true"></div>

    <form class="login-card" @submit.prevent="handleSubmit">
      <div class="login-brand">
        <span class="brand-mark">
          <svg viewBox="0 0 24 24" aria-hidden="true">
            <path d="M4 4h16v16H4z" stroke="currentColor" stroke-width="1.7" stroke-linejoin="round" fill="none"/>
            <path d="M8 12.2l2.8 2.8L16.5 9" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" fill="none"/>
          </svg>
        </span>
        <div>
          <h1>LPA System</h1>
          <p class="login-subtitle">Auditorías de proceso Layer Process Audit</p>
        </div>
      </div>

      <div v-if="error" class="msg msg-err" role="alert">{{ error }}</div>

      <div class="field">
        <label for="correo">Correo</label>
        <input
          id="correo"
          v-model="correo"
          type="email"
          required
          autocomplete="email"
          placeholder="correo@empresa.com"
        />
      </div>

      <div class="field">
        <label for="contrasena">Contraseña</label>
        <div class="password-wrapper">
          <input
            id="contrasena"
            v-model="contrasena"
            :type="mostrarContrasena ? 'text' : 'password'"
            required
            autocomplete="current-password"
            placeholder="Tu contraseña"
          />
          <button
            type="button"
            class="icon-btn toggle-password"
            :aria-label="mostrarContrasena ? 'Ocultar contraseña' : 'Mostrar contraseña'"
            @click="mostrarContrasena = !mostrarContrasena"
          >
            <svg
              v-if="mostrarContrasena"
              xmlns="http://www.w3.org/2000/svg"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="1.8"
              stroke-linecap="round"
              stroke-linejoin="round"
            >
              <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24" />
              <line x1="1" y1="1" x2="23" y2="23" />
            </svg>
            <svg
              v-else
              xmlns="http://www.w3.org/2000/svg"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="1.8"
              stroke-linecap="round"
              stroke-linejoin="round"
            >
              <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" />
              <circle cx="12" cy="12" r="3" />
            </svg>
          </button>
        </div>
      </div>

      <button class="btn-primary login-submit" type="submit" :disabled="cargando">
        {{ cargando ? 'Iniciando sesión…' : 'Iniciar sesión' }}
      </button>

      <p class="login-help">¿Problemas con tu cuenta? Contacta al administrador.</p>
    </form>
  </div>
</template>

<style scoped>
.login-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--c-canvas, #f3f5f8);
  padding: 1.25rem;
  position: relative;
  overflow: hidden;
}

.login-glow {
  position: absolute;
  inset: -30% -20% auto auto;
  width: 720px;
  height: 720px;
  background: radial-gradient(circle, rgba(37, 99, 235, 0.14) 0%, rgba(37, 99, 235, 0) 65%);
  pointer-events: none;
}

.login-card {
  position: relative;
  background: var(--c-surface, #fff);
  padding: 2.25rem 2.1rem 1.75rem;
  border-radius: var(--r-xl, 18px);
  border: 1px solid var(--c-line, #e6e9ef);
  box-shadow: var(--sh-lg, 0 12px 28px rgba(15, 23, 42, 0.12));
  width: 100%;
  max-width: 400px;
  display: flex;
  flex-direction: column;
  gap: 1.1rem;
  animation: card-in 0.28s var(--ease, cubic-bezier(0.2, 0.75, 0.2, 1));
}

@keyframes card-in {
  from {
    opacity: 0;
    transform: translateY(10px) scale(0.99);
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

.login-brand {
  display: flex;
  align-items: center;
  gap: 0.85rem;
  margin-bottom: 0.35rem;
}

.brand-mark {
  width: 3rem;
  height: 3rem;
  border-radius: 0.85rem;
  background: linear-gradient(140deg, #3b82f6, #2563eb);
  color: #fff;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 6px 16px rgba(37, 99, 235, 0.4);
  flex-shrink: 0;
}

.brand-mark svg {
  width: 1.75rem;
  height: 1.75rem;
}

h1 {
  font-size: 1.5rem;
  font-weight: 800;
  letter-spacing: -0.025em;
  color: var(--c-ink, #0f172a);
  line-height: 1.15;
}

.login-subtitle {
  color: var(--c-ink-3, #64748b);
  font-size: 0.82rem;
  margin-top: 0.2rem;
}

.password-wrapper {
  position: relative;
}

.password-wrapper input {
  width: 100%;
  padding-right: 2.6rem;
  box-sizing: border-box;
}

.toggle-password {
  position: absolute;
  top: 50%;
  right: 0.45rem;
  transform: translateY(-50%);
  width: 2.1rem;
  height: 2.1rem;
}

.toggle-password svg {
  width: 1.1rem;
  height: 1.1rem;
}

.login-submit {
  width: 100%;
  padding: 0.75rem 1.25rem;
  margin-top: 0.15rem;
  font-size: 0.9rem;
}

.login-help {
  text-align: center;
  color: var(--c-ink-4, #94a3b8);
  font-size: 0.78rem;
}
</style>