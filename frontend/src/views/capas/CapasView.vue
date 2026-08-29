<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { useCapasStore } from '@/stores/capas'
import { useAuthStore } from '@/stores/auth'
import type { Capa } from '@/types/capa'

const store = useCapasStore()
const authStore = useAuthStore()

const busqueda = ref('')

const modalCrearAbierto = ref(false)
const modalEditarAbierto = ref(false)
const capaEditando = ref<Capa | null>(null)
const formNombre = ref('')
const formDescripcion = ref('')
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
  await store.cargarCapas()
})

const capasFiltradas = computed(() => {
  const q = busqueda.value.trim().toLowerCase()
  if (!q) return store.capas
  return store.capas.filter((c) => c.nombre.toLowerCase().includes(q))
})

const totalCapas = computed(() => store.capas.length)
const capasActivas = computed(() => store.capas.filter((c) => c.activa).length)

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
  formDescripcion.value = ''
  formError.value = ''
  modalCrearAbierto.value = true
}

function cerrarModalCrear() {
  if (formGuardando.value) return
  modalCrearAbierto.value = false
}

async function confirmarCrear() {
  formError.value = ''
  if (!formNombre.value.trim()) {
    formError.value = 'El nombre de la capa es obligatorio.'
    return
  }
  formGuardando.value = true
  try {
    await store.crear({
      nombre: formNombre.value.trim(),
      descripcion: formDescripcion.value.trim() || undefined,
      activa: true,
    })
    mostrarToast('ok', `Capa "${formNombre.value.trim()}" creada.`)
    modalCrearAbierto.value = false
  } catch (err) {
    mostrarError('crear la capa', err)
  } finally {
    formGuardando.value = false
  }
}

/* ——— Modal editar ——— */
function abrirModalEditar(c: Capa) {
  capaEditando.value = c
  formNombre.value = c.nombre
  formDescripcion.value = c.descripcion || ''
  formError.value = ''
  modalEditarAbierto.value = true
}

function cerrarModalEditar() {
  if (formGuardando.value) return
  modalEditarAbierto.value = false
  capaEditando.value = null
}

async function confirmarEditar() {
  if (!capaEditando.value) return
  formError.value = ''
  if (!formNombre.value.trim()) {
    formError.value = 'El nombre de la capa es obligatorio.'
    return
  }
  formGuardando.value = true
  try {
    await store.actualizar(capaEditando.value.id, {
      nombre: formNombre.value.trim(),
      descripcion: formDescripcion.value.trim() || undefined,
    })
    mostrarToast('ok', 'Capa actualizada.')
    modalEditarAbierto.value = false
    capaEditando.value = null
  } catch (err) {
    mostrarError('actualizar la capa', err)
  } finally {
    formGuardando.value = false
  }
}

