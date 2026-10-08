<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

const avisoPermisos = ref(false)
const menuAbierto = ref(false)
const movil = ref(false)

let mediaQuery: MediaQueryList | null = null

function actualizarMovil() {
  movil.value = window.matchMedia('(max-width: 768px)').matches
}

onMounted(() => {
  mediaQuery = window.matchMedia('(max-width: 768px)')
  actualizarMovil()
  mediaQuery.addEventListener('change', actualizarMovil)
})

onUnmounted(() => {
  mediaQuery?.removeEventListener('change', actualizarMovil)
})

watch(
  () => route.query.sin_permisos,
  (val) => {
    if (val) {
      avisoPermisos.value = true
      router.replace({ query: {} })
      setTimeout(() => {
        avisoPermisos.value = false
      }, 5000)
    }
  },
  { immediate: true },
)

const enlaces = computed(() => [
  { to: '/dashboard', label: 'Dashboard', icon: 'grid', visible: true },
  { to: '/usuarios', label: 'Usuarios', icon: 'users', visible: authStore.isAdmin },
  { to: '/areas', label: 'Áreas', icon: 'areas', visible: authStore.isAdmin },
  { to: '/capas', label: 'Capas', icon: 'layers', visible: authStore.isAdmin },
  { to: '/auditorias', label: 'Auditorías', icon: 'clipboard', visible: authStore.isAdmin },
  { to: '/ejecutar', label: 'Ejecutar Auditoría', icon: 'play', visible: true },
  { to: '/mis-pendientes', label: 'Mis pendientes', icon: 'pend', visible: true },
  { to: '/auditorias-realizadas', label: 'Auditorías realizadas', icon: 'history', visible: true },
  { to: '/hallazgos', label: 'Hallazgos', icon: 'flag', visible: true },
  {
    to: '/revision-auditorias',
    label: 'Revisión de auditorías',
    icon: 'review',
    visible: authStore.isAdmin || authStore.isSupervisor || authStore.isGerente,
  },
])

function handleLogout() {
  authStore.clearToken()
  router.push('/login')
}
</script>

