<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { useAuditoriasStore } from '@/stores/auditorias'
import { useCriteriosStore } from '@/stores/criterios'
import { useAuthStore } from '@/stores/auth'
import { useAreasStore } from '@/stores/areas'
import { useCapasStore } from '@/stores/capas'
import { useFrecuenciasStore } from '@/stores/frecuencias'
import type { Auditoria } from '@/types/auditoria'
import type { Criterio } from '@/types/criterio'

const auditoriaStore = useAuditoriasStore()
const criterioStore = useCriteriosStore()
const authStore = useAuthStore()
const areasStore = useAreasStore()
const capasStore = useCapasStore()
const frecuenciasStore = useFrecuenciasStore()

const busqueda = ref('')
const auditoriasExpandidas = ref<Set<number>>(new Set())

const modalCrearAbierto = ref(false)
const modalEditarAbierto = ref(false)
const auditoriaEditando = ref<Auditoria | null>(null)
const formNombre = ref('')
const formDescripcion = ref('')
const formAreaId = ref<number | null>(null)
const formCapaId = ref<number | null>(null)
const formFrecuenciaId = ref<number | null>(null)
const formError = ref('')
const formGuardando = ref(false)

/* ——— Criterios ——— */
const criterioEditId = ref<number | null>(null)
const criterioEditDesc = ref('')
const criterioEditOrden = ref(1)
const criterioEditGuardando = ref(false)
const nuevaCriterioDesc = ref('')
const nuevaCriterioOrden = ref(1)
const criterioAgregando = ref(false)

interface Toast {
  id: number
  tipo: 'ok' | 'err'
  texto: string
}
const toasts = ref<Toast[]>([])
let toastId = 0

onMounted(async () => {
  await Promise.all([
    auditoriaStore.cargarAuditorias(),
    areasStore.cargarAreas(),
    capasStore.cargarCapas(),
    frecuenciasStore.cargarFrecuencias(),
  ])
  if (auditoriaStore.auditorias.length > 0) {
    await criterioStore.cargarTodosLosCriterios(
      auditoriaStore.auditorias.map((a) => a.id),
    )
  }
})

const auditoriasFiltradas = computed(() => {
  const q = busqueda.value.trim().toLowerCase()
  if (!q) return auditoriaStore.auditorias
  return auditoriaStore.auditorias.filter((a) => a.nombre.toLowerCase().includes(q))
})

const totalAuditorias = computed(() => auditoriaStore.auditorias.length)
const auditoriasActivas = computed(() => auditoriaStore.auditorias.filter((a) => a.activa).length)
const totalCriterios = computed(() => {
  let total = 0
  for (const lista of Object.values(criterioStore.criteriosPorAuditoria)) {
    total += lista.length
  }
  return total
})

function toggleExpand(auditoriaId: number) {
  const next = new Set(auditoriasExpandidas.value)
  if (next.has(auditoriaId)) {
    next.delete(auditoriaId)
  } else {
    next.add(auditoriaId)
    criterioStore.cargarCriterios(auditoriaId)
  }
  auditoriasExpandidas.value = next
}

function estaExpandida(auditoriaId: number): boolean {
  return auditoriasExpandidas.value.has(auditoriaId)
}

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
  formAreaId.value = null
  formCapaId.value = null
  formFrecuenciaId.value = null
  formError.value = ''
  modalCrearAbierto.value = true
}

function cerrarModalCrear() {
  if (formGuardando.value) return
  modalCrearAbierto.value = false
}

async function confirmarCrear() {
  formError.value = ''
  if (!formNombre.value.trim() || !formCapaId.value || !formFrecuenciaId.value) {
    formError.value = 'Complete todos los campos obligatorios.'
    return
  }
  formGuardando.value = true
  try {
    await auditoriaStore.crear({
      nombre: formNombre.value.trim(),
      descripcion: formDescripcion.value.trim() || undefined,
      activa: true,
      area_id: formAreaId.value ?? null,
      capa_id: formCapaId.value,
      frecuencia_id: formFrecuenciaId.value,
    })
    mostrarToast('ok', `Auditoría "${formNombre.value.trim()}" creada.`)
    modalCrearAbierto.value = false
  } catch (err) {
    mostrarError('crear la auditoría', err)
  } finally {
    formGuardando.value = false
  }
}

