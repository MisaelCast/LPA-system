<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { useAreasStore } from '@/stores/areas'
import { useAuthStore } from '@/stores/auth'
import type { Area, Celula } from '@/types/area'

const store = useAreasStore()
const authStore = useAuthStore()

const busqueda = ref('')

const modalCrearAbierto = ref(false)
const modalEditarAbierto = ref(false)
const areaEditando = ref<Area | null>(null)
const formNombre = ref('')
const formCelulas = ref('')
const formActiva = ref(true)
const formError = ref('')
const formGuardando = ref(false)

const areasExpandidas = ref<Set<number>>(new Set())

function toggleExpand(areaId: number) {
  const next = new Set(areasExpandidas.value)
  if (next.has(areaId)) next.delete(areaId)
  else next.add(areaId)
  areasExpandidas.value = next
}

function estaExpandida(areaId: number): boolean {
  return areasExpandidas.value.has(areaId)
}

interface Toast {
  id: number
  tipo: 'ok' | 'err'
  texto: string
}
const toasts = ref<Toast[]>([])
let toastId = 0

onMounted(async () => {
  await cargarTodo()
})

async function cargarTodo() {
  await store.cargarAreas()
  if (store.areas.length > 0) {
    await store.cargarTodasLasCelulas(store.areas.map((a) => a.id))
  }
}

const areasFiltradas = computed(() => {
  const q = busqueda.value.trim().toLowerCase()
  if (!q) return store.areas
  return store.areas.filter((a) => a.nombre.toLowerCase().includes(q))
})

const totalAreas = computed(() => store.areas.length)
const areasActivas = computed(() => store.areas.filter((a) => a.activa).length)
const totalCelulas = computed(() => {
  let total = 0
  for (const lista of Object.values(store.celulasPorArea)) {
    total += lista.length
  }
  return total
})

function celulasOrdenadas(areaId: number): Celula[] {
  return [...store.celulasDe(areaId)].sort((a, b) => a.numero - b.numero)
}

function parsearCelulas(raw: string): number[] {
  return raw
    .split(',')
    .map((n) => Number(n.trim()))
    .filter((n) => Number.isInteger(n) && n > 0)
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
  formCelulas.value = ''
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
    formError.value = 'El nombre del área es obligatorio.'
    return
  }
  formGuardando.value = true
  try {
    const area = await store.crear({ nombre: formNombre.value.trim(), activa: true })
    const numeros = parsearCelulas(formCelulas.value)
    for (const numero of numeros) {
      try {
        await store.crearCelulaEnArea(area.id, { numero, activa: true })
      } catch {
        // seguimos con las demás
      }
    }
    await store.cargarCelulas(area.id)
    mostrarToast('ok', `Área "${area.nombre}" creada.`)
    modalCrearAbierto.value = false
  } catch (err) {
    mostrarError('crear el área', err)
  } finally {
    formGuardando.value = false
  }
}

/* ——— Modal editar área ——— */
function abrirModalEditar(a: Area) {
  areaEditando.value = a
  formNombre.value = a.nombre
  formActiva.value = a.activa
  formError.value = ''
  modalEditarAbierto.value = true
}

function cerrarModalEditar() {
  if (formGuardando.value) return
  modalEditarAbierto.value = false
  areaEditando.value = null
}

async function confirmarEditar() {
  if (!areaEditando.value) return
  formError.value = ''
  if (!formNombre.value.trim()) {
    formError.value = 'El nombre del área es obligatorio.'
    return
  }
  formGuardando.value = true
  try {
    const area = areaEditando.value
    const nuevoNombre = formNombre.value.trim()
    if (nuevoNombre !== area.nombre) {
      await store.actualizar(area.id, { nombre: nuevoNombre })
    }
    if (formActiva.value !== area.activa) {
      await store.cambiarEstado(area.id, formActiva.value)
    }
    mostrarToast('ok', 'Área actualizada.')
    modalEditarAbierto.value = false
    areaEditando.value = null
  } catch (err) {
    mostrarError('actualizar el área', err)
  } finally {
    formGuardando.value = false
  }
}