<template>
  <div class="layout">
    <button
      v-if="movil"
      class="menu-toggle"
      aria-label="Abrir menú"
      @click="menuAbierto = true"
    >
      <svg viewBox="0 0 24 24" aria-hidden="true">
        <path d="M4 6h16M4 12h16M4 18h16" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/>
      </svg>
    </button>

    <div v-if="menuAbierto" class="backdrop" @click="menuAbierto = false"></div>

    <aside class="sidebar" :class="{ 'sidebar--open': menuAbierto }">
      <div class="sidebar-brand">
        <span class="brand-mark">
          <svg viewBox="0 0 24 24" aria-hidden="true">
            <path d="M4 4h16v16H4z" stroke="currentColor" stroke-width="1.7" stroke-linejoin="round" fill="none"/>
            <path d="M8 12.2l2.8 2.8L16.5 9" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" fill="none"/>
          </svg>
        </span>
        <span class="brand-text">LPA&nbsp;<strong>System</strong></span>
      </div>

      <nav class="sidebar-nav">
        <RouterLink
          v-for="enlace in enlaces.filter((e) => e.visible)"
          :key="enlace.to"
          :to="enlace.to"
          class="nav-item"
        >
          <svg class="nav-icon" viewBox="0 0 24 24" aria-hidden="true">
            <template v-if="enlace.icon === 'grid'">
              <rect x="3.5" y="3.5" width="7" height="7" rx="1.2" />
              <rect x="13.5" y="3.5" width="7" height="7" rx="1.2" />
              <rect x="3.5" y="13.5" width="7" height="7" rx="1.2" />
              <rect x="13.5" y="13.5" width="7" height="7" rx="1.2" />
            </template>
            <template v-else-if="enlace.icon === 'users'">
              <circle cx="12" cy="8" r="3.4" />
              <path d="M4.8 20c0-3 3.2-4.8 7.2-4.8s7.2 1.8 7.2 4.8" />
            </template>
            <template v-else-if="enlace.icon === 'areas'">
              <path d="M4 20V10.5l4-2.6V5.4L12 4l4 1.4v2.5l4 2.6V20" />
              <path d="M4 20h16M9 20v-3h2v3M13 20v-3h2v3" />
            </template>
            <template v-else-if="enlace.icon === 'layers'">
              <path d="M12 3.5l8 4-8 4-8-4 8-4z" />
              <path d="M4 12l8 4 8-4" />
              <path d="M4 16l8 4 8-4" />
            </template>
            <template v-else-if="enlace.icon === 'clipboard'">
              <path d="M8 4h1.2a1.6 1.6 0 0 1 3.2 0h1.2" />
              <rect x="5" y="4" width="14" height="16.5" rx="1.8" />
              <path d="M9 10h6M9 13.5h6M9 17h4" />
            </template>
            <template v-else-if="enlace.icon === 'play'">
              <rect x="4" y="4" width="16" height="16" rx="2.2" />
              <path d="M10.4 8.8l4.6 3.2-4.6 3.2V8.8z" fill="currentColor" stroke="none"/>
            </template>
            <template v-else-if="enlace.icon === 'history'">
              <circle cx="12" cy="12" r="8.6" />
              <path d="M12 7.2V12l3.2 2" />
              <path d="M7.5 5.2L5.5 7l1.8 2" />
            </template>
            <template v-else-if="enlace.icon === 'review'">
              <path d="M12 3.2l6.8 2.8V12c0 4.2-2.8 7.2-6.8 8.8C7.8 19.2 5 16.2 5 12V6L12 3.2z" />
              <path d="M9 12l2.1 2.1 4-4" />
            </template>
            <template v-else-if="enlace.icon === 'flag'">
              <path d="M6 4v16" />
              <path d="M6 5h10l-1.8 3.5L16 12H6" />
            </template>
            <template v-else-if="enlace.icon === 'pend'">
              <circle cx="12" cy="12" r="8.6" />
              <path d="M12 7.2V12l3.2 2" />
            </template>
          </svg>
          <span class="nav-label">{{ enlace.label }}</span>
        </RouterLink>
      </nav>
    </aside>

    <div class="main">
      <header class="header">
        <div class="header-left">
          <span class="header-brand">LPA System</span>
        </div>
        <div class="header-right">
          <span class="header-user">{{ authStore.usuario?.nombre || 'Usuario' }}</span>
          <span class="rol-badge">{{ authStore.usuario?.rol_nombre }}</span>
          <button class="btn-logout header-logout" @click="handleLogout">
            Cerrar sesión
          </button>
        </div>
      </header>

      <main class="content">
        <p v-if="avisoPermisos" class="aviso-permisos" role="alert">
          No tiene permisos para acceder a esa sección.
        </p>
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

