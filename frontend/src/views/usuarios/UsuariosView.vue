<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { useUsuariosStore } from '@/stores/usuarios'
import { useAuthStore } from '@/stores/auth'
import { obtenerRoles } from '@/services/rol.service'
import type { Usuario } from '@/types/auth'
import type { Rol } from '@/types/rol'

const store = useUsuariosStore()
const authStore = useAuthStore()

const roles = ref<Rol[]>([])
const busqueda = ref('')

const modalCrearAbierto = ref(false)
const modalEditarAbierto = ref(false)
const usuarioEditando = ref<Usuario | null>(null)
const formNombre = ref('')
const formCorreo = ref('')
const formContrasena = ref('')
const formRolId = ref(0)
const formError = ref('')
const formGuardando = ref(false)

interface Toast {
  id: number
  tipo: 'ok' | 'err'
  texto: string
}
const toasts = ref<Toast[]>([])
let toastId = 0

onMounted(async () => {
  store.cargarUsuarios()
  roles.value = await obtenerRoles()
})

const usuariosFiltrados = computed(() => {
  const q = busqueda.value.trim().toLowerCase()
  if (!q) return store.usuarios
  return store.usuarios.filter(
    (u) =>
      u.nombre.toLowerCase().includes(q) ||
      u.correo.toLowerCase().includes(q),
  )
})

const totalUsuarios = computed(() => store.usuarios.length)
const usuariosActivos = computed(() => store.usuarios.filter((u) => u.activo).length)

function mostrarToast(tipo: Toast['tipo'], texto: string) {
  const id = ++toastId
  toasts.value.push({ id, tipo, texto })
  setTimeout(() => {
    toasts.value = toasts.value.filter((t) => t.id !== id)
  }, 3500)
}

function mostrarError(prefix: string, err: unknown) {
  let mensaje = `Error al ${prefix}.`
  if (err && typeof err === 'object' && 'response' in err) {
    const axiosErr = err as { response: { status: number; data?: { detail?: string } } }
    if (axiosErr.response.status === 403) {
      mensaje = 'No tiene permisos para realizar esta acción.'
    } else if (axiosErr.response.data?.detail) {
      mensaje = axiosErr.response.data.detail
    }
  }
  mostrarToast('err', mensaje)
}

/* ——— Modal crear ——— */
function abrirModalCrear() {
  formNombre.value = ''
  formCorreo.value = ''
  formContrasena.value = ''
  formRolId.value = 0
  formError.value = ''
  modalCrearAbierto.value = true
}

function cerrarModalCrear() {
  if (formGuardando.value) return
  modalCrearAbierto.value = false
}

async function confirmarCrear() {
  formError.value = ''
  if (!formNombre.value.trim() || !formCorreo.value.trim() || !formContrasena.value || !formRolId.value) {
    formError.value = 'Complete todos los campos obligatorios.'
    return
  }
  formGuardando.value = true
  try {
    await store.crear({
      nombre: formNombre.value.trim(),
      correo: formCorreo.value.trim(),
      contrasena: formContrasena.value,
      rol_id: formRolId.value,
      activo: true,
    })
    mostrarToast('ok', `Usuario "${formNombre.value.trim()}" creado.`)
    modalCrearAbierto.value = false
  } catch (err) {
    mostrarError('crear el usuario', err)
  } finally {
    formGuardando.value = false
  }
}

/* ——— Modal editar ——— */
function abrirModalEditar(u: Usuario) {
  usuarioEditando.value = u
  formNombre.value = u.nombre
  formCorreo.value = u.correo
  formRolId.value = u.rol_id
  formError.value = ''
  modalEditarAbierto.value = true
}

function cerrarModalEditar() {
  if (formGuardando.value) return
  modalEditarAbierto.value = false
  usuarioEditando.value = null
}

async function confirmarEditar() {
  if (!usuarioEditando.value) return
  formError.value = ''
  if (!formNombre.value.trim() || !formCorreo.value.trim() || !formRolId.value) {
    formError.value = 'Complete todos los campos obligatorios.'
    return
  }
  formGuardando.value = true
  try {
    await store.actualizar(usuarioEditando.value.id, {
      nombre: formNombre.value.trim(),
      correo: formCorreo.value.trim(),
      rol_id: formRolId.value,
    })
    mostrarToast('ok', 'Usuario actualizado.')
    modalEditarAbierto.value = false
    usuarioEditando.value = null
  } catch (err) {
    mostrarError('actualizar el usuario', err)
  } finally {
    formGuardando.value = false
  }
}

