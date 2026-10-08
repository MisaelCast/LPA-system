<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useAuthStore } from '@/stores/auth'
import type { Area } from '@/types/area'
import type {
  EstadoHallazgo,
  HallazgoDetallado,
  HallazgoFiltros,
} from '@/types/hallazgo'
import {
  actualizarSeguimiento,
  listarHallazgos,
} from '@/services/hallazgo.service'
import { obtenerAreasActivas } from '@/services/area.service'

const authStore = useAuthStore()

const cargando = ref(false)
const error = ref('')
const exito = ref('')
const hallazgos = ref<HallazgoDetallado[]>([])
const areas = ref<Area[]>([])

const fEstado = ref<'' | EstadoHallazgo>('')
const fAreaId = ref<number | null>(null)

const detalleAbierto = ref(false)
const hallazgoSeleccionado = ref<HallazgoDetallado | null>(null)
const guardando = ref(false)

const formEstado = ref<EstadoHallazgo>('abierto')
const formAreaId = ref<number | null>(null)
const formAccion = ref('')

const estados: { valor: EstadoHallazgo; label: string }[] = [
  { valor: 'abierto', label: 'Abierto' },
  { valor: 'en_proceso', label: 'En proceso' },
  { valor: 'cerrado', label: 'Cerrado' },
]

const totales = computed(() => ({
  abierto: hallazgos.value.filter((h) => h.estado === 'abierto').length,
  en_proceso: hallazgos.value.filter((h) => h.estado === 'en_proceso').length,
  cerrado: hallazgos.value.filter((h) => h.estado === 'cerrado').length,
}))

const puedeEditar = computed(
  () =>
    hallazgoSeleccionado.value !== null &&
    authStore.usuario?.id === hallazgoSeleccionado.value.auditor_id,
)

onMounted(async () => {
  await Promise.all([cargarAreas(), cargar()])
})

async function cargarAreas() {
  try {
    areas.value = await obtenerAreasActivas()
  } catch {
    areas.value = []
  }
}

async function cargar() {
  cargando.value = true
  error.value = ''
  try {
    const filtros: HallazgoFiltros = {}
    if (fEstado.value) filtros.estado = fEstado.value
    if (fAreaId.value) filtros.area_responsable_id = fAreaId.value
    if (authStore.isSupervisor || authStore.isGerente) filtros.solo_propios = true
    hallazgos.value = await listarHallazgos(filtros)
  } catch (err) {
    error.value =
      (err as { response?: { data?: { detail?: string } } })?.response?.data
        ?.detail || 'Error al cargar los hallazgos.'
  } finally {
    cargando.value = false
  }
}

function limpiarFiltros() {
  fEstado.value = ''
  fAreaId.value = null
  cargar()
}

function formatearFecha(iso: string | null): string {
  if (!iso) return '—'
  const d = new Date(iso)
  if (Number.isNaN(d.getTime())) return iso
  const dia = String(d.getDate()).padStart(2, '0')
  const mes = String(d.getMonth() + 1).padStart(2, '0')
  const anio = d.getFullYear()
  const hh = String(d.getHours()).padStart(2, '0')
  const mm = String(d.getMinutes()).padStart(2, '0')
  return `${dia}/${mes}/${anio} ${hh}:${mm}`
}

function etiquetaEstado(estado: EstadoHallazgo): string {
  return estados.find((e) => e.valor === estado)?.label || estado
}

function chipTipoClase(tipo: string): string {
  return tipo === 'A' ? 'chip-a' : 'chip-r'
}

function etiquetaTipo(tipo: string): string {
  if (tipo === 'R') return 'Mayor'
  if (tipo === 'no_cumple') return 'No cumple'
  return 'Menor'
}

function etiquetaTipoLargo(tipo: string): string {
  if (tipo === 'R') return 'Hallazgo mayor / grave'
  if (tipo === 'no_cumple') return 'Hallazgo de verificación (no cumple)'
  return 'Hallazgo menor'
}

function abrirDetalle(h: HallazgoDetallado) {
  hallazgoSeleccionado.value = h
  formEstado.value = h.estado
  formAreaId.value = h.area_responsable_id
  formAccion.value = h.accion_correctiva || ''
  error.value = ''
  exito.value = ''
  detalleAbierto.value = true
}

function cerrarDetalle() {
  detalleAbierto.value = false
  hallazgoSeleccionado.value = null
}

