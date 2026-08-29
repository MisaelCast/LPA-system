<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import type { Auditoria } from '@/types/auditoria'
import type {
  EjecucionAuditoriaListItem,
  EjecucionAuditoriaDetalle,
} from '@/types/ejecucion'
import {
  listarEjecuciones,
  obtenerEjecucionDetalle,
  obtenerAuditoriasDisponibles,
} from '@/services/ejecucion.service'

const router = useRouter()

const cargando = ref(false)
const error = ref('')
const ejecuciones = ref<EjecucionAuditoriaListItem[]>([])
const auditorias = ref<Auditoria[]>([])

const fEstado = ref('')
const fAuditoriaId = ref<number | null>(null)
const fFechaDesde = ref('')
const fFechaHasta = ref('')

const detalleAbierto = ref(false)
const detalleCargando = ref(false)
const detalle = ref<EjecucionAuditoriaDetalle | null>(null)

onMounted(async () => {
  await Promise.all([cargar(), cargarAuditorias()])
})

async function cargarAuditorias() {
  try {
    auditorias.value = await obtenerAuditoriasDisponibles()
  } catch {
    auditorias.value = []
  }
}

async function cargar() {
  cargando.value = true
  error.value = ''
  try {
    ejecuciones.value = await listarEjecuciones({
      estado: fEstado.value || undefined,
      auditoria_id: fAuditoriaId.value ?? undefined,
      fecha_desde: fFechaDesde.value || undefined,
      fecha_hasta: fFechaHasta.value || undefined,
    })
  } catch (err) {
    error.value =
      (err as { response?: { data?: { detail?: string } } })?.response?.data
        ?.detail || 'Error al cargar el historial.'
  } finally {
    cargando.value = false
  }
}

