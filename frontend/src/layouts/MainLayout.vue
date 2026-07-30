<script setup lang="ts">
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()

function handleLogout() {
  authStore.clearToken()
  router.push('/login')
}
</script>

<template>
  <div class="layout">
    <aside class="sidebar">
      <nav>
        <RouterLink to="/dashboard">Dashboard</RouterLink>
        <RouterLink v-if="authStore.isAdmin" to="/usuarios">Usuarios</RouterLink>
      </nav>
    </aside>

    <div class="main">
      <header class="header">
        <span class="brand">LPA System</span>
        <div class="header-right">
          <span class="user">{{ authStore.usuario?.nombre || 'Usuario' }}</span>
          <button class="btn-logout" @click="handleLogout">Cerrar sesión</button>
        </div>
      </header>

      <main class="content">
        <RouterView />
      </main>
    </div>
  </div>
</template>

<style scoped>
.layout {
  display: flex;
  min-height: 100vh;
}

.sidebar {
  width: 220px;
  background: #1e293b;
  color: #fff;
  padding: 1rem;
}

.sidebar a {
  display: block;
  color: #cbd5e1;
  padding: 0.5rem 0.75rem;
  border-radius: 0.375rem;
  text-decoration: none;
}

.sidebar a:hover,
.sidebar a.router-link-active {
  background: #334155;
  color: #fff;
}

.main {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem 1.5rem;
  background: #fff;
  border-bottom: 1px solid #e2e8f0;
}

.brand {
  font-weight: 700;
  font-size: 1.125rem;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.user {
  color: #64748b;
}

.btn-logout {
  background: #ef4444;
  color: #fff;
  border: none;
  padding: 0.375rem 0.75rem;
  border-radius: 0.375rem;
  cursor: pointer;
  font-size: 0.875rem;
}

.btn-logout:hover {
  background: #dc2626;
}

.content {
  flex: 1;
  padding: 1.5rem;
}
</style>
