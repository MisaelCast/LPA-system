<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useAuthStore } from '@/stores/auth'
import type { Area } from '@/types/area'
import type {
  EstadoHallazgo,
  HallazgoDetallado,
  HallazgoFiltros,
  ResponsableResumen,
  Seguimiento,
} from '@/types/hallazgo'
import {
  asignarResponsable,
  listarHallazgos,
  listarHistorial,
  listarResponsables,
  resolverCierre,
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
const fCierrePendiente = ref(false)

const detalleAbierto = ref(false)
const hallazgoSeleccionado = ref<HallazgoDetallado | null>(null)
const historial = ref<Seguimiento[]>([])
const responsables = ref<ResponsableResumen[]>([])
const cargandoDetalle = ref(false)
const guardando = ref(false)

const formResponsableId = ref<number | null>(null)
const formFechaLimite = ref('')
const formObservacion = ref('')

const estados: { valor: EstadoHallazgo; label: string }[] = [
  { valor: 'abierto', label: 'Abierto' },
  { valor: 'en_correccion', label: 'En corrección' },
  { valor: 'cierre_solicitado', label: 'Cierre solicitado' },
  { valor: 'cerrado', label: 'Cerrado' },
]

const totales = computed(() => ({
  abierto: hallazgos.value.filter((h) => h.estado === 'abierto').length,
  en_correccion: hallazgos.value.filter((h) => h.estado === 'en_correccion').length,
  cierre_solicitado: hallazgos.value.filter((h) => h.estado === 'cierre_solicitado').length,
  cerrado: hallazgos.value.filter((h) => h.estado === 'cerrado').length,
}))

const puedeEditar = computed(
  () =>
    hallazgoSeleccionado.value !== null &&
    authStore.usuario?.id === hallazgoSeleccionado.value.auditor_id,
)
const puedeAsignar = computed(
  () => puedeEditar.value && hallazgoSeleccionado.value?.estado !== 'cerrado',
)
const puedeResolverCierre = computed(
  () =>
    puedeEditar.value &&
    hallazgoSeleccionado.value?.estado === 'cierre_solicitado',
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
    if (fCierrePendiente.value) filtros.cierre_pendiente = true
    if (authStore.isSupervisor || authStore.isGerente) filtros.solo_propios = true
    hallazgos.value = await listarHallazgos(filtros)
  } catch (err) {
    error.value = mensajeError(err, 'Error al cargar los hallazgos.')
  } finally {
    cargando.value = false
  }
}

function limpiarFiltros() {
  fEstado.value = ''
  fAreaId.value = null
  fCierrePendiente.value = false
  cargar()
}