/* ——— Agregar célula ——— */
const nuevaCelulaAreaId = ref<number | null>(null)
const nuevaCelulaNumero = ref<number | null>(null)
const celulaAgregando = ref(false)
const celulaErrorAreaId = ref<number | null>(null)

function mostrarInputCelula(areaId: number) {
  nuevaCelulaAreaId.value = areaId
  nuevaCelulaNumero.value = null
  celulaErrorAreaId.value = null
}

function cancelarAgregarCelula() {
  nuevaCelulaAreaId.value = null
  nuevaCelulaNumero.value = null
}

async function confirmarAgregarCelula(areaId: number) {
  if (!nuevaCelulaNumero.value || nuevaCelulaNumero.value <= 0) {
    celulaErrorAreaId.value = areaId
    return
  }
  celulaAgregando.value = true
  celulaErrorAreaId.value = null
  try {
    await store.crearCelulaEnArea(areaId, { numero: nuevaCelulaNumero.value, activa: true })
    mostrarToast('ok', `Célula ${nuevaCelulaNumero.value} agregada.`)
    nuevaCelulaAreaId.value = null
    nuevaCelulaNumero.value = null
  } catch (err) {
    mostrarError('agregar la célula', err)
  } finally {
    celulaAgregando.value = false
  }
}

/* ——— Editar célula ——— */
const celulaEditandoId = ref<number | null>(null)
const celulaEditNumero = ref<number | null>(null)
const celulaEditGuardando = ref(false)

function iniciarEdicionCelula(c: Celula) {
  celulaEditandoId.value = c.id
  celulaEditNumero.value = c.numero
}

function cancelarEdicionCelula() {
  celulaEditandoId.value = null
  celulaEditNumero.value = null
}

async function guardarEdicionCelula(areaId: number) {
  if (!celulaEditandoId.value || !celulaEditNumero.value) return
  celulaEditGuardando.value = true
  try {
    await store.actualizarCelulaEnArea(celulaEditandoId.value, areaId, {
      numero: celulaEditNumero.value,
    })
    mostrarToast('ok', 'Célula actualizada.')
    celulaEditandoId.value = null
    celulaEditNumero.value = null
  } catch (err) {
    mostrarError('actualizar la célula', err)
  } finally {
    celulaEditGuardando.value = false
  }
}