async function guardarSeguimiento() {
  if (!hallazgoSeleccionado.value || !puedeEditar.value) return
  guardando.value = true
  error.value = ''
  exito.value = ''
  try {
    const actualizado = await actualizarSeguimiento(
      hallazgoSeleccionado.value.id,
      {
        estado: formEstado.value,
        area_responsable_id: formAreaId.value ?? undefined,
        accion_correctiva: formAccion.value.trim() || null,
      },
    )
    const idx = hallazgos.value.findIndex((h) => h.id === actualizado.id)
    if (idx !== -1) hallazgos.value[idx] = actualizado
    hallazgoSeleccionado.value = actualizado
    exito.value = 'Seguimiento guardado correctamente.'
  } catch (err) {
    error.value =
      (err as { response?: { data?: { detail?: string } } })?.response?.data
        ?.detail || 'Error al guardar el seguimiento.'
  } finally {
    guardando.value = false
  }
}
</script>

<template>
  <div class="page">
    <header class="page-header">
      <div class="page-header-info">
        <h1>Mis hallazgos</h1>
        <p class="subtitle">
          Hallazgos detectados en tus auditorías y a los que das seguimiento.
        </p>
      </div>
    </header>

    <div class="stats">
      <div class="stat">
        <span class="stat-label">Abiertos</span>
        <span class="stat-value stat-abierto">{{ totales.abierto }}</span>
      </div>
      <div class="stat">
        <span class="stat-label">En proceso</span>
        <span class="stat-value stat-proceso">{{ totales.en_proceso }}</span>
      </div>
      <div class="stat">
        <span class="stat-label">Cerrados</span>
        <span class="stat-value stat-cerrado">{{ totales.cerrado }}</span>
      </div>
    </div>

    <div class="filtros">
      <select v-model="fEstado" @change="cargar">
        <option value="">Estado: todos</option>
        <option v-for="e in estados" :key="e.valor" :value="e.valor">
          {{ e.label }}
        </option>
      </select>

      <select v-model.number="fAreaId" @change="cargar">
        <option :value="null">Área responsable: todas</option>
        <option v-for="a in areas" :key="a.id" :value="a.id">
          {{ a.nombre }}
        </option>
      </select>

      <button class="btn-secondary" @click="limpiarFiltros">Limpiar</button>
    </div>

    <p v-if="error && !detalleAbierto" class="msg msg-err">{{ error }}</p>

    <div v-if="cargando" class="msg msg-info">Cargando…</div>

    <div v-else-if="hallazgos.length === 0" class="state state-empty">
      <h2>No hay hallazgos</h2>
      <p>Los hallazgos registrados en las auditorías aparecerán aquí.</p>
    </div>

    <div v-else class="table-wrap">
      <table class="table">
        <thead>
          <tr>
            <th>Fecha</th>
            <th>Auditoría</th>
            <th>Descripción</th>
            <th>Tipo</th>
            <th>Área responsable</th>
            <th>Estado</th>
            <th class="col-acciones">Acciones</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="h in hallazgos" :key="h.id" class="row" @click="abrirDetalle(h)">
            <td class="col-fecha">{{ formatearFecha(h.fecha_creacion) }}</td>
            <td class="col-auditoria">{{ h.auditoria_nombre }}</td>
            <td class="col-desc">{{ h.descripcion }}</td>
            <td>
              <span class="chip-tipo" :class="chipTipoClase(h.tipo)">
                {{ etiquetaTipo(h.tipo) }}
              </span>
            </td>
            <td>{{ h.area_responsable_nombre || '—' }}</td>
            <td>
              <span class="badge" :class="'badge-' + h.estado">
                {{ etiquetaEstado(h.estado) }}
              </span>
            </td>
            <td class="col-acciones">
              <button class="btn btn-sm" @click.stop="abrirDetalle(h)">Ver</button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Modal de detalle / seguimiento -->
    <div v-if="detalleAbierto && hallazgoSeleccionado" class="modal-backdrop" @click.self="cerrarDetalle">
      <div class="modal detalle-modal" role="dialog" aria-label="Detalle del hallazgo">
        <header class="modal-header">
          <h2>Detalle del hallazgo</h2>
          <button class="modal-close" @click="cerrarDetalle" aria-label="Cerrar">
            <svg viewBox="0 0 16 16" aria-hidden="true">
              <path d="M4 4l8 8M12 4l-8 8" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/>
            </svg>
          </button>
        </header>

        <div class="modal-body">
          <div class="detalle-encabezado">
            <span class="badge badge-lg" :class="'badge-' + hallazgoSeleccionado.estado">
              {{ etiquetaEstado(hallazgoSeleccionado.estado) }}
            </span>
            <span
              class="chip-tipo"
              :class="chipTipoClase(hallazgoSeleccionado.tipo)"
            >
              {{ etiquetaTipoLargo(hallazgoSeleccionado.tipo) }}
            </span>
          </div>

          <dl class="detalle-grid">
            <div class="dato">
              <dt>Auditoría</dt>
              <dd>{{ hallazgoSeleccionado.auditoria_nombre }}</dd>
            </div>
            <div class="dato">
              <dt>Criterio</dt>
              <dd>
                {{ hallazgoSeleccionado.criterio_orden }}.
                {{ hallazgoSeleccionado.criterio_descripcion }}
              </dd>
            </div>
            <div class="dato">
              <dt>Área responsable</dt>
              <dd>{{ hallazgoSeleccionado.area_responsable_nombre || '—' }}</dd>
            </div>
            <div class="dato">
              <dt>Célula</dt>
              <dd>{{ hallazgoSeleccionado.celula_numero ?? '—' }}</dd>
            </div>
            <div class="dato">
              <dt>Registrado</dt>
              <dd>{{ formatearFecha(hallazgoSeleccionado.fecha_creacion) }}</dd>
            </div>
            <div class="dato">
              <dt>Fecha de cierre</dt>
              <dd>{{ formatearFecha(hallazgoSeleccionado.fecha_cierre) }}</dd>
            </div>
          </dl>

          <section class="bloque">
            <h4>Descripción</h4>
            <p>{{ hallazgoSeleccionado.descripcion }}</p>
          </section>

          <section class="bloque">
            <h4>Acción correctiva</h4>
            <p v-if="hallazgoSeleccionado.accion_correctiva">
              {{ hallazgoSeleccionado.accion_correctiva }}
            </p>
            <p v-else class="vacio">Sin acción correctiva registrada.</p>
          </section>

          <!-- Solo el auditor que registró el hallazgo puede editar -->
          <section v-if="puedeEditar" class="seguimiento-form">
            <h4>Actualizar seguimiento</h4>

            <label class="field">
              <span>Estado</span>
              <select v-model="formEstado">
                <option v-for="e in estados" :key="e.valor" :value="e.valor">
                  {{ e.label }}
                </option>
              </select>
            </label>

            <label class="field">
              <span>Área responsable</span>
              <select v-model.number="formAreaId">
                <option :value="null" disabled>Seleccione el área</option>
                <option v-for="a in areas" :key="a.id" :value="a.id">
                  {{ a.nombre }}
                </option>
              </select>
            </label>

            <label class="field">
              <span>Acción correctiva</span>
              <textarea
                v-model="formAccion"
                class="input"
                rows="3"
                placeholder="Describe la acción correctiva a realizar..."
              ></textarea>
            </label>

            <p v-if="formEstado === 'cerrado'" class="aviso-cierre">
              Al guardar como cerrado se registrará la fecha de cierre.
            </p>

            <p v-if="error" class="msg msg-err">{{ error }}</p>
            <p v-if="exito" class="msg msg-ok">{{ exito }}</p>
          </section>

          <p v-else class="aviso-lectura">
            Solo el auditor que registró el hallazgo puede modificar su seguimiento.
          </p>
        </div>

        <footer class="modal-footer">
          <button class="btn-secondary" @click="cerrarDetalle">Cerrar</button>
          <button
            v-if="puedeEditar"
            class="btn-primary"
            :disabled="guardando"
            @click="guardarSeguimiento"
          >
            {{ guardando ? 'Guardando…' : 'Guardar seguimiento' }}
          </button>
        </footer>
      </div>
    </div>
  </div>