/* ——— Modal editar ——— */
function abrirModalEditar(a: Auditoria) {
  auditoriaEditando.value = a
  formNombre.value = a.nombre
  formDescripcion.value = a.descripcion || ''
  formAreaId.value = a.area_id
  formCapaId.value = a.capa_id
  formFrecuenciaId.value = a.frecuencia_id
  formError.value = ''
  modalEditarAbierto.value = true
}

function cerrarModalEditar() {
  if (formGuardando.value) return
  modalEditarAbierto.value = false
  auditoriaEditando.value = null
}

async function confirmarEditar() {
  if (!auditoriaEditando.value) return
  formError.value = ''
  if (!formNombre.value.trim() || !formCapaId.value || !formFrecuenciaId.value) {
    formError.value = 'Complete todos los campos obligatorios.'
    return
  }
  formGuardando.value = true
  try {
    await auditoriaStore.actualizar(auditoriaEditando.value.id, {
      nombre: formNombre.value.trim(),
      descripcion: formDescripcion.value.trim() || undefined,
      area_id: formAreaId.value ?? undefined,
      capa_id: formCapaId.value ?? undefined,
      frecuencia_id: formFrecuenciaId.value ?? undefined,
    })
    mostrarToast('ok', 'Auditoría actualizada.')
    modalEditarAbierto.value = false
    auditoriaEditando.value = null
  } catch (err) {
    mostrarError('actualizar la auditoría', err)
  } finally {
    formGuardando.value = false
  }
}

/* ——— Eliminar ——— */
async function eliminarAuditoria(a: Auditoria) {
  if (!window.confirm(`¿Está seguro de que desea eliminar la auditoría "${a.nombre}"?\n\nEsta acción no se puede deshacer.`)) return
  try {
    await auditoriaStore.eliminar(a.id)
    mostrarToast('ok', 'Auditoría eliminada correctamente.')
  } catch (err) {
    mostrarError('eliminar la auditoría', err)
  }
}

/* ——— Criterios: crear ——— */
async function handleCrearCriterio(auditoriaId: number) {
  if (!nuevaCriterioDesc.value.trim()) return
  criterioAgregando.value = true
  try {
    await criterioStore.crearEnAuditoria(auditoriaId, {
      descripcion: nuevaCriterioDesc.value.trim(),
      orden: nuevaCriterioOrden.value || 1,
      activo: true,
    })
    mostrarToast('ok', 'Criterio agregado.')
    nuevaCriterioDesc.value = ''
    nuevaCriterioOrden.value =
      Math.max(0, ...criterioStore.criteriosDe(auditoriaId).map((c) => c.orden)) + 1
  } catch (err) {
    mostrarError('agregar el criterio', err)
  } finally {
    criterioAgregando.value = false
  }
}

/* ——— Criterios: editar ——— */
function iniciarEdicionCriterio(c: Criterio) {
  criterioEditId.value = c.id
  criterioEditDesc.value = c.descripcion
  criterioEditOrden.value = c.orden
}

function cancelarEdicionCriterio() {
  criterioEditId.value = null
}

async function guardarEdicionCriterio(auditoriaId: number) {
  if (!criterioEditId.value) return
  criterioEditGuardando.value = true
  try {
    await criterioStore.actualizar(auditoriaId, criterioEditId.value, {
      descripcion: criterioEditDesc.value,
      orden: criterioEditOrden.value,
    })
    mostrarToast('ok', 'Criterio actualizado.')
    criterioEditId.value = null
  } catch (err) {
    mostrarError('actualizar el criterio', err)
  } finally {
    criterioEditGuardando.value = false
  }
}

