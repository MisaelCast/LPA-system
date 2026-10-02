<script setup lang="ts">
import { onMounted, ref, computed } from 'vue'
import type { Area, Celula } from '@/types/area'
import type { Usuario } from '@/types/auth'
import type {
  EjecucionAuditoriaListItem,
  EjecucionAuditoriaDetalle,
} from '@/types/ejecucion'
import {
  listarEjecuciones,
  obtenerEjecucionDetalle,
  obtenerOpcionesFiltrosRevision,
} from '@/services/ejecucion.service'

const cargando = ref(false)
const error = ref('')
const ejecuciones = ref<EjecucionAuditoriaListItem[]>([])

const areas = ref<Area[]>([])
const celulas = ref<Celula[]>([])
const auditores = ref<Usuario[]>([])

const fEstado = ref('')
const fAreaId = ref<number | null>(null)
const fCelulaId = ref<number | null>(null)
const fAuditorId = ref<number | null>(null)
const fFechaDesde = ref('')
const fFechaHasta = ref('')

const celulasFiltradas = computed(() => {
  if (!fAreaId.value) return celulas.value
  return celulas.value.filter((c) => c.area_id === fAreaId.value)
})

const detalleAbierto = ref(false)
const detalleCargando = ref(false)
const detalle = ref<EjecucionAuditoriaDetalle | null>(null)

onMounted(async () => {
  await Promise.all([cargarOpciones(), cargar()])
})

async function cargarOpciones() {
  try {
    const opciones = await obtenerOpcionesFiltrosRevision()
    areas.value = opciones.areas
    celulas.value = opciones.celulas
    auditores.value = opciones.auditores
  } catch {
    areas.value = []
    celulas.value = []
    auditores.value = []
  }
}

async function cargar() {
  cargando.value = true
  error.value = ''
  try {
    ejecuciones.value = await listarEjecuciones({
      estado: fEstado.value || undefined,
      area_id: fAreaId.value ?? undefined,
      celula_id: fCelulaId.value ?? undefined,
      usuario_id: fAuditorId.value ?? undefined,
      fecha_desde: fFechaDesde.value || undefined,
      fecha_hasta: fFechaHasta.value || undefined,
    })
  } catch (err) {
    error.value =
      (err as { response?: { data?: { detail?: string } } })?.response?.data
        ?.detail || 'Error al cargar las auditorías.'
  } finally {
    cargando.value = false
  }
}

function limpiarFiltros() {
  fEstado.value = ''
  fAreaId.value = null
  fCelulaId.value = null
  fAuditorId.value = null
  fFechaDesde.value = ''
  fFechaHasta.value = ''
  cargar()
}

function formatearFecha(iso: string): string {
  const d = new Date(iso)
  if (Number.isNaN(d.getTime())) return iso
  const dia = String(d.getDate()).padStart(2, '0')
  const mes = String(d.getMonth() + 1).padStart(2, '0')
  const anio = d.getFullYear()
  const hh = String(d.getHours()).padStart(2, '0')
  const mm = String(d.getMinutes()).padStart(2, '0')
  return `${dia}/${mes}/${anio} ${hh}:${mm}`
}

function estadoLabel(estado: string): string {
  return estado === 'finalizada' ? 'Finalizada' : 'En progreso'
}

function esFinalizada(estado: string): boolean {
  return estado === 'finalizada'
}

async function abrirDetalle(e: EjecucionAuditoriaListItem) {
  detalleAbierto.value = true
  detalleCargando.value = true
  detalle.value = null
  try {
    detalle.value = await obtenerEjecucionDetalle(e.id)
  } catch (err) {
    error.value =
      (err as { response?: { data?: { detail?: string } } })?.response?.data
        ?.detail || 'Error al cargar el detalle.'
    detalleAbierto.value = false
  } finally {
    detalleCargando.value = false
  }
}

function cerrarDetalle() {
  detalleAbierto.value = false
  detalle.value = null
}

function claseValor(valor: string | null): string {
  if (valor === 'V') return 'chip-v'
  if (valor === 'A') return 'chip-a'
  if (valor === 'R') return 'chip-r'
  return 'chip-sin'
}
</script>