/* ——— Activar/Desactivar ——— */
async function toggleEstado(u: Usuario) {
  const accion = u.activo ? 'desactivar' : 'activar'
  if (!window.confirm(`¿Desea ${accion} el usuario "${u.nombre}"?`)) return
  try {
    await store.cambiarEstado(u.id, !u.activo)
    mostrarToast('ok', `Usuario ${u.activo ? 'desactivado' : 'activado'}.`)
  } catch (err) {
    mostrarError('cambiar el estado del usuario', err)
  }
}

/* ——— Cerrar modal con Escape ——— */
function onKeydown(e: KeyboardEvent) {
  if (e.key === 'Escape') {
    if (modalEditarAbierto.value) cerrarModalEditar()
    else if (modalCrearAbierto.value) cerrarModalCrear()
  }
}

watch([modalCrearAbierto, modalEditarAbierto], ([crear, editar]) => {
  if (crear || editar) {
    document.addEventListener('keydown', onKeydown)
  } else {
    document.removeEventListener('keydown', onKeydown)
  }
})

onUnmounted(() => document.removeEventListener('keydown', onKeydown))
</script>

<template>
  <div class="usuarios-page">
    <!-- Encabezado -->
    <header class="page-header">
      <div class="page-header-info">
        <h1>Usuarios</h1>
        <p class="subtitle">Gestión de usuarios y sus roles en el sistema.</p>
      </div>
      <button
        v-if="authStore.isAdmin"
        class="btn-primary"
        @click="abrirModalCrear"
      >
        <svg class="icon-plus" viewBox="0 0 16 16" aria-hidden="true">
          <path d="M8 2v12M2 8h12" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
        </svg>
        Nuevo usuario
      </button>
    </header>

    <!-- Stats -->
    <div class="stats">
      <div class="stat">
        <span class="stat-label">Usuarios totales</span>
        <span class="stat-value">{{ totalUsuarios }}</span>
      </div>
      <div class="stat">
        <span class="stat-label">Usuarios activos</span>
        <span class="stat-value stat-active">{{ usuariosActivos }}</span>
      </div>
    </div>

    <!-- Búsqueda -->
    <div class="toolbar">
      <div class="search">
        <svg class="search-icon" viewBox="0 0 16 16" aria-hidden="true">
          <circle cx="7" cy="7" r="5" stroke="currentColor" stroke-width="1.6" fill="none"/>
          <path d="M11 11l3 3" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/>
        </svg>
        <input
          v-model="busqueda"
          type="search"
          placeholder="Buscar por nombre o correo…"
        />
        <button v-if="busqueda" class="search-clear" @click="busqueda = ''" title="Limpiar" aria-label="Limpiar búsqueda">
          <svg viewBox="0 0 16 16" aria-hidden="true">
            <path d="M4 4l8 8M12 4l-8 8" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/>
          </svg>
        </button>
      </div>
    </div>

    <!-- Cargando -->
    <div v-if="store.cargando" class="state state-loading">
      <div class="spinner"></div>
      <p>Cargando usuarios…</p>
    </div>

    <!-- Vacío -->
    <div v-else-if="store.usuarios.length === 0" class="state state-empty">
      <svg class="state-icon" viewBox="0 0 24 24" aria-hidden="true">
        <circle cx="12" cy="8" r="4" stroke="currentColor" stroke-width="1.6" fill="none"/>
        <path d="M4 20c0-3.3 3.6-5 8-5s8 1.7 8 5" stroke="currentColor" stroke-width="1.6" fill="none" stroke-linecap="round"/>
      </svg>
      <h2>Aún no hay usuarios</h2>
      <p>Comienza creando el primer usuario del sistema.</p>
      <button
        v-if="authStore.isAdmin"
        class="btn-primary"
        @click="abrirModalCrear"
      >
        Crear primer usuario
      </button>
    </div>

    <!-- Sin resultados -->
    <div v-else-if="usuariosFiltrados.length === 0" class="state state-empty">
      <svg class="state-icon" viewBox="0 0 24 24" aria-hidden="true">
        <circle cx="10.5" cy="10.5" r="6.5" stroke="currentColor" stroke-width="1.8" fill="none"/>
        <path d="M15.5 15.5L20 20" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/>
      </svg>
      <h2>Sin resultados</h2>
      <p>No hay usuarios que coincidan con «{{ busqueda }}».</p>
      <button class="btn-secondary" @click="busqueda = ''">
        Limpiar búsqueda
      </button>
    </div>

    <!-- Lista de usuarios -->
    <div v-else class="usuarios-list">
      <article
        v-for="u in usuariosFiltrados"
        :key="u.id"
        class="usuario-card"
        :class="{ 'usuario-card--inactive': !u.activo }"
      >
        <header class="usuario-card-header">
          <div class="usuario-avatar">{{ u.nombre.charAt(0).toUpperCase() }}</div>
          <div class="usuario-card-title">
            <h3>{{ u.nombre }}</h3>
            <span class="usuario-correo">{{ u.correo }}</span>
          </div>
          <div v-if="authStore.isAdmin" class="usuario-card-actions">
            <button
              class="icon-btn"
              title="Editar usuario"
              aria-label="Editar usuario"
              @click="abrirModalEditar(u)"
            >
              <svg viewBox="0 0 16 16" aria-hidden="true">
                <path d="M11.5 2.5l2 2-8 8H3.5v-2l8-8z" stroke="currentColor" stroke-width="1.4" fill="none" stroke-linejoin="round"/>
              </svg>
            </button>
            <button
              class="icon-btn"
              :title="u.activo ? 'Desactivar usuario' : 'Activar usuario'"
              :aria-label="u.activo ? 'Desactivar usuario' : 'Activar usuario'"
              @click="toggleEstado(u)"
            >
              <svg v-if="u.activo" viewBox="0 0 16 16" aria-hidden="true">
                <rect x="4" y="3" width="3" height="10" rx="0.5" fill="currentColor"/>
                <rect x="9" y="3" width="3" height="10" rx="0.5" fill="currentColor"/>
              </svg>
              <svg v-else viewBox="0 0 16 16" aria-hidden="true">
                <path d="M5 3l8 5-8 5V3z" fill="currentColor"/>
              </svg>
            </button>
          </div>
        </header>
        <div class="usuario-card-meta">
          <span class="badge rol-badge">{{ u.rol_nombre }}</span>
          <span class="badge" :class="u.activo ? 'badge-on' : 'badge-off'">
            {{ u.activo ? 'Activo' : 'Inactivo' }}
          </span>
        </div>
      </article>
    </div>

    <!-- Modal: crear usuario -->
    <div
      v-if="modalCrearAbierto"
      class="modal-backdrop"
      @click.self="cerrarModalCrear"
    >
      <div class="modal" role="dialog" aria-labelledby="modal-crear-titulo">
        <header class="modal-header">
          <h2 id="modal-crear-titulo">Nuevo usuario</h2>
          <button class="modal-close" @click="cerrarModalCrear" aria-label="Cerrar">
            <svg viewBox="0 0 16 16" aria-hidden="true">
              <path d="M4 4l8 8M12 4l-8 8" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/>
            </svg>
          </button>
        </header>
        <div class="modal-body">
          <label class="field">
            <span>Nombre</span>
            <input v-model="formNombre" placeholder="Ej: Juan Pérez" autofocus />
          </label>
          <label class="field">
            <span>Correo</span>
            <input v-model="formCorreo" type="email" placeholder="correo@empresa.com" />
          </label>
          <label class="field">
            <span>Contraseña</span>
            <input v-model="formContrasena" type="password" placeholder="Contraseña" />
          </label>
          <label class="field">
            <span>Rol</span>
            <select v-model.number="formRolId">
              <option :value="0" disabled>Seleccione</option>
              <option v-for="r in roles" :key="r.id" :value="r.id">{{ r.nombre }}</option>
            </select>
          </label>
          <p v-if="formError" class="form-error">{{ formError }}</p>
        </div>
        <footer class="modal-footer">
          <button class="btn-secondary" :disabled="formGuardando" @click="cerrarModalCrear">
            Cancelar
          </button>
          <button class="btn-primary" :disabled="formGuardando" @click="confirmarCrear">
            {{ formGuardando ? 'Creando…' : 'Crear usuario' }}
          </button>
        </footer>
      </div>
    </div>

    <!-- Modal: editar usuario -->
    <div
      v-if="modalEditarAbierto && usuarioEditando"
      class="modal-backdrop"
      @click.self="cerrarModalEditar"
    >
      <div class="modal" role="dialog" aria-labelledby="modal-editar-titulo">
        <header class="modal-header">
          <h2 id="modal-editar-titulo">Editar usuario</h2>
          <button class="modal-close" @click="cerrarModalEditar" aria-label="Cerrar">
            <svg viewBox="0 0 16 16" aria-hidden="true">
              <path d="M4 4l8 8M12 4l-8 8" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/>
            </svg>
          </button>
        </header>
        <div class="modal-body">
          <label class="field">
            <span>Nombre</span>
            <input v-model="formNombre" autofocus />
          </label>
          <label class="field">
            <span>Correo</span>
            <input v-model="formCorreo" type="email" />
          </label>
          <label class="field">
            <span>Rol</span>
            <select v-model.number="formRolId">
              <option v-for="r in roles" :key="r.id" :value="r.id">{{ r.nombre }}</option>
            </select>
          </label>
          <p v-if="formError" class="form-error">{{ formError }}</p>
        </div>
        <footer class="modal-footer">
          <button class="btn-secondary" :disabled="formGuardando" @click="cerrarModalEditar">
            Cancelar
          </button>
          <button class="btn-primary" :disabled="formGuardando" @click="confirmarEditar">
            {{ formGuardando ? 'Guardando…' : 'Guardar cambios' }}
          </button>
        </footer>
      </div>
    </div>

    <!-- Toasts -->
    <div class="toasts" aria-live="polite">
      <div
        v-for="t in toasts"
        :key="t.id"
        class="toast"
        :class="t.tipo === 'ok' ? 'toast-ok' : 'toast-err'"
      >
        <svg v-if="t.tipo === 'ok'" class="toast-icon" viewBox="0 0 16 16" aria-hidden="true">
          <path d="M3 8l3.5 3.5L13 5" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
        <svg v-else class="toast-icon" viewBox="0 0 16 16" aria-hidden="true">
          <path d="M8 2l7 13H1L8 2z" stroke="currentColor" stroke-width="1.6" fill="none" stroke-linejoin="round"/>
          <path d="M8 7v3" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/>
          <circle cx="8" cy="12" r="0.8" fill="currentColor"/>
        </svg>
        <span>{{ t.texto }}</span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.usuarios-page {
  max-width: 900px;
  margin: 0 auto;
}