/* ——— Criterios: estado ——— */
async function toggleEstadoCriterio(auditoriaId: number, c: Criterio) {
  try {
    await criterioStore.cambiarEstado(auditoriaId, c.id, !c.activo)
    mostrarToast('ok', `Criterio ${c.activo ? 'desactivado' : 'activado'}.`)
  } catch (err) {
    mostrarError('cambiar el estado del criterio', err)
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
  <div class="auditorias-page">
    <!-- Encabezado -->
    <header class="page-header">
      <div class="page-header-info">
        <h1>Auditorías</h1>
        <p class="subtitle">Plantillas y criterios de las auditorías LPA.</p>
      </div>
      <button
        v-if="authStore.isAdmin"
        class="btn-primary"
        @click="abrirModalCrear"
      >
        <svg class="icon-plus" viewBox="0 0 16 16" aria-hidden="true">
          <path d="M8 2v12M2 8h12" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
        </svg>
        Nueva auditoría
      </button>
    </header>

    <!-- Stats -->
    <div class="stats">
      <div class="stat">
        <span class="stat-label">Auditorías totales</span>
        <span class="stat-value">{{ totalAuditorias }}</span>
      </div>
      <div class="stat">
        <span class="stat-label">Auditorías activas</span>
        <span class="stat-value stat-active">{{ auditoriasActivas }}</span>
      </div>
      <div class="stat">
        <span class="stat-label">Criterios totales</span>
        <span class="stat-value">{{ totalCriterios }}</span>
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
          placeholder="Buscar auditoría por nombre…"
        />
        <button v-if="busqueda" class="search-clear" @click="busqueda = ''" title="Limpiar" aria-label="Limpiar búsqueda">
          <svg viewBox="0 0 16 16" aria-hidden="true">
            <path d="M4 4l8 8M12 4l-8 8" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/>
          </svg>
        </button>
      </div>
    </div>

    <!-- Cargando -->
    <div v-if="auditoriaStore.cargando" class="state state-loading">
      <div class="spinner"></div>
      <p>Cargando auditorías…</p>
    </div>

    <!-- Vacío -->
    <div v-else-if="auditoriaStore.auditorias.length === 0" class="state state-empty">
      <svg class="state-icon" viewBox="0 0 24 24" aria-hidden="true">
        <path d="M5 3h14v18H5z" stroke="currentColor" stroke-width="1.6" fill="none" stroke-linejoin="round"/>
        <path d="M8 8h8M8 12h8M8 16h5" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/>
      </svg>
      <h2>Aún no hay auditorías</h2>
      <p>Comienza creando la primera auditoría.</p>
      <button
        v-if="authStore.isAdmin"
        class="btn-primary"
        @click="abrirModalCrear"
      >
        Crear primera auditoría
      </button>
    </div>

    <!-- Sin resultados -->
    <div v-else-if="auditoriasFiltradas.length === 0" class="state state-empty">
      <svg class="state-icon" viewBox="0 0 24 24" aria-hidden="true">
        <circle cx="10.5" cy="10.5" r="6.5" stroke="currentColor" stroke-width="1.8" fill="none"/>
        <path d="M15.5 15.5L20 20" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/>
      </svg>
      <h2>Sin resultados</h2>
      <p>No hay auditorías que coincidan con «{{ busqueda }}».</p>
      <button class="btn-secondary" @click="busqueda = ''">
        Limpiar búsqueda
      </button>
    </div>

    <!-- Lista de auditorías -->
    <div v-else class="auditorias-list">
      <article
        v-for="a in auditoriasFiltradas"
        :key="a.id"
        class="auditoria-card"
        :class="[
          { 'auditoria-card--inactive': !a.activa },
          { 'auditoria-card--expanded': estaExpandida(a.id) }
        ]"
      >
        <button
          type="button"
          class="auditoria-card-header"
          :aria-expanded="estaExpandida(a.id)"
          :aria-controls="`auditoria-body-${a.id}`"
          @click="toggleExpand(a.id)"
        >
          <div class="auditoria-card-title">
            <svg class="chevron" :class="{ 'chevron--open': estaExpandida(a.id) }" viewBox="0 0 16 16" aria-hidden="true">
              <path d="M5 3l6 5-6 5" stroke="currentColor" stroke-width="1.8" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
            <h3>{{ a.nombre }}</h3>
            <span class="badge" :class="a.activa ? 'badge-on' : 'badge-off'">
              {{ a.activa ? 'Activa' : 'Inactiva' }}
            </span>
          </div>
          <div v-if="authStore.isAdmin" class="auditoria-card-actions" @click.stop>
            <button
              class="icon-btn"
              title="Editar auditoría"
              aria-label="Editar auditoría"
              @click="abrirModalEditar(a)"
            >
              <svg viewBox="0 0 16 16" aria-hidden="true">
                <path d="M11.5 2.5l2 2-8 8H3.5v-2l8-8z" stroke="currentColor" stroke-width="1.4" fill="none" stroke-linejoin="round"/>
              </svg>
            </button>
            <button
              class="icon-btn icon-btn--danger"
              title="Eliminar auditoría"
              aria-label="Eliminar auditoría"
              @click="eliminarAuditoria(a)"
            >
              <svg viewBox="0 0 16 16" aria-hidden="true">
                <path d="M2.5 4h11M6.5 4V2.5h3V4M4 4l.5 9.5h7L12 4" stroke="currentColor" stroke-width="1.4" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
            </button>
          </div>
        </button>

        <div class="auditoria-card-meta">
          <span class="badge meta-badge">{{ a.area_nombre || 'Sin área' }}</span>
          <span class="badge meta-badge">{{ a.capa_nombre }}</span>
          <span class="badge meta-badge">{{ a.frecuencia_nombre }}</span>
          <span class="meta-text">
            {{ criterioStore.criteriosDe(a.id).length }} criterios
          </span>
        </div>

        <div
          v-show="estaExpandida(a.id)"
          :id="`auditoria-body-${a.id}`"
          class="auditoria-card-body"
        >
          <div class="criterios-header">Criterios</div>

          <ul v-if="criterioStore.criteriosDe(a.id).length > 0" class="criterio-list">
            <li
              v-for="c in criterioStore.criteriosDe(a.id)"
              :key="c.id"
              class="criterio-item"
              :class="{ 'criterio-item--inactive': !c.activo }"
            >
              <template v-if="criterioEditId === c.id">
                <div class="criterio-edit">
                  <span class="criterio-orden-input">
                    <input v-model.number="criterioEditOrden" type="number" min="1" class="cell-input" />
                  </span>
                  <input v-model="criterioEditDesc" class="criterio-input" @keyup.enter="guardarEdicionCriterio(a.id)" @keyup.escape="cancelarEdicionCriterio" />
                  <div class="criterio-actions">
                    <button class="icon-btn icon-btn--ok" :disabled="criterioEditGuardando" title="Guardar" aria-label="Guardar" @click="guardarEdicionCriterio(a.id)">
                      <svg viewBox="0 0 16 16" aria-hidden="true">
                        <path d="M3 8l3.5 3.5L13 5" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
                      </svg>
                    </button>
                    <button class="icon-btn icon-btn--cancel" title="Cancelar" aria-label="Cancelar" @click="cancelarEdicionCriterio">
                      <svg viewBox="0 0 16 16" aria-hidden="true">
                        <path d="M4 4l8 8M12 4l-8 8" stroke="currentColor" stroke-width="1.8" fill="none" stroke-linecap="round"/>
                      </svg>
                    </button>
                  </div>
                </div>
              </template>
              <template v-else>
                <span class="criterio-orden">{{ c.orden }}</span>
                <span class="criterio-desc">{{ c.descripcion }}</span>
                <div v-if="authStore.isAdmin" class="criterio-actions">
                  <button class="icon-btn" title="Editar criterio" aria-label="Editar criterio" @click="iniciarEdicionCriterio(c)">
                    <svg viewBox="0 0 16 16" aria-hidden="true">
                      <path d="M11.5 2.5l2 2-8 8H3.5v-2l8-8z" stroke="currentColor" stroke-width="1.4" fill="none" stroke-linejoin="round"/>
                    </svg>
                  </button>
                  <button class="icon-btn" :title="c.activo ? 'Desactivar criterio' : 'Activar criterio'" :aria-label="c.activo ? 'Desactivar criterio' : 'Activar criterio'" @click="toggleEstadoCriterio(a.id, c)">
                    <svg v-if="c.activo" viewBox="0 0 16 16" aria-hidden="true">
                      <rect x="4" y="3" width="3" height="10" rx="0.5" fill="currentColor"/>
                      <rect x="9" y="3" width="3" height="10" rx="0.5" fill="currentColor"/>
                    </svg>
                    <svg v-else viewBox="0 0 16 16" aria-hidden="true">
                      <path d="M5 3l8 5-8 5V3z" fill="currentColor"/>
                    </svg>
                  </button>
                </div>
              </template>
            </li>
          </ul>

          <div v-if="authStore.isAdmin" class="criterio-add-bar">
            <input v-model.number="nuevaCriterioOrden" type="number" min="1" class="cell-input" title="Orden" />
            <input v-model="nuevaCriterioDesc" placeholder="Nuevo criterio…" class="criterio-input" @keyup.enter="handleCrearCriterio(a.id)" />
            <button class="btn-primary btn-small" :disabled="criterioAgregando" @click="handleCrearCriterio(a.id)">
              <svg viewBox="0 0 16 16" aria-hidden="true">
                <path d="M8 2v12M2 8h12" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/>
              </svg>
              Agregar
            </button>
          </div>
        </div>
      </article>
    </div>

    <!-- Modal: crear auditoría -->
    <div
      v-if="modalCrearAbierto"
      class="modal-backdrop"
      @click.self="cerrarModalCrear"
    >
      <div class="modal" role="dialog" aria-labelledby="modal-crear-titulo">
        <header class="modal-header">
          <h2 id="modal-crear-titulo">Nueva auditoría</h2>
          <button class="modal-close" @click="cerrarModalCrear" aria-label="Cerrar">
            <svg viewBox="0 0 16 16" aria-hidden="true">
              <path d="M4 4l8 8M12 4l-8 8" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/>
            </svg>
          </button>
        </header>
        <div class="modal-body">
          <label class="field">
            <span>Nombre</span>
            <input v-model="formNombre" placeholder="Ej: Auditoría de Proceso" autofocus />
          </label>
          <label class="field">
            <span>Descripción (opcional)</span>
            <input v-model="formDescripcion" placeholder="Opcional" />
          </label>
          <label class="field">
            <span>Área</span>
            <select v-model.number="formAreaId">
              <option :value="null">Sin área</option>
              <option v-for="ar in areasStore.areas" :key="ar.id" :value="ar.id">{{ ar.nombre }}</option>
            </select>
          </label>
          <label class="field">
            <span>Capa</span>
            <select v-model.number="formCapaId">
              <option :value="null" disabled>Seleccione</option>
              <option v-for="c in capasStore.capas" :key="c.id" :value="c.id">{{ c.nombre }}</option>
            </select>
          </label>
          <label class="field">
            <span>Frecuencia</span>
            <select v-model.number="formFrecuenciaId">
              <option :value="null" disabled>Seleccione</option>
              <option v-for="f in frecuenciasStore.frecuencias" :key="f.id" :value="f.id">{{ f.nombre }}</option>
            </select>
          </label>
          <p v-if="formError" class="form-error">{{ formError }}</p>
        </div>
        <footer class="modal-footer">
          <button class="btn-secondary" :disabled="formGuardando" @click="cerrarModalCrear">
            Cancelar
          </button>
          <button class="btn-primary" :disabled="formGuardando" @click="confirmarCrear">
            {{ formGuardando ? 'Guardando…' : 'Crear auditoría' }}
          </button>
        </footer>
      </div>
    </div>

    <!-- Modal: editar auditoría -->
    <div
      v-if="modalEditarAbierto && auditoriaEditando"
      class="modal-backdrop"
      @click.self="cerrarModalEditar"
    >
      <div class="modal" role="dialog" aria-labelledby="modal-editar-titulo">
        <header class="modal-header">
          <h2 id="modal-editar-titulo">Editar auditoría</h2>
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
            <span>Descripción (opcional)</span>
            <input v-model="formDescripcion" />
          </label>
          <label class="field">
            <span>Área</span>
            <select v-model.number="formAreaId">
              <option :value="null">Sin área</option>
              <option v-for="ar in areasStore.areas" :key="ar.id" :value="ar.id">{{ ar.nombre }}</option>
            </select>
          </label>
          <label class="field">
            <span>Capa</span>
            <select v-model.number="formCapaId">
              <option :value="null" disabled>Seleccione</option>
              <option v-for="c in capasStore.capas" :key="c.id" :value="c.id">{{ c.nombre }}</option>
            </select>
          </label>
          <label class="field">
            <span>Frecuencia</span>
            <select v-model.number="formFrecuenciaId">
              <option :value="null" disabled>Seleccione</option>
              <option v-for="f in frecuenciasStore.frecuencias" :key="f.id" :value="f.id">{{ f.nombre }}</option>
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
.auditorias-page {
  max-width: 1000px;
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

/* --- Lista --- */
.auditorias-list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.auditoria-card {
  background: #fff;
  border: 1px solid #e2e8f0;
  border-radius: 0.6rem;
  box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04);
  transition: border-color 0.15s, box-shadow 0.15s;
  overflow: hidden;
}

.auditoria-card:hover {
  border-color: #cbd5e1;
  box-shadow: 0 2px 6px rgba(15, 23, 42, 0.05);
}

.auditoria-card--expanded {
  border-color: #93c5fd;
  box-shadow: 0 2px 8px rgba(59, 130, 246, 0.08);
}

.auditoria-card--inactive {
  background: #f8fafc;
}

.auditoria-card-header {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  width: 100%;
  background: transparent;
  border: none;
  padding: 0.85rem 1.1rem;
  cursor: pointer;
  text-align: left;
  font: inherit;
  color: inherit;
  transition: background 0.12s;
}

.auditoria-card-header:hover {
  background: #f8fafc;
}

.auditoria-card-header:focus-visible {
  outline: 2px solid #3b82f6;
  outline-offset: -2px;
}

.auditoria-card-title {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  flex: 1;
  min-width: 0;
}

.chevron {
  width: 0.95rem;
  height: 0.95rem;
  color: #94a3b8;
  flex-shrink: 0;
  transition: transform 0.18s ease, color 0.15s;
}

.chevron--open {
  transform: rotate(90deg);
  color: #1d4ed8;
}

.auditoria-card-title h3 {
  margin: 0;
  font-size: 1.02rem;
  font-weight: 600;
  color: #0f172a;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.auditoria-card-actions {
  display: flex;
  gap: 0.25rem;
  margin-left: auto;
}

.auditoria-card-meta {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  flex-wrap: wrap;
  padding: 0 1.1rem 0.85rem;
}

.meta-badge {
  background: #f1f5f9;
  color: #475569;
  text-transform: none;
}

.meta-text {
  font-size: 0.78rem;
  color: #94a3b8;
}

.auditoria-card-body {
  border-top: 1px solid #f1f5f9;
  padding: 0.75rem 1.1rem 1rem;
  background: #fafbfc;
}

.criterios-header {
  font-size: 0.75rem;
  font-weight: 600;
  color: #64748b;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  margin-bottom: 0.5rem;
}

.criterio-list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 0.3rem;
}