/* ——— Toggle estado célula ——— */
async function toggleEstadoCelula(c: Celula, areaId: number) {
  try {
    await store.cambiarEstadoCelulaEnArea(c.id, areaId, !c.activa)
    mostrarToast('ok', `Célula ${c.activa ? 'desactivada' : 'activada'}.`)
  } catch (err) {
    mostrarError('cambiar el estado de la célula', err)
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
  <div class="areas-page">
    <!-- Encabezado -->
    <header class="page-header">
      <div class="page-header-info">
        <h1>Áreas y células</h1>
        <p class="subtitle">
          Gestiona las áreas de la planta y las células de producción asociadas.
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
        Nueva área
      </button>
    </header>

    <!-- Stats -->
    <div class="stats">
      <div class="stat">
        <span class="stat-label">Áreas totales</span>
        <span class="stat-value">{{ totalAreas }}</span>
      </div>
      <div class="stat">
        <span class="stat-label">Áreas activas</span>
        <span class="stat-value stat-active">{{ areasActivas }}</span>
      </div>
      <div class="stat">
        <span class="stat-label">Células totales</span>
        <span class="stat-value">{{ totalCelulas }}</span>
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
          placeholder="Buscar área por nombre…"
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
      <p>Cargando áreas…</p>
    </div>

    <!-- Vacío -->
    <div v-else-if="store.areas.length === 0" class="state state-empty">
      <svg class="state-icon" viewBox="0 0 24 24" aria-hidden="true">
        <path d="M3 21h18M5 21V10l4-3v3l4-3v3l4-3v11M9 21v-4h2v4M14 21v-4h2v4" stroke="currentColor" stroke-width="1.6" fill="none" stroke-linejoin="round" stroke-linecap="round"/>
      </svg>
      <h2>Aún no hay áreas</h2>
      <p>Comienza creando la primera área de producción.</p>
      <button
        v-if="authStore.isAdmin"
        class="btn-primary"
        @click="abrirModalCrear"
      >
        Crear primera área
      </button>
    </div>

    <!-- Sin resultados de búsqueda -->
    <div
      v-else-if="areasFiltradas.length === 0"
      class="state state-empty"
    >
      <svg class="state-icon" viewBox="0 0 24 24" aria-hidden="true">
        <circle cx="10.5" cy="10.5" r="6.5" stroke="currentColor" stroke-width="1.8" fill="none"/>
        <path d="M15.5 15.5L20 20" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/>
      </svg>
      <h2>Sin resultados</h2>
      <p>No hay áreas que coincidan con «{{ busqueda }}».</p>
      <button class="btn-secondary" @click="busqueda = ''">
        Limpiar búsqueda
      </button>
    </div>

    <!-- Lista colapsable de áreas -->
    <div v-else class="areas-list">
      <article
        v-for="a in areasFiltradas"
        :key="a.id"
        class="area-card"
        :class="[
          { 'area-card--inactive': !a.activa },
          { 'area-card--expanded': estaExpandida(a.id) }
        ]"
      >
        <button
          type="button"
          class="area-card-header"
          :aria-expanded="estaExpandida(a.id)"
          :aria-controls="`area-body-${a.id}`"
          @click="toggleExpand(a.id)"
        >
          <div class="area-card-title">
            <svg class="chevron" :class="{ 'chevron--open': estaExpandida(a.id) }" viewBox="0 0 16 16" aria-hidden="true">
              <path d="M5 3l6 5-6 5" stroke="currentColor" stroke-width="1.8" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
            <h3>{{ a.nombre }}</h3>
            <span class="badge" :class="a.activa ? 'badge-on' : 'badge-off'">
              {{ a.activa ? 'Activa' : 'Inactiva' }}
            </span>
          </div>
          <div class="area-card-meta">
            <span>
              {{ store.celulasDe(a.id).length }} célula{{ store.celulasDe(a.id).length === 1 ? '' : 's' }}
            </span>
            <span class="meta-divider">·</span>
            <span>
              {{ store.celulasDe(a.id).filter((c) => c.activa).length }} activas
            </span>
          </div>
          <div v-if="authStore.isAdmin" class="area-card-actions" @click.stop>
            <button
              class="icon-btn"
              title="Editar área"
              aria-label="Editar área"
              @click="abrirModalEditar(a)"
            >
              <svg viewBox="0 0 16 16" aria-hidden="true">
                <path d="M11.5 2.5l2 2-8 8H3.5v-2l8-8z" stroke="currentColor" stroke-width="1.4" fill="none" stroke-linejoin="round"/>
              </svg>
            </button>
          </div>
        </button>

        <div
          v-show="estaExpandida(a.id)"
          :id="`area-body-${a.id}`"
          class="area-card-body"
        >
          <ul class="cell-list">
            <li
              v-for="c in celulasOrdenadas(a.id)"
              :key="c.id"
              class="cell-item"
              :class="{ 'cell-item--inactive': !c.activa }"
            >
              <template v-if="celulaEditandoId === c.id">
                <div class="cell-edit">
                  <span class="cell-edit-label">N°</span>
                  <input
                    v-model.number="celulaEditNumero"
                    type="number"
                    min="1"
                    class="cell-input"
                    autofocus
                    @keyup.enter="guardarEdicionCelula(a.id)"
                    @keyup.escape="cancelarEdicionCelula"
                  />
                  <div class="cell-actions">
                    <button
                      class="icon-btn icon-btn--ok"
                      :disabled="celulaEditGuardando"
                      title="Guardar"
                      aria-label="Guardar"
                      @click="guardarEdicionCelula(a.id)"
                    >
                      <svg viewBox="0 0 16 16" aria-hidden="true">
                        <path d="M3 8l3.5 3.5L13 5" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
                      </svg>
                    </button>
                    <button
                      class="icon-btn icon-btn--cancel"
                      title="Cancelar"
                      aria-label="Cancelar"
                      @click="cancelarEdicionCelula"
                    >
                      <svg viewBox="0 0 16 16" aria-hidden="true">
                        <path d="M4 4l8 8M12 4l-8 8" stroke="currentColor" stroke-width="1.8" fill="none" stroke-linecap="round"/>
                      </svg>
                    </button>
                  </div>
                </div>
              </template>
              <template v-else>
                <span class="cell-index">#{{ c.numero }}</span>
                <span
                  class="cell-status"
                  :class="c.activa ? 'status-on' : 'status-off'"
                  :title="c.activa ? 'Célula activa' : 'Célula inactiva'"
                >
                  <span class="status-dot"></span>
                  {{ c.activa ? 'Activa' : 'Inactiva' }}
                </span>
                <div v-if="authStore.isAdmin" class="cell-actions">
                  <button
                    class="icon-btn"
                    title="Editar número"
                    aria-label="Editar número de célula"
                    @click="iniciarEdicionCelula(c)"
                  >
                    <svg viewBox="0 0 16 16" aria-hidden="true">
                      <path d="M11.5 2.5l2 2-8 8H3.5v-2l8-8z" stroke="currentColor" stroke-width="1.4" fill="none" stroke-linejoin="round"/>
                    </svg>
                  </button>
                  <button
                    class="icon-btn"
                    :title="c.activa ? 'Desactivar célula' : 'Activar célula'"
                    :aria-label="c.activa ? 'Desactivar célula' : 'Activar célula'"
                    @click="toggleEstadoCelula(c, a.id)"
                  >
                    <svg v-if="c.activa" viewBox="0 0 16 16" aria-hidden="true">
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

          <li
            v-if="nuevaCelulaAreaId === a.id"
            class="cell-item cell-item--adding"
          >
            <div class="cell-edit">
              <span class="cell-edit-label">Nueva N°</span>
              <input
                v-model.number="nuevaCelulaNumero"
                type="number"
                min="1"
                placeholder="Ej: 5"
                class="cell-input"
                autofocus
                @keyup.enter="confirmarAgregarCelula(a.id)"
                @keyup.escape="cancelarAgregarCelula"
              />
              <div class="cell-actions">
                <button
                  class="icon-btn icon-btn--ok"
                  :disabled="celulaAgregando"
                  title="Agregar"
                  aria-label="Agregar célula"
                  @click="confirmarAgregarCelula(a.id)"
                >
                  <svg viewBox="0 0 16 16" aria-hidden="true">
                    <path d="M3 8l3.5 3.5L13 5" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
                  </svg>
                </button>
                <button
                  class="icon-btn icon-btn--cancel"
                  title="Cancelar"
                  aria-label="Cancelar"
                  @click="cancelarAgregarCelula"
                >
                  <svg viewBox="0 0 16 16" aria-hidden="true">
                    <path d="M4 4l8 8M12 4l-8 8" stroke="currentColor" stroke-width="1.8" fill="none" stroke-linecap="round"/>
                  </svg>
                </button>
              </div>
            </div>
          </li>
          <li v-else-if="authStore.isAdmin">
            <button
              class="cell-add-btn"
              @click="mostrarInputCelula(a.id)"
            >
              <svg viewBox="0 0 16 16" aria-hidden="true">
                <path d="M8 2v12M2 8h12" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/>
              </svg>
              Agregar célula
            </button>
          </li>
        </ul>
          <p v-if="celulaErrorAreaId === a.id" class="inline-error">
            Ingresa un número válido mayor a 0.
          </p>
        </div>
      </article>
    </div>

    <!-- Modal: crear área -->
    <div
      v-if="modalCrearAbierto"
      class="modal-backdrop"
      @click.self="cerrarModalCrear"
    >
      <div class="modal" role="dialog" aria-labelledby="modal-crear-titulo">
        <header class="modal-header">
          <h2 id="modal-crear-titulo">Nueva área</h2>
          <button class="modal-close" @click="cerrarModalCrear" aria-label="Cerrar">
            <svg viewBox="0 0 16 16" aria-hidden="true">
              <path d="M4 4l8 8M12 4l-8 8" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/>
            </svg>
          </button>
        </header>
        <div class="modal-body">
          <label class="field">
            <span>Nombre del área</span>
            <input
              v-model="formNombre"
              placeholder="Ej: Ensamble Final"
              autofocus
              @keyup.enter="confirmarCrear"
            />
          </label>
          <label class="field">
            <span>Células iniciales (opcional)</span>
            <input
              v-model="formCelulas"
              placeholder="Ej: 1,2,3,4"
              @keyup.enter="confirmarCrear"
            />
            <small>Separadas por coma. Puedes agregar más después.</small>
          </label>
          <p v-if="formError" class="form-error">{{ formError }}</p>
        </div>
        <footer class="modal-footer">
          <button class="btn-secondary" :disabled="formGuardando" @click="cerrarModalCrear">
            Cancelar
          </button>
          <button class="btn-primary" :disabled="formGuardando" @click="confirmarCrear">
            {{ formGuardando ? 'Guardando…' : 'Crear área' }}
          </button>
        </footer>
      </div>
    </div>

    <!-- Modal: editar área -->
    <div
      v-if="modalEditarAbierto && areaEditando"
      class="modal-backdrop"
      @click.self="cerrarModalEditar"
    >
      <div class="modal" role="dialog" aria-labelledby="modal-editar-titulo">
        <header class="modal-header">
          <h2 id="modal-editar-titulo">Editar área</h2>
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
          <div class="field-toggle">
            <span class="field-toggle-label">Estado</span>
            <label class="switch">
              <input
                type="checkbox"
                v-model="formActiva"
              />
              <span class="switch-track">
                <span class="switch-thumb"></span>
              </span>
              <span class="switch-text">
                {{ formActiva ? 'Activa' : 'Inactiva' }}
              </span>
            </label>
            <small class="field-toggle-hint">
              Las áreas inactivas no aparecen en la selección de auditorías.
            </small>
          </div>
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
.areas-page {
  max-width: 1400px;
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

/* --- Lista colapsable --- */
.areas-list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.area-card {
  background: #fff;
  border: 1px solid #e2e8f0;
  border-radius: 0.6rem;
  box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04);
  transition: border-color 0.15s, box-shadow 0.15s;
  overflow: hidden;
}

.area-card:hover {
  border-color: #cbd5e1;
  box-shadow: 0 2px 6px rgba(15, 23, 42, 0.05);
}

.area-card--expanded {
  border-color: #93c5fd;
  box-shadow: 0 2px 8px rgba(59, 130, 246, 0.08);
}

.area-card--inactive {
  background: #f8fafc;
}

.area-card-header {
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

.area-card-header:hover {
  background: #f8fafc;
}

.area-card-header:focus-visible {
  outline: 2px solid #3b82f6;
  outline-offset: -2px;
}

.area-card-title {
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

.area-card-title h3 {
  margin: 0;
  font-size: 1.02rem;
  font-weight: 600;
  color: #0f172a;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.area-card-actions {
  display: flex;
  gap: 0.25rem;
  margin-left: auto;
}

.area-card-meta {
  font-size: 0.78rem;
  color: #94a3b8;
  display: flex;
  gap: 0.4rem;
  align-items: center;
  white-space: nowrap;
}

.area-card-body {
  border-top: 1px solid #f1f5f9;
  padding: 0.5rem 1.1rem 1rem;
  background: #fafbfc;
}

.meta-divider {
  opacity: 0.6;
}

/* --- Lista de células --- */
.cell-list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  border-top: 1px solid #f1f5f9;
}

.cell-item {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  padding: 0.55rem 0.25rem;
  border-bottom: 1px solid #f1f5f9;
  transition: background 0.15s;
}

.cell-item:hover {
  background: #f8fafc;
  border-radius: 0.3rem;
}

.cell-item--inactive {
  opacity: 0.65;
}

.cell-item--inactive:hover {
  opacity: 0.85;
}

.cell-item:last-child {
  border-bottom: none;
}

.cell-index {
  font-size: 0.95rem;
  font-weight: 700;
  color: #0f172a;
  min-width: 2.5rem;
  font-variant-numeric: tabular-nums;
}

.cell-item--inactive .cell-index {
  color: #64748b;
  text-decoration: line-through;
}

.cell-status {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  font-size: 0.78rem;
  font-weight: 500;
  color: #64748b;
  flex: 1;
}

.status-dot {
  width: 0.5rem;
  height: 0.5rem;
  border-radius: 50%;
  display: inline-block;
}

.status-on {
  color: #166534;
}

.status-on .status-dot {
  background: #16a34a;
  box-shadow: 0 0 0 2px rgba(22, 163, 74, 0.15);
}

.status-off {
  color: #64748b;
}

.status-off .status-dot {
  background: #cbd5e1;
}

.cell-actions {
  display: flex;
  gap: 0.2rem;
  margin-left: auto;
}

.cell-edit {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  flex: 1;
}

.cell-edit-label {
  font-size: 0.75rem;
  color: #94a3b8;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

.cell-input {
  width: 5rem;
  padding: 0.35rem 0.5rem;
  border: 1px solid #93c5fd;
  border-radius: 0.35rem;
  font-size: 0.9rem;
  background: #fff;
  color: #0f172a;
  -moz-appearance: textfield;
  font-variant-numeric: tabular-nums;
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

.cell-item--adding {
  background: #eff6ff;
  border-radius: 0.4rem;
  padding: 0.5rem;
  margin-top: 0.35rem;
  border: 1px dashed #93c5fd;
}

.cell-add-btn {
  width: 100%;
  background: transparent;
  border: 1px dashed #cbd5e1;
  color: #64748b;
  font-size: 0.85rem;
  font-weight: 500;
  padding: 0.55rem 0.75rem;
  border-radius: 0.4rem;
  cursor: pointer;
  margin-top: 0.35rem;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 0.4rem;
  transition: color 0.15s, border-color 0.15s, background 0.15s;
}

.cell-add-btn svg {
  width: 0.95rem;
  height: 0.95rem;
}

.cell-add-btn:hover {
  color: #1d4ed8;
  border-color: #3b82f6;
  background: rgba(59, 130, 246, 0.05);
}

.inline-error {
  margin: 0.5rem 0 0;
  font-size: 0.75rem;
  color: #dc2626;
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

.field small {
  font-size: 0.75rem;
  color: #94a3b8;
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

/* --- Switch toggle --- */
.field-toggle {
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
}

.field-toggle-label {
  font-size: 0.8rem;
  font-weight: 600;
  color: #475569;
}

.field-toggle-hint {
  font-size: 0.75rem;
  color: #94a3b8;
}

.switch {
  display: inline-flex;
  align-items: center;
  gap: 0.65rem;
  cursor: pointer;
  user-select: none;
}

.switch input {
  position: absolute;
  opacity: 0;
  pointer-events: none;
}

.switch-track {
  position: relative;
  width: 2.5rem;
  height: 1.35rem;
  background: #cbd5e1;
  border-radius: 999px;
  transition: background 0.18s;
  flex-shrink: 0;
}

.switch-thumb {
  position: absolute;
  top: 2px;
  left: 2px;
  width: 1.15rem;
  height: 1.15rem;
  background: #fff;
  border-radius: 50%;
  box-shadow: 0 1px 3px rgba(15, 23, 42, 0.2);
  transition: transform 0.18s;
}

.switch input:checked + .switch-track {
  background: #16a34a;
}

.switch input:checked + .switch-track .switch-thumb {
  transform: translateX(1.15rem);
}

.switch input:focus-visible + .switch-track {
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.2);
}

.switch-text {
  font-size: 0.88rem;
  font-weight: 500;
  color: #0f172a;
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
  .area-card-header {
    flex-wrap: wrap;
    padding: 0.75rem 0.9rem;
    gap: 0.5rem;
  }
  .area-card-meta {
    flex-basis: 100%;
    padding-left: 1.55rem;
  }
  .area-card-body {
    padding: 0.5rem 0.9rem 0.9rem;
  }
}
</style>