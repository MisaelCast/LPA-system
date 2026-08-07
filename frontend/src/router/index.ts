import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import MainLayout from '@/layouts/MainLayout.vue'

declare module 'vue-router' {
  interface RouteMeta {
    requiresAuth?: boolean
    roles?: string[]
  }
}

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/login',
      name: 'login',
      component: () => import('@/views/auth/LoginView.vue'),
    },
    {
      path: '/',
      component: MainLayout,
      meta: { requiresAuth: true },
      children: [
        {
          path: '',
          redirect: { name: 'dashboard' },
        },
        {
          path: 'dashboard',
          name: 'dashboard',
          component: () => import('@/views/dashboard/DashboardView.vue'),
        },
        {
          path: 'usuarios',
          name: 'usuarios',
          component: () => import('@/views/usuarios/UsuariosView.vue'),
          meta: { roles: ['Administrador'] },
        },
        {
          path: 'areas',
          name: 'areas',
          component: () => import('@/views/areas/AreasView.vue'),
          meta: { roles: ['Administrador'] },
        },
      ],
    },
  ],
})

router.beforeEach(async (to, from) => {
  const authStore = useAuthStore()

  if (to.meta.requiresAuth && !authStore.isAuthenticated) {
    return { name: 'login' }
  }

  if (to.name === 'login' && authStore.isAuthenticated) {
    return { name: 'dashboard' }
  }

  // Cargar datos del usuario si hay token pero no están en memoria (recarga de página)
  if (authStore.isAuthenticated && !authStore.usuario) {
    try {
      await authStore.cargarUsuario()
    } catch {
      authStore.clearToken()
      return { name: 'login' }
    }
  }

  // Validar rol requerido por la ruta
  const allowedRoles = to.meta.roles as string[] | undefined
  if (allowedRoles && authStore.usuario) {
    if (!allowedRoles.includes(authStore.usuario.rol_nombre)) {
      return { name: 'dashboard', query: { sin_permisos: '1' } }
    }
  }
})

export default router