function limpiarFiltros() {
  fEstado.value = ''
  fAuditoriaId.value = null
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

function continuar(e: EjecucionAuditoriaListItem) {
  router.push({ name: 'ejecutar', query: { id: String(e.id) } })
}

function continuarDesdeDetalle() {
  const id = detalle.value?.id
  if (id) {
    cerrarDetalle()
    router.push({ name: 'ejecutar', query: { id: String(id) } })
  }
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
      <div>
        <h1>Auditorías realizadas</h1>
        <p class="subtitle">Historial de ejecuciones de auditoría.</p>
      </div>
    </header>

    <!-- Filtros -->
    <div class="filtros">
      <select v-model="fEstado" @change="cargar">
        <option value="">Estado: todos</option>
        <option value="en_proceso">En progreso</option>
        <option value="finalizada">Finalizada</option>
      </select>

      <select v-model.number="fAuditoriaId" @change="cargar">
        <option :value="null">Auditoría: todas</option>
        <option v-for="a in auditorias" :key="a.id" :value="a.id">
          {{ a.nombre }}
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

      <button class="btn btn-secondary" @click="limpiarFiltros">
        Limpiar
      </button>
    </div>

    <p v-if="error" class="msg msg-err">{{ error }}</p>

    <!-- Cargando -->
    <div v-if="cargando" class="msg msg-info">Cargando…</div>

    <!-- Vacío -->
    <div v-else-if="ejecuciones.length === 0" class="msg msg-info">
      No hay ejecuciones registradas.
    </div>

    <!-- Tabla -->
    <table v-else class="table">
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
              class="btn btn-sm btn-secondary"
              @click.stop="abrirDetalle(e)"
            >
              Ver
            </button>
            <button
              v-if="!esFinalizada(e.estado)"
              class="btn btn-sm btn-primary"
              @click.stop="continuar(e)"
            >
              Continuar
            </button>
          </td>
        </tr>
      </tbody>
    </table>

    <!-- Modal detalle -->
    <div
      v-if="detalleAbierto"
      class="modal-backdrop"
      @click.self="cerrarDetalle"
    >
      <div class="modal" role="dialog" aria-label="Detalle de ejecución">
        <header class="modal-header">
          <h2>{{ detalle?.auditoria_nombre || 'Detalle de ejecución' }}</h2>
          <button class="modal-close" @click="cerrarDetalle" aria-label="Cerrar">
            ✕
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
            </div>

            <section class="resumen">
              <h3>Resultado</h3>
              <div class="resumen-chips">
                <span class="stat">
                  <span class="stat-num">{{ detalle.resumen.total_criterios }}</span>
                  <span class="stat-label">criterios</span>
                </span>
                <span class="stat stat-v">
                  <span class="stat-num">{{ detalle.resumen.total_v }}</span>
                  <span class="stat-label">V</span>
                </span>
                <span class="stat stat-a">
                  <span class="stat-num">{{ detalle.resumen.total_a }}</span>
                  <span class="stat-label">A</span>
                </span>
                <span class="stat stat-r">
                  <span class="stat-num">{{ detalle.resumen.total_r }}</span>
                  <span class="stat-label">R</span>
                </span>
              </div>
            </section>

            <section class="criterios-detalle">
              <h3>Criterios</h3>
              <div
                v-for="c in detalle.criterios"
                :key="c.id"
                class="criterio"
              >
                <div class="criterio-head">
                  <span class="criterio-orden">{{ c.orden }}</span>
                  <span class="criterio-desc">{{ c.descripcion }}</span>
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
                  class="criterio-obs"
                >
                  Observación: {{ c.respuesta_observaciones }}
                </div>
                <div
                  v-if="c.hallazgo_id"
                  class="criterio-hallazgo"
                >
                  Hallazgo ({{ c.respuesta_valor === 'R' ? 'mayor' : 'menor' }}):
                  {{ c.hallazgo_descripcion }}
                </div>
              </div>
            </section>
          </template>
        </div>

        <footer class="modal-footer">
          <button class="btn btn-secondary" @click="cerrarDetalle">
            Cerrar
          </button>
          <button
            v-if="detalle && !esFinalizada(detalle.estado)"
            class="btn btn-primary"
            @click="continuarDesdeDetalle"
          >
            Continuar auditoría
          </button>
        </footer>
      </div>
    </div>
  </div>
</template>

<style scoped>
.page {
  max-width: 1400px;
}

.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 1rem;
}

h1 {
  margin: 0;
  font-size: 1.25rem;
  color: #1e293b;
}

.subtitle {
  margin: 0.25rem 0 0;
  color: #64748b;
  font-size: 0.875rem;
}

.filtros {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
  margin-bottom: 1rem;
}

.filtros select,
.filtros input {
  padding: 0.4rem 0.6rem;
  border: 1px solid #e2e8f0;
  border-radius: 0.375rem;
  font-size: 0.85rem;
  background: #fff;
  color: #334155;
}

.filtros select:focus,
.filtros input:focus {
  outline: none;
  border-color: #3b82f6;
}

.msg {
  padding: 0.5rem 0.75rem;
  border-radius: 0.375rem;
  font-size: 0.8rem;
  margin-bottom: 0.75rem;
}

.msg-err {
  background: #fef2f2;
  color: #dc2626;
}

.msg-info {
  background: #f8fafc;
  color: #64748b;
}

.table {
  width: 100%;
  border-collapse: collapse;
  background: #fff;
  border: 1px solid #e2e8f0;
  border-radius: 0.375rem;
  overflow: hidden;
}

th {
  text-align: left;
  padding: 0.5rem 0.75rem;
  background: #f8fafc;
  color: #64748b;
  font-size: 0.72rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.025em;
  border-bottom: 1px solid #e2e8f0;
}

td {
  padding: 0.5rem 0.75rem;
  border-bottom: 1px solid #f1f5f9;
  font-size: 0.85rem;
  color: #334155;
  vertical-align: middle;
}

tr.row {
  cursor: pointer;
}

tr.row:hover {
  background: #f8fafc;
}

tr:last-child td {
  border-bottom: none;
}

.col-fecha {
  white-space: nowrap;
  color: #64748b;
}

.col-auditoria {
  font-weight: 600;
  color: #0f172a;
}

.col-acciones {
  text-align: right;
  white-space: nowrap;
}

.resultado {
  display: inline-flex;
  gap: 0.25rem;
  font-weight: 600;
  font-size: 0.8rem;
}

.resultado .v {
  color: #16a34a;
}

.resultado .a {
  color: #b45309;
}

.resultado .r {
  color: #dc2626;
}

.badge {
  display: inline-block;
  padding: 0.125rem 0.5rem;
  border-radius: 999px;
  font-size: 0.7rem;
  font-weight: 600;
  white-space: nowrap;
}

.badge-finalizada {
  background: #dcfce7;
  color: #166534;
}

.badge-progreso {
  background: #fef3c7;
  color: #92400e;
}

.btn {
  border: none;
  border-radius: 0.375rem;
  cursor: pointer;
  font-size: 0.8rem;
}

.btn-sm {
  padding: 0.25rem 0.6rem;
  font-size: 0.75rem;
}

.btn-primary {
  background: #2563eb;
  color: #fff;
  padding: 0.5rem 1rem;
  font-weight: 600;
}

.btn-primary:hover {
  background: #1d4ed8;
}

.btn-secondary {
  background: #e2e8f0;
  color: #334155;
  padding: 0.5rem 1rem;
}

.btn-secondary:hover {
  background: #cbd5e1;
}

/* Modal */
.modal-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(15, 23, 42, 0.45);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 100;
}