/* ——— Eliminar ——— */
async function eliminarCapa(c: Capa) {
  if (!window.confirm(`¿Está seguro de que desea eliminar la capa "${c.nombre}"?\n\nEsta acción no se puede deshacer.`)) return
  try {
    await store.eliminar(c.id)
    mostrarToast('ok', 'Capa eliminada correctamente.')
  } catch (err) {
    mostrarError('eliminar la capa', err)
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
  <div class="capas-page">
    <!-- Encabezado -->
    <header class="page-header">
      <div class="page-header-info">
        <h1>Capas</h1>
        <p class="subtitle">
          Niveles jerárquicos del proceso LPA.
        </p>
      </div>
      <button
        v-if="authStore.isAdmin"
        class="btn-primary"
        @click="abrirModalCrear"
      >
        <svg class="icon-plus" viewBox="0 0 16 16" aria-hidden="true">
          <path d="M8 2v12M2 8h12" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
        </svg>
        Nueva capa
      </button>
    </header>

    <!-- Stats -->
    <div class="stats">
      <div class="stat">
        <span class="stat-label">Capas totales</span>
        <span class="stat-value">{{ totalCapas }}</span>
      </div>
      <div class="stat">
        <span class="stat-label">Capas activas</span>
        <span class="stat-value stat-active">{{ capasActivas }}</span>
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
          placeholder="Buscar capa por nombre…"
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
      <p>Cargando capas…</p>
    </div>

    <!-- Vacío -->
    <div v-else-if="store.capas.length === 0" class="state state-empty">
      <svg class="state-icon" viewBox="0 0 24 24" aria-hidden="true">
        <path d="M12 3l9 5-9 5-9-5 9-5z" stroke="currentColor" stroke-width="1.6" fill="none" stroke-linejoin="round"/>
        <path d="M3 12l9 5 9-5" stroke="currentColor" stroke-width="1.6" fill="none" stroke-linejoin="round"/>
        <path d="M3 16l9 5 9-5" stroke="currentColor" stroke-width="1.6" fill="none" stroke-linejoin="round"/>
      </svg>
      <h2>Aún no hay capas</h2>
      <p>Comienza creando la primera capa del proceso.</p>
      <button
        v-if="authStore.isAdmin"
        class="btn-primary"
        @click="abrirModalCrear"
      >
        Crear primera capa
      </button>
    </div>

    <!-- Sin resultados -->
    <div v-else-if="capasFiltradas.length === 0" class="state state-empty">
      <svg class="state-icon" viewBox="0 0 24 24" aria-hidden="true">
        <circle cx="10.5" cy="10.5" r="6.5" stroke="currentColor" stroke-width="1.8" fill="none"/>
        <path d="M15.5 15.5L20 20" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/>
      </svg>
      <h2>Sin resultados</h2>
      <p>No hay capas que coincidan con «{{ busqueda }}».</p>
      <button class="btn-secondary" @click="busqueda = ''">
        Limpiar búsqueda
      </button>
    </div>

    <!-- Lista de capas -->
    <div v-else class="capas-list">
      <article
        v-for="c in capasFiltradas"
        :key="c.id"
        class="capa-card"
        :class="{ 'capa-card--inactive': !c.activa }"
      >
        <header class="capa-card-header">
          <div class="capa-card-title">
            <h3>{{ c.nombre }}</h3>
            <span class="badge" :class="c.activa ? 'badge-on' : 'badge-off'">
              {{ c.activa ? 'Activa' : 'Inactiva' }}
            </span>
          </div>
          <div v-if="authStore.isAdmin" class="capa-card-actions">
            <button
              class="icon-btn"
              title="Editar capa"
              aria-label="Editar capa"
              @click="abrirModalEditar(c)"
            >
              <svg viewBox="0 0 16 16" aria-hidden="true">
                <path d="M11.5 2.5l2 2-8 8H3.5v-2l8-8z" stroke="currentColor" stroke-width="1.4" fill="none" stroke-linejoin="round"/>
              </svg>
            </button>
            <button
              class="icon-btn icon-btn--danger"
              title="Eliminar capa"
              aria-label="Eliminar capa"
              @click="eliminarCapa(c)"
            >
              <svg viewBox="0 0 16 16" aria-hidden="true">
                <path d="M2.5 4h11M6.5 4V2.5h3V4M4 4l.5 9.5h7L12 4" stroke="currentColor" stroke-width="1.4" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
            </button>
          </div>
        </header>
        <p class="capa-desc">{{ c.descripcion || 'Sin descripción' }}</p>
      </article>
    </div>

    <!-- Modal: crear capa -->
    <div
      v-if="modalCrearAbierto"
      class="modal-backdrop"
      @click.self="cerrarModalCrear"
    >
      <div class="modal" role="dialog" aria-labelledby="modal-crear-titulo">
        <header class="modal-header">
          <h2 id="modal-crear-titulo">Nueva capa</h2>
          <button class="modal-close" @click="cerrarModalCrear" aria-label="Cerrar">
            <svg viewBox="0 0 16 16" aria-hidden="true">
              <path d="M4 4l8 8M12 4l-8 8" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/>
            </svg>
          </button>
        </header>
        <div class="modal-body">
          <label class="field">
            <span>Nombre</span>
            <input
              v-model="formNombre"
              placeholder="Ej: Auditor"
              autofocus
              @keyup.enter="confirmarCrear"
            />
          </label>
          <label class="field">
            <span>Descripción (opcional)</span>
            <input
              v-model="formDescripcion"
              placeholder="Ej: Capa de auditor"
              @keyup.enter="confirmarCrear"
            />
          </label>
          <p v-if="formError" class="form-error">{{ formError }}</p>
        </div>
        <footer class="modal-footer">
          <button class="btn-secondary" :disabled="formGuardando" @click="cerrarModalCrear">
            Cancelar
          </button>
          <button class="btn-primary" :disabled="formGuardando" @click="confirmarCrear">
            {{ formGuardando ? 'Guardando…' : 'Crear capa' }}
          </button>
        </footer>
      </div>
    </div>

    <!-- Modal: editar capa -->
    <div
      v-if="modalEditarAbierto && capaEditando"
      class="modal-backdrop"
      @click.self="cerrarModalEditar"
    >
      <div class="modal" role="dialog" aria-labelledby="modal-editar-titulo">
        <header class="modal-header">
          <h2 id="modal-editar-titulo">Editar capa</h2>
          <button class="modal-close" @click="cerrarModalEditar" aria-label="Cerrar">
            <svg viewBox="0 0 16 16" aria-hidden="true">
              <path d="M4 4l8 8M12 4l-8 8" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/>
            </svg>
          </button>
        </header>
        <div class="modal-body">
          <label class="field">
            <span>Nombre</span>
            <input
              v-model="formNombre"
              autofocus
              @keyup.enter="confirmarEditar"
            />
          </label>
          <label class="field">
            <span>Descripción (opcional)</span>
            <input
              v-model="formDescripcion"
              @keyup.enter="confirmarEditar"
            />
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
.capas-page {
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

/* --- Lista de capas --- */
.capas-list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.capa-card {
  background: #fff;
  border: 1px solid #e2e8f0;
  border-radius: 0.6rem;
  padding: 1rem 1.1rem;
  box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04);
  transition: border-color 0.15s, box-shadow 0.15s;
}

.capa-card:hover {
  border-color: #cbd5e1;
  box-shadow: 0 2px 6px rgba(15, 23, 42, 0.05);
}

.capa-card--inactive {
  background: #f8fafc;
  opacity: 0.85;
}

.capa-card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.5rem;
}

.capa-card-title {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  flex: 1;
  min-width: 0;
}

.capa-card-title h3 {
  margin: 0;
  font-size: 1.02rem;
  font-weight: 600;
  color: #0f172a;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.capa-card-actions {
  display: flex;
  gap: 0.25rem;
  margin-left: auto;
}

.capa-desc {
  margin: 0.5rem 0 0;
  font-size: 0.85rem;
  color: #64748b;
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

.icon-btn--danger {
  color: #dc2626;
}

.icon-btn--danger:hover {
  background: #fee2e2;
  color: #b91c1c;
  border-color: #fca5a5;
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

.field input {
  padding: 0.55rem 0.75rem;
  border: 1px solid #cbd5e1;
  border-radius: 0.4rem;
  font-size: 0.9rem;
  color: #0f172a;
  background: #fff;
  outline: none;
  transition: border-color 0.15s, box-shadow 0.15s;
}

.field input:focus {
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