/* --- Sidebar --- */
.sidebar {
  width: 248px;
  flex-shrink: 0;
  background: var(--c-sidebar, #0f172a);
  color: #cbd5e1;
  display: flex;
  flex-direction: column;
  position: sticky;
  top: 0;
  height: 100vh;
  padding: 1rem 0.75rem;
  gap: 0.25rem;
}

.sidebar-brand {
  display: flex;
  align-items: center;
  gap: 0.65rem;
  padding: 0.25rem 0.6rem 1.1rem;
  color: #f1f5f9;
}

.brand-mark {
  width: 2.1rem;
  height: 2.1rem;
  border-radius: 0.6rem;
  background: linear-gradient(140deg, #3b82f6, #2563eb);
  color: #fff;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 4px 12px rgba(37, 99, 235, 0.4);
  flex-shrink: 0;
}

.brand-mark svg {
  width: 1.25rem;
  height: 1.25rem;
}

.brand-text {
  font-size: 1.05rem;
  font-weight: 600;
  letter-spacing: -0.01em;
  white-space: nowrap;
}

.brand-text strong {
  color: #fff;
  font-weight: 800;
}

.sidebar-nav {
  display: flex;
  flex-direction: column;
  gap: 0.2rem;
  flex: 1;
  overflow-y: auto;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 0.7rem;
  padding: 0.56rem 0.7rem;
  border-radius: 0.6rem;
  color: #94a3b8;
  text-decoration: none;
  font-size: 0.875rem;
  font-weight: 500;
  transition: background 0.15s var(--ease), color 0.15s var(--ease);
  line-height: 1.2;
}

.nav-icon {
  width: 1.2rem;
  height: 1.2rem;
  flex-shrink: 0;
  fill: none;
  stroke: currentColor;
  stroke-width: 1.6;
  stroke-linecap: round;
  stroke-linejoin: round;
}

.nav-item:hover {
  background: rgba(148, 163, 184, 0.1);
  color: #e2e8f0;
}

.nav-item.router-link-active {
  background: var(--c-primary, #2563eb);
  color: #fff;
  font-weight: 600;
  box-shadow: 0 4px 12px rgba(37, 99, 235, 0.35);
}

.nav-item.router-link-active .nav-icon {
  stroke-width: 1.9;
}

/* --- Main --- */
.main {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  padding: 0.9rem 1.75rem;
  background: var(--c-surface, #fff);
  border-bottom: 1px solid var(--c-line, #e6e9ef);
  position: sticky;
  top: 0;
  z-index: 40;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 0.6rem;
}

.header-brand {
  display: none;
  font-weight: 800;
  font-size: 1.05rem;
  letter-spacing: -0.02em;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-left: auto;
}

.header-user {
  color: var(--c-ink-2, #334155);
  font-size: 0.875rem;
  font-weight: 600;
}

.rol-badge {
  display: inline-flex;
  align-items: center;
  padding: 0.22rem 0.65rem;
  border-radius: 999px;
  background: var(--c-primary-soft, #eef2ff);
  color: var(--c-primary-active, #1e40af);
  font-size: 0.72rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.03em;
}

.header-logout {
  display: inline-flex;
  align-items: center;
  padding: 0.45rem 0.85rem;
  border: 1px solid var(--c-line-2, #d5dae3);
  border-radius: 0.5rem;
  background: var(--c-surface, #fff);
  color: var(--c-ink-3, #64748b);
}

.header-logout:hover {
  background: var(--c-danger-soft, #fee2e2);
  border-color: #fecaca;
  color: var(--c-danger-ink, #b91c1c);
}

.content {
  flex: 1;
  width: 100%;
  max-width: var(--content-max-width, 1280px);
  margin: 0 auto;
  padding: var(--content-pad, 1.75rem);
}

.aviso-permisos {
  background: var(--c-warn-soft, #fef3c7);
  color: var(--c-warn-ink, #92400e);
  border: 1px solid #fcd34d;
  padding: 0.75rem 1rem;
  border-radius: 0.6rem;
  margin-bottom: 1rem;
  font-size: 0.875rem;
}

/* --- Mobile --- */
.menu-toggle {
  display: none;
}

.backdrop {
  display: none;
}

@media (max-width: 1024px) {
  .sidebar {
    width: 68px;
    padding: 1rem 0.5rem;
  }

  .brand-text,
  .nav-label {
    display: none;
  }

  .sidebar-brand {
    justify-content: center;
    padding-left: 0;
    padding-right: 0;
  }

  .nav-item {
    justify-content: center;
    padding: 0.6rem;
  }
}

@media (max-width: 768px) {
  .menu-toggle {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    position: fixed;
    top: 0.85rem;
    left: 1rem;
    z-index: 60;
    width: 2.4rem;
    height: 2.4rem;
    border-radius: 0.6rem;
    border: 1px solid var(--c-line, #e6e9ef);
    background: var(--c-surface, #fff);
    color: var(--c-ink-2, #334155);
    box-shadow: var(--sh-md, 0 2px 6px rgba(15, 23, 42, 0.06));
    cursor: pointer;
  }

  .menu-toggle svg {
    width: 1.2rem;
    height: 1.2rem;
  }

  .sidebar {
    position: fixed;
    inset: 0 auto 0 0;
    width: 248px;
    transform: translateX(-100%);
    transition: transform 0.22s var(--ease);
    z-index: 55;
  }

  .sidebar--open {
    transform: translateX(0);
  }

  .sidebar--open .brand-text,
  .sidebar--open .nav-label {
    display: initial;
  }

  .sidebar--open .sidebar-brand,
  .sidebar--open .nav-item {
    justify-content: flex-start;
  }

  .backdrop {
    display: block;
    position: fixed;
    inset: 0;
    background: rgba(15, 23, 42, 0.5);
    z-index: 50;
  }

  .header {
    padding: 0.9rem 1rem 0.9rem 3.9rem;
  }

  .header-brand {
    display: inline;
  }

  .header-user {
    display: none;
  }

  .content {
    padding: var(--content-pad-sm, 1.25rem 1rem);
  }
}
</style>