<template>
  <div class="page">
    <header class="page-header">
      <div class="page-header-info">
        <h1>Revisión de auditorías</h1>
        <p class="subtitle">Consulta las auditorías realizadas por los auditores.</p>
      </div>
    </header>

    <!-- Filtros -->
    <div class="filtros">
      <select v-model="fEstado" @change="cargar">
        <option value="">Estado: todos</option>
        <option value="en_proceso">En progreso</option>
        <option value="finalizada">Finalizada</option>
      </select>

      <select v-model.number="fAreaId" @change="cargar">
        <option :value="null">Área: todas</option>
        <option v-for="a in areas" :key="a.id" :value="a.id">
          {{ a.nombre }}
        </option>
      </select>

      <select v-model.number="fCelulaId" @change="cargar">
        <option :value="null">Célula: todas</option>
        <option v-for="c in celulasFiltradas" :key="c.id" :value="c.id">
          Célula {{ c.numero }}
        </option>
      </select>

      <select v-model.number="fAuditorId" @change="cargar">
        <option :value="null">Auditor: todos</option>
        <option v-for="u in auditores" :key="u.id" :value="u.id">
          {{ u.nombre }}
        </option>
      </select>

      <input
        v-model="fFechaDesde"
        type="date"
        title="Desde"
        @change="cargar"
      />
      <input
        v-model="fFechaHasta"
        type="date"
        title="Hasta"
        @change="cargar"
      />

      <button class="btn-secondary" @click="limpiarFiltros">Limpiar</button>
    </div>

    <p v-if="error" class="msg msg-err">{{ error }}</p>

    <!-- Cargando -->
    <div v-if="cargando" class="msg msg-info">Cargando…</div>

    <!-- Vacío -->
    <div v-else-if="ejecuciones.length === 0" class="state state-empty">
      <svg class="state-icon" viewBox="0 0 24 24" aria-hidden="true">
        <path d="M12 3.2l6.8 2.8V12c0 4.2-2.8 7.2-6.8 8.8C7.8 19.2 5 16.2 5 12V6L12 3.2z" />
        <path d="M9 12l2.1 2.1 4-4" />
      </svg>
      <h2>No hay auditorías para revisar</h2>
      <p>Las ejecuciones de los auditores aparecerán aquí.</p>
    </div>

    <!-- Tabla -->
    <div v-else class="table-wrap">
      <table class="table">
        <thead>
          <tr>
            <th>Fecha</th>
            <th>Auditoría</th>
            <th>Área</th>
            <th>Célula</th>
            <th>Auditor</th>
            <th>Resultado</th>
            <th>Estado</th>
            <th class="col-acciones">Acciones</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="e in ejecuciones"
            :key="e.id"
            class="row"
            @click="abrirDetalle(e)"
          >
            <td class="col-fecha">{{ formatearFecha(e.fecha) }}</td>
            <td class="col-auditoria">{{ e.auditoria_nombre }}</td>
            <td>{{ e.area_nombre || '—' }}</td>
            <td>{{ e.celula_numero ? `Célula ${e.celula_numero}` : '—' }}</td>
            <td>{{ e.usuario_nombre }}</td>
            <td>
              <span class="resultado">
                <span v-if="e.resumen.total_v" class="v">{{ e.resumen.total_v }} V</span>
                <span v-if="e.resumen.total_a" class="a">{{ e.resumen.total_a }} A</span>
                <span v-if="e.resumen.total_r" class="r">{{ e.resumen.total_r }} R</span>
                <span
                  v-if="
                    !e.resumen.total_v && !e.resumen.total_a && !e.resumen.total_r
                  "
                  >—</span
                >
              </span>
            </td>
            <td>
              <span
                class="badge"
                :class="esFinalizada(e.estado) ? 'badge-finalizada' : 'badge-progreso'"
              >
                {{ estadoLabel(e.estado) }}
              </span>
            </td>
            <td class="col-acciones">
              <button
                class="btn btn-sm"
                @click.stop="abrirDetalle(e)"
              >
                Ver
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Modal detalle (solo lectura) -->
    <div
      v-if="detalleAbierto"
      class="modal-backdrop"
      @click.self="cerrarDetalle"
    >
      <div class="modal detalle-modal" role="dialog" aria-label="Detalle de ejecución">
        <header class="modal-header">
          <h2>{{ detalle?.auditoria_nombre || 'Detalle de ejecución' }}</h2>
          <button class="modal-close" @click="cerrarDetalle" aria-label="Cerrar">
            <svg viewBox="0 0 16 16" aria-hidden="true">
              <path d="M4 4l8 8M12 4l-8 8" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/>
            </svg>
          </button>
        </header>

        <div class="modal-body">
          <div v-if="detalleCargando" class="msg msg-info">Cargando…</div>

          <template v-else-if="detalle">
            <div class="detalle-info">
              <p>
                <strong>Fecha:</strong>
                {{ formatearFecha(detalle.fecha) }}
              </p>
              <p><strong>Auditor:</strong> {{ detalle.auditor_nombre }}</p>
              <p><strong>Área:</strong> {{ detalle.area_nombre || '—' }}</p>
              <p>
                <strong>Célula:</strong>
                {{ detalle.celula_numero ? detalle.celula_numero : '—' }}
              </p>
              <p>
                <strong>Estado:</strong>
                <span
                  class="badge"
                  :class="
                    esFinalizada(detalle.estado)
                      ? 'badge-finalizada'
                      : 'badge-progreso'
                  "
                >
                  {{ estadoLabel(detalle.estado) }}
                </span>
              </p>
              <p v-if="detalle.observaciones">
                <strong>Observaciones:</strong> {{ detalle.observaciones }}
              </p>
            </div>

            <section class="resumen">
              <h3>Resultado</h3>
              <div class="chip-stats">
                <span class="chip-stat">
                  <span class="chip-stat-num">{{ detalle.resumen.total_criterios }}</span>
                  <span class="chip-stat-label">criterios</span>
                </span>
                <span class="chip-stat chip-stat-v">
                  <span class="chip-stat-num">{{ detalle.resumen.total_v }}</span>
                  <span class="chip-stat-label">V</span>
                </span>
                <span class="chip-stat chip-stat-a">
                  <span class="chip-stat-num">{{ detalle.resumen.total_a }}</span>
                  <span class="chip-stat-label">A</span>
                </span>
                <span class="chip-stat chip-stat-r">
                  <span class="chip-stat-num">{{ detalle.resumen.total_r }}</span>
                  <span class="chip-stat-label">R</span>
                </span>
              </div>
            </section>

            <section class="criterios-detalle">
              <h3>Criterios</h3>
              <div
                v-for="c in detalle.criterios"
                :key="c.id"
                class="criterio-detalle"
              >
                <div class="criterio-detalle-head">
                  <span class="criterio-detalle-orden">{{ c.orden }}</span>
                  <span class="criterio-detalle-desc">{{ c.descripcion }}</span>
                  <span
                    v-if="c.respuesta_valor"
                    class="chip-valor"
                    :class="claseValor(c.respuesta_valor)"
                  >
                    {{ c.respuesta_valor }}
                  </span>
                  <span v-else class="chip-valor chip-sin">—</span>
                </div>
                <div
                  v-if="c.respuesta_observaciones"
                  class="criterio-detalle-obs"
                >
                  Observación: {{ c.respuesta_observaciones }}
                </div>
                <div
                  v-if="c.hallazgo_id"
                  class="criterio-detalle-hallazgo"
                >
                  Hallazgo ({{ c.respuesta_valor === 'R' ? 'mayor' : 'menor' }}):
                  {{ c.hallazgo_descripcion }}
                </div>
              </div>
            </section>
          </template>
        </div>

        <footer class="modal-footer">
          <button class="btn-secondary" @click="cerrarDetalle">
            Cerrar
          </button>
        </footer>
      </div>
    </div>
  </div>