.criterio-item {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  padding: 0.45rem 0.6rem;
  border: 1px solid #e8e8ec;
  border-radius: 0.4rem;
  background: #fff;
}

.criterio-item--inactive {
  opacity: 0.55;
}

.criterio-orden {
  min-width: 1.6rem;
  height: 1.6rem;
  border-radius: 50%;
  background: #e8e8ec;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.75rem;
  font-weight: 700;
  color: #555;
  flex-shrink: 0;
}

.criterio-desc {
  flex: 1;
  font-size: 0.88rem;
  color: #334155;
}

.criterio-actions {
  display: flex;
  gap: 0.2rem;
  margin-left: auto;
}

.criterio-edit {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  flex: 1;
}

.criterio-orden-input {
  flex-shrink: 0;
}

.criterio-input {
  flex: 1;
  padding: 0.4rem 0.6rem;
  border: 1px solid #cbd5e1;
  border-radius: 0.35rem;
  font-size: 0.88rem;
  color: #0f172a;
  background: #fff;
  outline: none;
}

.criterio-input:focus {
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.12);
}

.cell-input {
  width: 3rem;
  padding: 0.4rem 0.5rem;
  border: 1px solid #cbd5e1;
  border-radius: 0.35rem;
  font-size: 0.88rem;
  text-align: center;
  background: #fff;
  color: #0f172a;
  -moz-appearance: textfield;
}

.cell-input::-webkit-inner-spin-button,
.cell-input::-webkit-outer-spin-button {
  -webkit-appearance: none;
  margin: 0;
}

.cell-input:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.12);
}

.criterio-add-bar {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-top: 0.6rem;
  padding-top: 0.6rem;
  border-top: 1px dashed #e2e8f0;
}

.btn-small {
  padding: 0.5rem 0.9rem;
  font-size: 0.82rem;
}

.btn-small svg {
  width: 0.85rem;
  height: 0.85rem;
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

.icon-btn--ok {
  color: #16a34a;
}

.icon-btn--ok:hover {
  background: #dcfce7;
  color: #15803d;
  border-color: #86efac;
}

.icon-btn--cancel {
  color: #dc2626;
}

.icon-btn--cancel:hover {
  background: #fee2e2;
  color: #b91c1c;
  border-color: #fca5a5;
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