/* --- Header --- */
.page-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 1rem;
  margin-bottom: 1.25rem;
  flex-wrap: wrap;
}

.page-header-info h1 {
  margin: 0;
  font-size: 1.6rem;
  font-weight: 700;
  color: #0f172a;
  letter-spacing: -0.01em;
}

.subtitle {
  margin: 0.25rem 0 0;
  color: #64748b;
  font-size: 0.95rem;
}

/* --- Stats --- */
.stats {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 0.75rem;
  margin-bottom: 1.25rem;
}

.stat {
  background: #fff;
  border: 1px solid #e2e8f0;
  border-radius: 0.6rem;
  padding: 0.85rem 1rem;
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04);
}

.stat-label {
  font-size: 0.75rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: #94a3b8;
  font-weight: 600;
}

.stat-value {
  font-size: 1.65rem;
  font-weight: 700;
  color: #0f172a;
  line-height: 1.1;
}

.stat-active {
  color: #16a34a;
}

/* --- Toolbar --- */
.toolbar {
  margin-bottom: 1rem;
}

.search {
  position: relative;
  display: flex;
  align-items: center;
  background: #fff;
  border: 1px solid #e2e8f0;
  border-radius: 0.5rem;
  padding: 0 0.75rem;
  transition: border-color 0.15s, box-shadow 0.15s;
}