function mensajeError(err: unknown, porDefecto: string): string {
  return (
    (err as { response?: { data?: { detail?: string } } })?.response?.data
      ?.detail || porDefecto
  )
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

function aInputLocal(iso: string | null): string {
  if (!iso) return ''
  const d = new Date(iso)
  if (Number.isNaN(d.getTime())) return ''
  const off = d.getTimezoneOffset() * 60000
  return new Date(d.getTime() - off).toISOString().slice(0, 16)
}

function etiquetaEstado(estado: EstadoHallazgo): string {
  return estados.find((e) => e.valor === estado)?.label || estado
}

function chipTipoClase(tipo: string): string {
  return tipo === 'A' ? 'chip-a' : 'chip-r'
}

function etiquetaTipo(tipo: string): string {
  const map: Record<string, string> = {
    asignacion: 'Asignación',
    comentario: 'Comentario',
    accion_correctiva: 'Acción correctiva',
    estado: 'Cambio de estado',
    solicitud_cierre: 'Solicitud de cierre',
    cierre_aprobado: 'Cierre aprobado',
    cierre_rechazado: 'Cierre rechazado',
  }
  return map[tipo] || tipo
}

function etiquetaTipoLargo(tipo: string): string {
  if (tipo === 'R') return 'Hallazgo mayor / grave'
  if (tipo === 'no_cumple') return 'Hallazgo de verificación (no cumple)'
  return 'Hallazgo menor'
}

async function abrirDetalle(h: HallazgoDetallado) {
  hallazgoSeleccionado.value = h
  formResponsableId.value = h.responsable_id
  formFechaLimite.value = aInputLocal(h.fecha_limite)
  formObservacion.value = ''
  responsables.value = []
  historial.value = []
  error.value = ''
  exito.value = ''
  detalleAbierto.value = true
  cargandoDetalle.value = true
  try {
    const [hist, resp] = await Promise.all([
      listarHistorial(h.id),
      listarResponsables(h.id),
    ])
    historial.value = hist
    responsables.value = resp
  } catch {
    /* silencioso */
  } finally {
    cargandoDetalle.value = false
  }
}

function cerrarDetalle() {
  detalleAbierto.value = false
  hallazgoSeleccionado.value = null
}

function actualizarEnLista(actualizado: HallazgoDetallado) {
  const idx = hallazgos.value.findIndex((h) => h.id === actualizado.id)
  if (idx !== -1) hallazgos.value[idx] = actualizado
  hallazgoSeleccionado.value = actualizado
}

async function guardarAsignacion() {
  const h = hallazgoSeleccionado.value
  if (!h || formResponsableId.value === null) {
    error.value = 'Selecciona un responsable.'
    return
  }
  guardando.value = true
  error.value = ''
  exito.value = ''
  try {
    const actualizado = await asignarResponsable(h.id, {
      responsable_id: formResponsableId.value,
      fecha_limite: formFechaLimite.value
        ? new Date(formFechaLimite.value).toISOString()
        : null,
    })
    actualizarEnLista(actualizado)
    formFechaLimite.value = aInputLocal(actualizado.fecha_limite)
    historial.value = await listarHistorial(h.id)
    exito.value = 'Responsable asignado.'
  } catch (err) {
    error.value = mensajeError(err, 'No se pudo asignar el responsable.')
  } finally {
    guardando.value = false
  }
}

async function resolver(aprobar: boolean) {
  const h = hallazgoSeleccionado.value
  if (!h) return
  if (!aprobar && !formObservacion.value.trim()) {
    error.value = 'Indica qué falta corregir al rechazar el cierre.'
    return
  }
  guardando.value = true
  error.value = ''
  exito.value = ''
  try {
    const actualizado = await resolverCierre(h.id, {
      aprobar,
      observacion: formObservacion.value.trim() || null,
    })
    actualizarEnLista(actualizado)
    formObservacion.value = ''
    historial.value = await listarHistorial(h.id)
    exito.value = aprobar ? 'Cierre aprobado.' : 'Cierre devuelto al responsable.'
  } catch (err) {
    error.value = mensajeError(err, 'No se pudo resolver el cierre.')
  } finally {
    guardando.value = false
  }
}
</script>

<template>
  <div class="page">
    <header class="page-header">
      <div class="page-header-info">
        <h1>{{ authStore.isSupervisor || authStore.isGerente ? 'Hallazgos de mis auditorías' : 'Mis hallazgos' }}</h1>
        <p class="subtitle">
          Hallazgos detectados en tus auditorías; asigna responsables y confirma cierres.
        </p>
      </div>
    </header>

    <div class="stats">
      <div class="stat">
        <span class="stat-label">Abiertos</span>
        <span class="stat-value stat-abierto">{{ totales.abierto }}</span>
      </div>
      <div class="stat">
        <span class="stat-label">En corrección</span>
        <span class="stat-value stat-proceso">{{ totales.en_correccion }}</span>
      </div>
      <div class="stat">
        <span class="stat-label">Cierre solicitado</span>
        <span class="stat-value stat-cierre">{{ totales.cierre_solicitado }}</span>
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

      <label class="chk">
        <input v-model="fCierrePendiente" type="checkbox" @change="cargar" />
        Solo cierres pendientes
      </label>

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
            <th>Área</th>
            <th>Responsable</th>
            <th>Estado</th>
            <th class="col-acciones">Acciones</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="h in hallazgos" :key="h.id" class="row" @click="abrirDetalle(h)">
            <td class="col-fecha">{{ formatearFecha(h.fecha_creacion) }}</td>
            <td class="col-auditoria">{{ h.auditoria_nombre }}</td>
            <td class="col-desc">
              {{ h.descripcion }}
              <span v-if="h.evidencias.length" class="foto-contador">
                {{ h.evidencias.length }} foto{{ h.evidencias.length === 1 ? '' : 's' }}
              </span>
            </td>
            <td>
              <span class="chip-tipo" :class="chipTipoClase(h.tipo)">
                {{ h.tipo === 'R' ? 'Mayor' : h.tipo === 'no_cumple' ? 'No cumple' : 'Menor' }}
              </span>
            </td>
            <td>{{ h.area_responsable_nombre || '—' }}</td>
            <td>{{ h.responsable_nombre || '—' }}</td>
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
            <span class="chip-tipo" :class="chipTipoClase(hallazgoSeleccionado.tipo)">
              {{ etiquetaTipoLargo(hallazgoSeleccionado.tipo) }}
            </span>
            <span v-if="hallazgoSeleccionado.atrasado" class="tag-atrasado">atrasado</span>
            <span v-if="hallazgoSeleccionado.reincidente" class="tag-reincidente">reincidente</span>
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
              <dt>Responsable actual</dt>
              <dd>{{ hallazgoSeleccionado.responsable_nombre || 'Sin asignar' }}</dd>
            </div>
            <div class="dato">
              <dt>Fecha límite</dt>
              <dd>{{ formatearFecha(hallazgoSeleccionado.fecha_limite) }}</dd>
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
            <h4>Acción correctiva registrada</h4>
            <p v-if="hallazgoSeleccionado.accion_correctiva">
              {{ hallazgoSeleccionado.accion_correctiva }}
            </p>
            <p v-else class="vacio">Sin acción correctiva registrada.</p>
          </section>

          <section v-if="hallazgoSeleccionado.evidencias.length" class="bloque">
            <h4>Evidencias ({{ hallazgoSeleccionado.evidencias.length }})</h4>
            <div class="evidencias-grid">
              <a
                v-for="ev in hallazgoSeleccionado.evidencias"
                :key="ev.id"
                :href="ev.url ?? undefined"
                target="_blank"
                rel="noopener"
                class="evidencia-thumb"
                :title="ev.tipo === 'correccion' ? 'Evidencia de corrección' : 'Evidencia original'"
              >
                <img :src="ev.url ?? undefined" :alt="`Evidencia ${ev.id}`" loading="lazy" />
                <span class="evidencia-tipo">{{ ev.tipo === 'correccion' ? 'corrección' : 'original' }}</span>
              </a>
            </div>
          </section>

          <!-- Asignar / reasignar responsable -->
          <section v-if="puedeAsignar" class="seguimiento-form">
            <h4>Asignar responsable</h4>
            <label class="field">
              <span>Responsable de Manufactura</span>
              <select v-model.number="formResponsableId">
                <option :value="null" disabled>Seleccione el responsable</option>
                <option v-for="r in responsables" :key="r.id" :value="r.id">
                  {{ r.nombre }}
                </option>
              </select>
              <small v-if="!responsables.length" class="ayuda">
                No hay Responsables de Manufactura registrados para el área.
              </small>
            </label>
            <label class="field">
              <span>Fecha límite</span>
              <input v-model="formFechaLimite" type="datetime-local" />
            </label>
            <div class="acciones-fila">
              <button class="btn-primary" :disabled="guardando" @click="guardarAsignacion">
                {{ guardando ? 'Guardando…' : 'Asignar responsable' }}
              </button>
            </div>
          </section>

          <!-- Resolver solicitud de cierre -->
          <section v-if="puedeResolverCierre" class="seccion-cierre">
            <h4>Solicitud de cierre pendiente</h4>
            <label class="field">
              <span>Observación (obligatoria para rechazar)</span>
              <textarea
                v-model="formObservacion"
                class="input"
                rows="3"
                placeholder="¿Qué falta corregir? / comentario de aprobación..."
              ></textarea>
            </label>
            <div class="acciones-fila">
              <button class="btn-primary" :disabled="guardando" @click="resolver(true)">
                Aprobar cierre
              </button>
              <button class="btn-secondary" :disabled="guardando" @click="resolver(false)">
                Rechazar cierre
              </button>
            </div>
          </section>
          <p v-if="!puedeEditar" class="aviso-lectura">
            Solo el auditor que registró el hallazgo puede asignar responsables o resolver el cierre.
          </p>

          <p v-if="error" class="msg msg-err">{{ error }}</p>
          <p v-if="exito" class="msg msg-ok">{{ exito }}</p>

          <section class="bloque">
            <h4>Historial</h4>
            <div v-if="cargandoDetalle" class="msg msg-info">Cargando…</div>
            <ul v-else-if="historial.length" class="timeline">
              <li v-for="h in historial" :key="h.id" class="timeline-item">
                <span class="timeline-tipo">{{ etiquetaTipo(h.tipo) }}</span>
                <span class="timeline-meta">
                  {{ h.usuario_nombre }} · {{ formatearFecha(h.fecha_creacion) }}
                </span>
                <span v-if="h.detalle" class="timeline-detalle">{{ h.detalle }}</span>
              </li>
            </ul>
            <p v-else class="vacio">Sin movimientos registrados.</p>
          </section>
        </div>

        <footer class="modal-footer">
          <button class="btn-secondary" @click="cerrarDetalle">Cerrar</button>
        </footer>
      </div>
    </div>
  </div>
</template>

<style scoped>
.stats {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
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

.stat-cierre {
  color: #6d28d9;
}

.stat-cerrado {
  color: var(--c-ok, #16a34a);
}

.filtros {
  display: flex;
  gap: 0.6rem;
  flex-wrap: wrap;
  align-items: center;
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

.chk {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  font-size: 0.85rem;
  color: var(--c-ink-2, #334155);
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

.foto-contador {
  display: inline-block;
  margin-left: 0.4rem;
  padding: 0.05rem 0.45rem;
  border-radius: 999px;
  background: var(--c-primary-soft, #eef2ff);
  color: var(--c-primary-active, #1e40af);
  font-size: 0.7rem;
  font-weight: 700;
  white-space: nowrap;
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

.badge-en_correccion {
  background: var(--c-primary-soft, #eef2ff);
  color: var(--c-primary-active, #1e40af);
}

.badge-cierre_solicitado {
  background: #ede9fe;
  color: #6d28d9;
}

.badge-cerrado {
  background: var(--c-ok-soft, #dcfce7);
  color: #166534;
}

.badge-lg {
  padding: 0.28rem 0.85rem;
  font-size: 0.78rem;
}

.tag-atrasado,
.tag-reincidente {
  display: inline-block;
  padding: 0.05rem 0.4rem;
  border-radius: 999px;
  font-size: 0.66rem;
  font-weight: 700;
  text-transform: uppercase;
}

.tag-atrasado {
  background: var(--c-danger-soft, #fee2e2);
  color: var(--c-danger-ink, #b91c1c);
}

.tag-reincidente {
  background: var(--c-warn-soft, #fef3c7);
  color: var(--c-warn-ink, #92400e);
}

.detalle-modal {
  width: min(680px, calc(100% - 2rem));
}

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

.bloque,
.seccion-cierre {
  margin-top: 1rem;
}

.bloque h4,
.seguimiento-form h4,
.seccion-cierre h4 {
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

.evidencias-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.evidencia-thumb {
  position: relative;
  width: 84px;
  height: 84px;
  border-radius: 10px;
  overflow: hidden;
  border: 1px solid var(--c-line, #e6e9ef);
  background: var(--c-surface-3, #f1f5f9);
  display: block;
}

.evidencia-thumb img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.evidencia-tipo {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  font-size: 0.58rem;
  text-align: center;
  background: rgba(15, 23, 42, 0.65);
  color: #fff;
  text-transform: uppercase;
}

.seguimiento-form,
.seccion-cierre {
  margin-top: 1.25rem;
  padding-top: 1.1rem;
  border-top: 1px solid var(--c-line, #e6e9ef);
  display: flex;
  flex-direction: column;
  gap: 0.85rem;
}

.seccion-cierre {
  border-top-color: #ddd6fe;
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
.field input,
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

.ayuda {
  font-size: 0.75rem;
  color: var(--c-ink-3, #64748b);
}

.acciones-fila {
  display: flex;
  gap: 0.6rem;
  flex-wrap: wrap;
}

.btn-sm {
  padding: 0.4rem 0.75rem;
  font-size: 0.82rem;
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

.timeline {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.timeline-item {
  display: flex;
  flex-direction: column;
  gap: 0.15rem;
  padding: 0.5rem 0.7rem;
  border-left: 3px solid var(--c-line-2, #d5dae3);
  background: var(--c-surface-3, #f8fafc);
  border-radius: 0 var(--r-md, 10px) var(--r-md, 10px) 0;
}

.timeline-tipo {
  font-size: 0.78rem;
  font-weight: 700;
  color: var(--c-ink, #0f172a);
}

.timeline-meta {
  font-size: 0.72rem;
  color: var(--c-ink-3, #64748b);
}

.timeline-detalle {
  font-size: 0.85rem;
  color: var(--c-ink-2, #334155);
}

@media (max-width: 560px) {
  .detalle-grid {
    grid-template-columns: 1fr;
  }
}
</style>