</template>

<style scoped>
.col-fecha {
  white-space: nowrap;
  color: var(--c-ink-3, #64748b);
}

.col-auditoria {
  font-weight: 600;
  color: var(--c-ink, #0f172a);
}

.resultado {
  display: inline-flex;
  gap: 0.35rem;
  font-weight: 600;
  font-size: 0.8rem;
  white-space: nowrap;
}

.resultado .v {
  color: var(--c-ok, #16a34a);
}

.resultado .a {
  color: var(--c-warn, #d97706);
}

.resultado .r {
  color: var(--c-danger, #dc2626);
}

.detalle-modal {
  width: min(680px, calc(100% - 2rem));
}

.detalle-info p {
  margin: 0.3rem 0;
  font-size: 0.875rem;
  color: var(--c-ink-2, #334155);
}

.resumen,
.criterios-detalle {
  margin-top: 1.25rem;
}

.resumen h3,
.criterios-detalle h3 {
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--c-ink-3, #64748b);
  margin: 0 0 0.55rem;
}

.chip-stats {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.chip-stat {
  display: flex;
  flex-direction: column;
  align-items: center;
  min-width: 4rem;
  padding: 0.55rem 0.9rem;
  border-radius: var(--r-md, 10px);
  background: var(--c-surface-3, #f1f5f9);
}

.chip-stat-num {
  font-size: 1.35rem;
  font-weight: 800;
  color: var(--c-ink, #0f172a);
  font-variant-numeric: tabular-nums;
  line-height: 1.15;
}

.chip-stat-label {
  font-size: 0.7rem;
  color: var(--c-ink-3, #64748b);
}

.chip-stat-v .chip-stat-num {
  color: var(--c-ok, #16a34a);
}

.chip-stat-a .chip-stat-num {
  color: var(--c-warn, #d97706);
}

.chip-stat-r .chip-stat-num {
  color: var(--c-danger, #dc2626);
}

.criterio-detalle {
  padding: 0.65rem 0.8rem;
  border: 1px solid var(--c-line, #e6e9ef);
  border-radius: var(--r-md, 10px);
  margin-bottom: 0.5rem;
}

.criterio-detalle-head {
  display: flex;
  align-items: center;
  gap: 0.6rem;
}

.criterio-detalle-orden {
  min-width: 1.6rem;
  height: 1.6rem;
  border-radius: 50%;
  background: var(--c-surface-3, #f1f5f9);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.75rem;
  font-weight: 700;
  color: var(--c-ink-3, #64748b);
  flex-shrink: 0;
}

.criterio-detalle-desc {
  flex: 1;
  font-size: 0.875rem;
  color: var(--c-ink-2, #334155);
}

.chip-valor {
  padding: 0.15rem 0.6rem;
  border-radius: 999px;
  font-size: 0.75rem;
  font-weight: 700;
  flex-shrink: 0;
}

.criterio-detalle-obs {
  margin-top: 0.45rem;
  font-size: 0.82rem;
  color: var(--c-warn, #d97706);
}

.criterio-detalle-hallazgo {
  margin-top: 0.45rem;
  font-size: 0.82rem;
  color: var(--c-danger, #dc2626);
}
</style>