.search:focus-within {
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.search-icon {
  color: #94a3b8;
  margin-right: 0.5rem;
  width: 1rem;
  height: 1rem;
  flex-shrink: 0;
}

.search input {
  flex: 1;
  border: none;
  padding: 0.6rem 0;
  font-size: 0.9rem;
  outline: none;
  background: transparent;
  color: #0f172a;
}

.search-clear {
  background: transparent;
  border: none;
  color: #94a3b8;
  cursor: pointer;
  padding: 0.35rem;
  border-radius: 0.25rem;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.search-clear svg {
  width: 0.85rem;
  height: 0.85rem;
}

.search-clear:hover {
  color: #475569;
}

/* --- Estados --- */
.state {
  background: #fff;
  border: 1px dashed #cbd5e1;
  border-radius: 0.6rem;
  padding: 2.5rem 1.5rem;
  text-align: center;
  color: #475569;
}

.state-icon {
  width: 3rem;
  height: 3rem;
  color: #94a3b8;
  margin: 0 auto 0.5rem;
  display: block;
}

.state h2 {
  margin: 0.5rem 0;
  font-size: 1.1rem;
  color: #0f172a;
}

.state p {
  margin: 0 0 1rem;
  color: #64748b;
}

.state-loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.75rem;
}

.spinner {
  width: 1.75rem;
  height: 1.75rem;
  border: 3px solid #e2e8f0;
  border-top-color: #3b82f6;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* --- Lista de usuarios --- */
.usuarios-list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.usuario-card {
  background: #fff;
  border: 1px solid #e2e8f0;
  border-radius: 0.6rem;
  padding: 1rem 1.1rem;
  box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04);
  transition: border-color 0.15s, box-shadow 0.15s;
}

.usuario-card:hover {
  border-color: #cbd5e1;
  box-shadow: 0 2px 6px rgba(15, 23, 42, 0.05);
}

.usuario-card--inactive {
  background: #f8fafc;
  opacity: 0.85;
}

.usuario-card-header {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.usuario-avatar {
  width: 2.4rem;
  height: 2.4rem;
  border-radius: 50%;
  background: #e0e7ff;
  color: #4338ca;
  font-weight: 700;
  font-size: 1.1rem;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.usuario-card-title {
  display: flex;
  flex-direction: column;
  gap: 0.15rem;
  flex: 1;
  min-width: 0;
}

.usuario-card-title h3 {
  margin: 0;
  font-size: 1.02rem;
  font-weight: 600;
  color: #0f172a;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.usuario-correo {
  font-size: 0.82rem;
  color: #64748b;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.usuario-card-actions {
  display: flex;
  gap: 0.25rem;
  margin-left: auto;
}

.usuario-card-meta {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  margin-top: 0.65rem;
  padding-left: 3.15rem;
}

.rol-badge {
  background: #eef2ff;
  color: #4338ca;
}

/* --- Badges --- */
.badge {
  display: inline-block;
  padding: 0.15rem 0.55rem;
  border-radius: 999px;
  font-size: 0.7rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.03em;
}

.badge-on {
  background: #dcfce7;
  color: #166534;
}

.badge-off {
  background: #f1f5f9;
  color: #64748b;
}

/* --- Icon buttons --- */
.icon-btn {
  width: 1.85rem;
  height: 1.85rem;
  border: 1px solid transparent;
  background: transparent;
  border-radius: 0.4rem;
  cursor: pointer;
  color: #64748b;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  transition: background 0.15s, color 0.15s, border-color 0.15s;
  padding: 0;
}

.icon-btn svg {
  width: 0.95rem;
  height: 0.95rem;
}

.icon-btn:hover {
  background: #f1f5f9;
  color: #0f172a;
  border-color: #e2e8f0;
}

/* --- Botones --- */
.btn-primary {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  background: #2563eb;
  color: #fff;
  border: none;
  border-radius: 0.5rem;
  padding: 0.6rem 1.1rem;
  font-size: 0.9rem;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.15s, transform 0.05s;
  box-shadow: 0 1px 2px rgba(37, 99, 235, 0.2);
}

.btn-primary:hover {
  background: #1d4ed8;
}

.btn-primary:active {
  transform: translateY(1px);
}

.btn-primary:disabled {
  background: #93c5fd;
  cursor: not-allowed;
}

.btn-secondary {
  background: #fff;
  color: #334155;
  border: 1px solid #cbd5e1;
  border-radius: 0.5rem;
  padding: 0.55rem 1rem;
  font-size: 0.9rem;
  cursor: pointer;
  transition: background 0.15s, border-color 0.15s;
}

.btn-secondary:hover {
  background: #f8fafc;
  border-color: #94a3b8;
}

.btn-secondary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.icon-plus {
  width: 1rem;
  height: 1rem;
  flex-shrink: 0;
}

/* --- Modal --- */
.modal-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(15, 23, 42, 0.45);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 100;
  animation: fade-in 0.15s ease;
}

@keyframes fade-in {
  from { opacity: 0; }
  to { opacity: 1; }
}

.modal {
  background: #fff;
  border-radius: 0.75rem;
  width: min(440px, calc(100% - 2rem));
  box-shadow: 0 20px 40px rgba(15, 23, 42, 0.2);
  display: flex;
  flex-direction: column;
  animation: pop-in 0.18s ease;
}

@keyframes pop-in {
  from { transform: translateY(8px) scale(0.98); opacity: 0; }
  to { transform: translateY(0) scale(1); opacity: 1; }
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1rem 1.25rem;
  border-bottom: 1px solid #e2e8f0;
}

.modal-header h2 {
  margin: 0;
  font-size: 1.05rem;
  color: #0f172a;
}

.modal-close {
  background: transparent;
  border: none;
  color: #94a3b8;
  cursor: pointer;
  padding: 0.4rem;
  border-radius: 0.3rem;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.modal-close svg {
  width: 1rem;
  height: 1rem;
}

.modal-close:hover {
  background: #f1f5f9;
  color: #0f172a;
}

.modal-body {
  padding: 1.25rem;
  display: flex;
  flex-direction: column;
  gap: 0.85rem;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 0.5rem;
  padding: 0.85rem 1.25rem;
  border-top: 1px solid #e2e8f0;
  background: #f8fafc;
  border-radius: 0 0 0.75rem 0.75rem;
}

.field {
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
}

.field span {
  font-size: 0.8rem;
  font-weight: 600;
  color: #475569;
}

.field input,
.field select {
  padding: 0.55rem 0.75rem;
  border: 1px solid #cbd5e1;
  border-radius: 0.4rem;
  font-size: 0.9rem;
  color: #0f172a;
  background: #fff;
  outline: none;
  transition: border-color 0.15s, box-shadow 0.15s;
}

.field input:focus,
.field select:focus {
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.form-error {
  margin: 0;
  padding: 0.5rem 0.75rem;
  border-radius: 0.4rem;
  background: #fef2f2;
  color: #dc2626;
  font-size: 0.85rem;
  border: 1px solid #fecaca;
}

/* --- Toasts --- */
.toasts {
  position: fixed;
  top: 1.25rem;
  right: 1.25rem;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  z-index: 200;
  pointer-events: none;
}

.toast {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.65rem 1rem;
  border-radius: 0.5rem;
  background: #fff;
  border: 1px solid #e2e8f0;
  box-shadow: 0 6px 18px rgba(15, 23, 42, 0.12);
  font-size: 0.88rem;
  color: #0f172a;
  min-width: 240px;
  pointer-events: auto;
  animation: slide-in 0.2s ease;
}

@keyframes slide-in {
  from { transform: translateX(20px); opacity: 0; }
  to { transform: translateX(0); opacity: 1; }
}

.toast-ok {
  border-left: 3px solid #16a34a;
}

.toast-ok .toast-icon {
  color: #16a34a;
}

.toast-err {
  border-left: 3px solid #dc2626;
}

.toast-err .toast-icon {
  color: #dc2626;
}

.toast-icon {
  width: 1.1rem;
  height: 1.1rem;
  flex-shrink: 0;
}

/* --- Responsive --- */
@media (max-width: 640px) {
  .page-header-info h1 {
    font-size: 1.35rem;
  }
}
</style>