</template>

<style scoped>
.stats {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
  gap: 0.75rem;
  margin-bottom: 1.25rem;
}

.stat {
  background: var(--c-surface, #fff);
  border: 1px solid var(--c-line, #e6e9ef);
  border-radius: var(--r-md, 10px);
  padding: 0.85rem 1rem;
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  box-shadow: var(--sh-sm, 0 1px 2px rgba(15, 23, 42, 0.05));
}

.stat-label {
  font-size: 0.75rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--c-ink-3, #64748b);
  font-weight: 600;
}

.stat-value {
  font-size: 1.6rem;
  font-weight: 800;
  line-height: 1.1;
  font-variant-numeric: tabular-nums;
}

.stat-abierto {
  color: var(--c-warn, #d97706);
}

.stat-proceso {
  color: var(--c-primary, #2563eb);
}

.stat-cerrado {
  color: var(--c-ok, #16a34a);
}

.filtros {
  display: flex;
  gap: 0.6rem;
  flex-wrap: wrap;
  margin-bottom: 1.1rem;
}

.filtros select {
  padding: 0.55rem 0.75rem;
  border: 1px solid var(--c-line-2, #d5dae3);
  border-radius: var(--r-md, 10px);
  background: var(--c-surface, #fff);
  font-size: 0.875rem;
  color: var(--c-ink, #0f172a);
}

.col-fecha {
  white-space: nowrap;
  color: var(--c-ink-3, #64748b);
}

.col-auditoria {
  font-weight: 600;
  color: var(--c-ink, #0f172a);
}

.col-desc {
  max-width: 320px;
  color: var(--c-ink-2, #334155);
}

.chip-tipo {
  padding: 0.15rem 0.55rem;
  border-radius: 999px;
  font-size: 0.72rem;
  font-weight: 700;
  white-space: nowrap;
}

.chip-a {
  background: var(--c-warn-soft, #fef3c7);
  color: var(--c-warn-ink, #92400e);
}

.chip-r {
  background: var(--c-danger-soft, #fee2e2);
  color: var(--c-danger-ink, #b91c1c);
}

.badge-abierto {
  background: var(--c-warn-soft, #fef3c7);
  color: var(--c-warn-ink, #92400e);
}

.badge-en_proceso {
  background: var(--c-primary-soft, #eef2ff);
  color: var(--c-primary-active, #1e40af);
}

.badge-cerrado {
  background: var(--c-ok-soft, #dcfce7);
  color: #166534;
}

.badge-lg {
  padding: 0.28rem 0.85rem;
  font-size: 0.78rem;
}

.detalle-modal {
  width: min(640px, calc(100% - 2rem));
}

/* --- Detalle estructurado --- */
.detalle-encabezado {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  flex-wrap: wrap;
  padding-bottom: 1rem;
  border-bottom: 1px solid var(--c-line, #e6e9ef);
}

.detalle-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 0.9rem 1.5rem;
  margin: 1.1rem 0;
}

.dato {
  display: flex;
  flex-direction: column;
  gap: 0.2rem;
  min-width: 0;
}

.dato dt {
  font-size: 0.7rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--c-ink-3, #64748b);
}

.dato dd {
  margin: 0;
  font-size: 0.9rem;
  color: var(--c-ink, #0f172a);
  overflow-wrap: anywhere;
}

.bloque {
  margin-top: 1rem;
}

.bloque h4,
.seguimiento-form h4 {
  margin: 0 0 0.4rem;
  font-size: 0.72rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--c-ink-3, #64748b);
}

.bloque p {
  margin: 0;
  padding: 0.7rem 0.9rem;
  border-radius: var(--r-md, 10px);
  background: var(--c-surface-3, #f1f5f9);
  font-size: 0.9rem;
  color: var(--c-ink, #0f172a);
  line-height: 1.5;
}

.bloque .vacio {
  color: var(--c-ink-3, #64748b);
  font-style: italic;
}

.seguimiento-form {
  margin-top: 1.25rem;
  padding-top: 1.1rem;
  border-top: 1px solid var(--c-line, #e6e9ef);
  display: flex;
  flex-direction: column;
  gap: 0.85rem;
}

.field {
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
}

.field span {
  font-size: 0.8rem;
  font-weight: 600;
  color: var(--c-ink-2, #334155);
}

.field select,
.field textarea {
  padding: 0.55rem 0.75rem;
  border: 1px solid var(--c-line-2, #d5dae3);
  border-radius: var(--r-md, 10px);
  font-size: 0.9rem;
  color: var(--c-ink, #0f172a);
  background: var(--c-surface, #fff);
  font-family: inherit;
  box-sizing: border-box;
  width: 100%;
}

.field textarea {
  resize: vertical;
}

.aviso-cierre {
  margin: 0;
  font-size: 0.82rem;
  color: var(--c-ok, #16a34a);
}

.aviso-lectura {
  margin: 1.25rem 0 0;
  padding: 0.7rem 0.9rem;
  border-radius: var(--r-md, 10px);
  background: var(--c-surface-3, #f1f5f9);
  font-size: 0.82rem;
  color: var(--c-ink-3, #64748b);
  text-align: center;
}

.btn-sm {
  padding: 0.4rem 0.75rem;
  font-size: 0.82rem;
}

@media (max-width: 560px) {
  .detalle-grid {
    grid-template-columns: 1fr;
  }
}
</style>