.modal {
  background: #fff;
  border-radius: 0.75rem;
  width: min(680px, calc(100% - 2rem));
  max-height: calc(100vh - 4rem);
  display: flex;
  flex-direction: column;
  box-shadow: 0 20px 40px rgba(15, 23, 42, 0.2);
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
  font-size: 1rem;
  padding: 0.25rem 0.5rem;
  border-radius: 0.3rem;
}

.modal-close:hover {
  background: #f1f5f9;
  color: #0f172a;
}

.modal-body {
  padding: 1.25rem;
  overflow-y: auto;
}

.detalle-info p {
  margin: 0.25rem 0;
  font-size: 0.9rem;
  color: #334155;
}

.resumen {
  margin: 1rem 0;
}

.resumen h3,
.criterios-detalle h3 {
  font-size: 0.85rem;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  color: #64748b;
  margin: 0 0 0.5rem;
}

.resumen-chips {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.stat {
  display: flex;
  flex-direction: column;
  align-items: center;
  background: #f1f5f9;
  border-radius: 0.5rem;
  padding: 0.5rem 1rem;
  min-width: 4rem;
}

.stat-num {
  font-size: 1.4rem;
  font-weight: 700;
  color: #0f172a;
}

.stat-label {
  font-size: 0.7rem;
  color: #64748b;
}

.stat-v .stat-num {
  color: #16a34a;
}

.stat-a .stat-num {
  color: #b45309;
}

.stat-r .stat-num {
  color: #dc2626;
}

.criterios-detalle {
  margin-top: 1rem;
}

.criterio {
  padding: 0.6rem 0.75rem;
  border: 1px solid #e8e8ec;
  border-radius: 0.5rem;
  margin-bottom: 0.5rem;
}

.criterio-head {
  display: flex;
  align-items: center;
  gap: 0.5rem;
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
}

.criterio-desc {
  flex: 1;
  font-size: 0.9rem;
  color: #334155;
}

.chip-valor {
  padding: 0.125rem 0.6rem;
  border-radius: 999px;
  font-size: 0.75rem;
  font-weight: 700;
}

.chip-v {
  background: #dcfce7;
  color: #166534;
}

.chip-a {
  background: #fef3c7;
  color: #92400e;
}

.chip-r {
  background: #fee2e2;
  color: #b91c1c;
}

.chip-sin {
  background: #f1f5f9;
  color: #94a3b8;
}

.criterio-obs {
  margin-top: 0.4rem;
  font-size: 0.82rem;
  color: #b45309;
}

.criterio-hallazgo {
  margin-top: 0.4rem;
  font-size: 0.82rem;
  color: #b91c1c;
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
</style>
