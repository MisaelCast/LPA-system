<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import type {
  EstadoHallazgo,
  HallazgoDetallado,
  Seguimiento,
} from '@/types/hallazgo'
import {
  listarHallazgos,
  listarHistorial,
  registrarAvance,
  solicitarCierre,
  subirEvidencia,
} from '@/services/hallazgo.service'

const cargando = ref(false)
const error = ref('')
const exito = ref('')
const tickets = ref<HallazgoDetallado[]>([])

type Vista = 'pendientes' | 'historial'
const vista = ref<Vista>('pendientes')
const fAreaId = ref<number | null>(null)

const detalleAbierto = ref(false)
const seleccionado = ref<HallazgoDetallado | null>(null)
const historial = ref<Seguimiento[]>([])
const cargandoDetalle = ref(false)
const guardando = ref(false)
const subiendo = ref(false)

const formAccion = ref('')
const formComentario = ref('')
const inputFoto = ref<HTMLInputElement | null>(null)

const estados: { valor: EstadoHallazgo; label: string }[] = [
  { valor: 'abierto', label: 'Abierto' },
  { valor: 'en_correccion', label: 'En corrección' },
  { valor: 'cierre_solicitado', label: 'Cierre solicitado' },
  { valor: 'cerrado', label: 'Cerrado' },
]

const ticketsPendientes = computed(() =>
  tickets.value.filter((t) => t.estado !== 'cerrado'),
)
const ticketsCerrados = computed(() =>
  tickets.value.filter((t) => t.estado === 'cerrado'),
)
const atrasadosPendientes = computed(
  () => ticketsPendientes.value.filter((t) => t.atrasado).length,
)

const areasAsignadas = computed(() => {
  const mapa = new Map<number, string>()
  for (const t of tickets.value) {
    if (t.area_responsable_id != null && t.area_responsable_nombre) {
      mapa.set(t.area_responsable_id, t.area_responsable_nombre)
    }
  }
  return [...mapa.entries()]
    .map(([id, nombre]) => ({ id, nombre }))
    .sort((a, b) => a.nombre.localeCompare(b.nombre))
})

const ticketsVisibles = computed(() => {
  const base =
    vista.value === 'historial' ? ticketsCerrados.value : ticketsPendientes.value
  const filtrados =
    fAreaId.value != null
      ? base.filter((t) => t.area_responsable_id === fAreaId.value)
      : base
  return [...filtrados].sort(ordenarTickets)
})

const tituloVacio = computed(() => {
  if (tickets.value.length === 0) return 'Sin hallazgos asignados'
  if (fAreaId.value != null) return 'Sin hallazgos en esta área'
  if (vista.value === 'historial') return 'Aún no hay hallazgos cerrados'
  return 'No tienes hallazgos pendientes'
})

const detalleVacio = computed(() => {
  if (tickets.value.length === 0) {
    return 'Cuando un auditor te asigne un hallazgo aparecerá aquí.'
  }
  if (fAreaId.value != null) {
    return 'Prueba con otra área o quita el filtro.'
  }
  if (vista.value === 'historial') {
    return 'Los hallazgos cerrados se guardarán en este historial.'
  }
  return 'Tus hallazgos asignados están al día.'
})

const puedeAvanzar = computed(() => {
  const t = seleccionado.value
  return t !== null && (t.estado === 'abierto' || t.estado === 'en_correccion')
})
const puedeSolicitarCierre = computed(
  () => seleccionado.value?.estado === 'en_correccion',
)

onMounted(cargar)

async function cargar() {
  cargando.value = true
  error.value = ''
  try {
    tickets.value = await listarHallazgos({ solo_asignados: true })
  } catch (err) {
    error.value = mensajeError(err, 'Error al cargar tus tickets.')
  } finally {
    cargando.value = false
  }
}

const PESO_ESTADO: Record<EstadoHallazgo, number> = {
  abierto: 0,
  en_correccion: 1,
  cierre_solicitado: 2,
  cerrado: 3,
}

function msFecha(iso: string | null | undefined): number {
  if (!iso) return Number.POSITIVE_INFINITY
  const valor = new Date(iso).getTime()
  return Number.isNaN(valor) ? Number.POSITIVE_INFINITY : valor
}

function ordenarTickets(a: HallazgoDetallado, b: HallazgoDetallado): number {
  if (vista.value === 'historial') {
    return (
      msFecha(b.fecha_cierre ?? b.fecha_creacion) -
      msFecha(a.fecha_cierre ?? a.fecha_creacion)
    )
  }
  const atraso = Number(b.atrasado) - Number(a.atrasado)
  if (atraso !== 0) return atraso
  const estado = PESO_ESTADO[a.estado] - PESO_ESTADO[b.estado]
  if (estado !== 0) return estado
  const limiteA = msFecha(a.fecha_limite)
  const limiteB = msFecha(b.fecha_limite)
  if (limiteA !== limiteB) return limiteA - limiteB
  return msFecha(b.fecha_creacion) - msFecha(a.fecha_creacion)
}

function fechaCorta(iso: string | null | undefined): string {
  if (!iso) return ''
  const fecha = new Date(iso)
  if (Number.isNaN(fecha.getTime())) return ''
  return fecha.toLocaleDateString('es-MX', {
    day: 'numeric',
    month: 'short',
  })
}

function textoPlazo(t: HallazgoDetallado): string {
  if (t.estado === 'cerrado') {
    return t.fecha_cierre ? `Cerrado ${fechaCorta(t.fecha_cierre)}` : 'Cerrado'
  }
  if (!t.fecha_limite) return 'Sin fecha límite'
  const limite = new Date(t.fecha_limite)
  if (Number.isNaN(limite.getTime())) return 'Sin fecha límite'

  const hoy = new Date()
  const inicioHoy = new Date(hoy.getFullYear(), hoy.getMonth(), hoy.getDate())
  const inicioLimite = new Date(
    limite.getFullYear(),
    limite.getMonth(),
    limite.getDate(),
  )
  const dias = Math.round(
    (inicioHoy.getTime() - inicioLimite.getTime()) / 86_400_000,
  )

  if (t.atrasado) {
    const vencidos = Math.max(1, dias)
    return vencidos === 1
      ? 'Vencido hace 1 día'
      : `Vencido hace ${vencidos} días`
  }
  if (dias === 0) return 'Vence hoy'
  if (dias === -1) return 'Vence mañana'
  return `Vence ${fechaCorta(t.fecha_limite)}`
}

function etiquetaAccion(t: HallazgoDetallado): string {
  return t.estado === 'abierto' || t.estado === 'en_correccion'
    ? 'Atender'
    : 'Ver'
}

function mostrarArea(t: HallazgoDetallado): boolean {
  const area = t.area_responsable_nombre
  if (!area) return false
  return !t.auditoria_nombre.toLowerCase().includes(area.toLowerCase())
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

function etiquetaEstado(estado: EstadoHallazgo): string {
  return estados.find((e) => e.valor === estado)?.label || estado
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

async function abrirDetalle(t: HallazgoDetallado) {
  seleccionado.value = t
  detalleAbierto.value = true
  formAccion.value = ''
  formComentario.value = ''
  historial.value = []
  cargandoDetalle.value = true
  try {
    historial.value = await listarHistorial(t.id)
  } catch {
    historial.value = []
  } finally {
    cargandoDetalle.value = false
  }
}

function cerrarDetalle() {
  detalleAbierto.value = false
  seleccionado.value = null
}

function actualizarEnLista(actualizado: HallazgoDetallado) {
  const idx = tickets.value.findIndex((t) => t.id === actualizado.id)
  if (idx !== -1) tickets.value[idx] = actualizado
  seleccionado.value = actualizado
}

async function refrescarHistorial() {
  if (!seleccionado.value) return
  historial.value = await listarHistorial(seleccionado.value.id)
}

async function guardarAvance() {
  const t = seleccionado.value
  if (!t) return
  const accion = formAccion.value.trim()
  const comentario = formComentario.value.trim()
  if (!accion && !comentario) {
    error.value = 'Escribe una acción correctiva o un comentario.'
    return
  }
  guardando.value = true
  error.value = ''
  exito.value = ''
  try {
    const actualizado = await registrarAvance(t.id, {
      accion_correctiva: accion || null,
      comentario: comentario || null,
    })
    actualizarEnLista(actualizado)
    formAccion.value = ''
    formComentario.value = ''
    await refrescarHistorial()
    exito.value = 'Avance registrado.'
  } catch (err) {
    error.value = mensajeError(err, 'No se pudo registrar el avance.')
  } finally {
    guardando.value = false
  }
}

async function solicitarCierreTicket() {
  const t = seleccionado.value
  if (!t) return
  guardando.value = true
  error.value = ''
  exito.value = ''
  try {
    const actualizado = await solicitarCierre(t.id, {
      comentario: formComentario.value.trim() || null,
    })
    actualizarEnLista(actualizado)
    await refrescarHistorial()
    exito.value = 'Solicitud de cierre enviada al auditor.'
  } catch (err) {
    error.value = mensajeError(err, 'No se pudo solicitar el cierre.')
  } finally {
    guardando.value = false
  }
}

function abrirSelectorFoto() {
  inputFoto.value?.click()
}

async function onFotoSeleccionada(event: Event) {
  const input = event.target as HTMLInputElement
  const t = seleccionado.value
  if (!t || !input.files?.length) return
  const archivo = input.files[0]
  input.value = ''
  if (!archivo) return
  if (!['image/jpeg', 'image/png', 'image/webp'].includes(archivo.type)) {
    error.value = 'Formato no permitido. Usa JPG, PNG o WEBP.'
    return
  }
  if (archivo.size > 5 * 1024 * 1024) {
    error.value = 'La imagen supera el límite de 5 MB.'
    return
  }
  subiendo.value = true
  error.value = ''
  try {
    const evidencia = await subirEvidencia(t.id, archivo, 'correccion')
    seleccionado.value = {
      ...t,
      evidencias: [...t.evidencias, evidencia],
    }
    actualizarEnLista(seleccionado.value)
    exito.value = 'Evidencia de corrección agregada.'
  } catch (err) {
    error.value = mensajeError(err, 'No se pudo subir la evidencia.')
  } finally {
    subiendo.value = false
  }
}
</script>

<template>
  <div class="page">
    <header class="page-header">
      <div class="page-header-info">
        <h1>Hallazgos asignados</h1>
        <p class="subtitle">
          Revisa primero lo vencido. Registra la corrección y solicita el cierre.
        </p>
      </div>
    </header>

    <div class="barra">
      <div class="vistas" role="tablist" aria-label="Vista de hallazgos">
        <button
          type="button"
          role="tab"
          class="vista"
          :class="{ 'vista--activa': vista === 'pendientes' }"
          :aria-selected="vista === 'pendientes'"
          @click="vista = 'pendientes'"
        >
          Pendientes
          <span class="vista-count">{{ ticketsPendientes.length }}</span>
        </button>
        <button
          type="button"
          role="tab"
          class="vista"
          :class="{ 'vista--activa': vista === 'historial' }"
          :aria-selected="vista === 'historial'"
          @click="vista = 'historial'"
        >
          Historial
          <span class="vista-count">{{ ticketsCerrados.length }}</span>
        </button>
      </div>

      <div class="barra-meta">
        <span v-if="atrasadosPendientes > 0" class="aviso-vencidos">
          <svg viewBox="0 0 24 24" aria-hidden="true">
            <circle cx="12" cy="12" r="8.5" fill="none" stroke="currentColor" stroke-width="1.7"/>
            <path d="M12 7.5V12l3 1.8" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round"/>
          </svg>
          {{ atrasadosPendientes }} vencido{{ atrasadosPendientes === 1 ? '' : 's' }}
        </span>

        <select
          v-if="areasAsignadas.length > 1"
          v-model.number="fAreaId"
          class="area-select"
          aria-label="Filtrar por área"
        >
          <option :value="null">Todas las áreas</option>
          <option v-for="a in areasAsignadas" :key="a.id" :value="a.id">
            {{ a.nombre }}
          </option>
        </select>
      </div>
    </div>

    <p v-if="error && !detalleAbierto" class="msg msg-err">{{ error }}</p>

    <div v-if="cargando" class="ticket-list" aria-hidden="true">
      <div v-for="n in 3" :key="n" class="ticket-skel">
        <span class="ticket-skel-badge"></span>
        <div class="ticket-skel-body">
          <span class="ticket-skel-line ticket-skel-line--desc"></span>
          <span class="ticket-skel-line ticket-skel-line--meta"></span>
        </div>
      </div>
    </div>

    <div v-else-if="ticketsVisibles.length === 0" class="state state-empty">
      <svg class="state-icon" viewBox="0 0 24 24" aria-hidden="true">
        <template v-if="tickets.length === 0">
          <path d="M6 4v16" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/>
          <path d="M6 5h10l-1.8 3.5L16 12H6" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linejoin="round"/>
        </template>
        <template v-else>
          <circle cx="12" cy="12" r="8.4" fill="none" stroke="currentColor" stroke-width="1.6"/>
          <path d="M8.2 12.4l2.6 2.6 5-5.2" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>
        </template>
      </svg>
      <h2>{{ tituloVacio }}</h2>
      <p>{{ detalleVacio }}</p>
    </div>

    <template v-else>
      <div class="lista-head">
        <h2>
          {{ vista === 'pendientes' ? 'Prioridad de atención' : 'Hallazgos cerrados' }}
        </h2>
        <span>
          {{ vista === 'pendientes' ? 'Ordenados por vencimiento y estado' : 'Más recientes primero' }}
        </span>
      </div>

      <div class="ticket-list">
        <button
          v-for="t in ticketsVisibles"
          :key="t.id"
          type="button"
          class="ticket"
          :class="{ 'ticket--vencido': t.atrasado && t.estado !== 'cerrado' }"
          @click="abrirDetalle(t)"
        >
          <span class="ticket-status">
            <span class="badge" :class="'badge-' + t.estado">
              {{ etiquetaEstado(t.estado) }}
            </span>
            <span v-if="t.reincidente" class="ticket-tag">Reincidente</span>
          </span>

          <span class="ticket-body">
            <span class="ticket-desc">{{ t.descripcion }}</span>
            <span class="ticket-context">
              <span class="ticket-auditoria">{{ t.auditoria_nombre }}</span>
              <template v-if="mostrarArea(t)">
                <span class="ticket-sep" aria-hidden="true">·</span>
                {{ t.area_responsable_nombre }}
              </template>
              <template v-if="t.celula_numero">
                <span class="ticket-sep" aria-hidden="true">·</span>
                Célula {{ t.celula_numero }}
              </template>
            </span>
          </span>

          <span class="ticket-side">
            <span
              class="ticket-plazo"
              :class="{ 'ticket-plazo--vencido': t.atrasado && t.estado !== 'cerrado' }"
            >
              <svg viewBox="0 0 24 24" aria-hidden="true">
                <circle cx="12" cy="12" r="8.5" fill="none" stroke="currentColor" stroke-width="1.7"/>
                <path d="M12 7.5V12l3 1.8" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round"/>
              </svg>
              {{ textoPlazo(t) }}
            </span>
            <span class="ticket-accion">
              {{ etiquetaAccion(t) }}
              <svg viewBox="0 0 24 24" aria-hidden="true">
                <path d="M5 12h13M13 6l6 6-6 6" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
            </span>
          </span>
        </button>
      </div>
    </template>

    <!-- Modal detalle -->
    <div v-if="detalleAbierto && seleccionado" class="modal-backdrop" @click.self="cerrarDetalle">
      <div class="modal detalle-modal" role="dialog" aria-label="Detalle del ticket">
        <header class="modal-header detalle-header">
          <div class="detalle-titulo-row">
            <h2>{{ seleccionado.descripcion }}</h2>
            <button class="modal-close" @click="cerrarDetalle" aria-label="Cerrar">
              <svg viewBox="0 0 16 16" aria-hidden="true">
                <path d="M4 4l8 8M12 4l-8 8" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/>
              </svg>
            </button>
          </div>
          <div class="detalle-sub">
            <span class="badge badge-lg" :class="'badge-' + seleccionado.estado">
              {{ etiquetaEstado(seleccionado.estado) }}
            </span>
            <span v-if="seleccionado.atrasado" class="tag-atrasado">atrasado</span>
            <span v-if="seleccionado.reincidente" class="tag-reincidente">reincidente</span>
            <span class="detalle-ticket">Ticket #{{ seleccionado.id }}</span>
            <span class="detalle-sep" aria-hidden="true">·</span>
            <span class="detalle-auditoria">{{ seleccionado.auditoria_nombre }}</span>
          </div>
        </header>

        <div class="modal-body">
          <dl class="detalle-grid">
            <div class="dato dato--full">
              <dt>Criterio</dt>
              <dd>{{ seleccionado.criterio_orden }}. {{ seleccionado.criterio_descripcion }}</dd>
            </div>
            <div class="dato">
              <dt>Área responsable</dt>
              <dd>{{ seleccionado.area_responsable_nombre || '—' }}</dd>
            </div>
            <div class="dato">
              <dt>Fecha límite</dt>
              <dd :class="{ 'fecha-atrasada': seleccionado.atrasado }">
                {{ formatearFecha(seleccionado.fecha_limite) }}
              </dd>
            </div>
            <div class="dato">
              <dt>Registrado</dt>
              <dd>{{ formatearFecha(seleccionado.fecha_creacion) }}</dd>
            </div>
          </dl>

          <section class="bloque">
            <h4>Evidencia original</h4>
            <div
              v-if="seleccionado.evidencias.filter((e) => e.tipo === 'original').length"
              class="evidencias-grid"
            >
              <a
                v-for="ev in seleccionado.evidencias.filter((e) => e.tipo === 'original')"
                :key="'o' + ev.id"
                :href="ev.url ?? undefined"
                target="_blank"
                rel="noopener"
                class="evidencia-thumb"
              >
                <img :src="ev.url ?? undefined" alt="Evidencia original" loading="lazy" />
              </a>
            </div>
            <p v-else class="vacio">Sin evidencia original.</p>
          </section>

          <section class="bloque">
            <h4>Evidencia de corrección</h4>
            <div
              v-if="seleccionado.evidencias.filter((e) => e.tipo === 'correccion').length"
              class="evidencias-grid"
            >
              <a
                v-for="ev in seleccionado.evidencias.filter((e) => e.tipo === 'correccion')"
                :key="'c' + ev.id"
                :href="ev.url ?? undefined"
                target="_blank"
                rel="noopener"
                class="evidencia-thumb"
              >
                <img :src="ev.url ?? undefined" alt="Evidencia de corrección" loading="lazy" />
              </a>
            </div>
            <p v-else class="vacio">Aún no hay evidencia de corrección.</p>
            <button
              v-if="puedeAvanzar"
              type="button"
              class="btn small ghost"
              :disabled="subiendo"
              @click="abrirSelectorFoto"
            >
              {{ subiendo ? 'Subiendo…' : 'Agregar foto de corrección' }}
            </button>
            <input
              ref="inputFoto"
              type="file"
              accept="image/jpeg,image/png,image/webp"
              hidden
              @change="onFotoSeleccionada"
            />
          </section>

          <section v-if="puedeAvanzar" class="seguimiento-form">
            <h4>Registrar avance</h4>
            <label class="field">
              <span>Acción correctiva</span>
              <textarea
                v-model="formAccion"
                class="input"
                rows="3"
                placeholder="Describe la acción correctiva aplicada..."
              ></textarea>
            </label>
            <label class="field">
              <span>Comentario</span>
              <textarea
                v-model="formComentario"
                class="input"
                rows="2"
                placeholder="Comentario adicional (opcional)..."
              ></textarea>
            </label>
            <div class="acciones-fila">
              <button class="btn-primary" :disabled="guardando" @click="guardarAvance">
                {{ guardando ? 'Guardando…' : 'Guardar avance' }}
              </button>
              <button
                v-if="puedeSolicitarCierre"
                class="btn-secondary"
                :disabled="guardando"
                @click="solicitarCierreTicket"
              >
                Solicitar cierre
              </button>
            </div>
            <p v-if="error" class="msg msg-err">{{ error }}</p>
            <p v-if="exito" class="msg msg-ok">{{ exito }}</p>
          </section>
          <p v-else class="aviso-lectura">
            Este ticket está {{ etiquetaEstado(seleccionado.estado).toLowerCase() }}; no admite más cambios.
          </p>

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
/* --- Barra de vistas --- */
.barra {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  flex-wrap: wrap;
  margin-bottom: 1rem;
}

.vistas {
  display: inline-flex;
  gap: 0.25rem;
  padding: 0.25rem;
  border-radius: var(--r-md, 10px);
  background: var(--c-surface-3, #f1f5f9);
}

.vista {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  padding: 0.45rem 0.75rem;
  border: none;
  border-radius: 7px;
  background: transparent;
  color: var(--c-ink-3, #64748b);
  font-family: inherit;
  font-size: 0.82rem;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.15s var(--ease), color 0.15s var(--ease);
}

.vista:hover {
  color: var(--c-ink-2, #334155);
}

.vista--activa {
  background: var(--c-surface, #fff);
  color: var(--c-ink, #0f172a);
  box-shadow: var(--sh-sm, 0 1px 2px rgba(15, 23, 42, 0.05));
}

.vista-count {
  min-width: 1.25rem;
  padding: 0.05rem 0.35rem;
  border-radius: var(--r-pill, 999px);
  background: var(--c-surface-3, #f1f5f9);
  color: var(--c-ink-3, #64748b);
  font-size: 0.68rem;
  font-weight: 700;
  font-variant-numeric: tabular-nums;
  text-align: center;
}

.vista--activa .vista-count {
  background: var(--c-primary-soft, #eef2ff);
  color: var(--c-primary-active, #1e40af);
}

.barra-meta {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  flex-wrap: wrap;
  margin-left: auto;
}

.aviso-vencidos {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  font-size: 0.78rem;
  font-weight: 600;
  color: var(--c-danger-ink, #b91c1c);
  white-space: nowrap;
}

.aviso-vencidos svg {
  width: 0.9rem;
  height: 0.9rem;
}

.area-select {
  padding: 0.45rem 0.7rem;
  border: 1px solid var(--c-line-2, #d5dae3);
  border-radius: var(--r-md, 10px);
  background: var(--c-surface, #fff);
  color: var(--c-ink, #0f172a);
  font-family: inherit;
  font-size: 0.8rem;
}

/* --- Lista de tickets --- */
.lista-head {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 0.75rem;
  flex-wrap: wrap;
  margin-bottom: 0.5rem;
}

.lista-head h2 {
  font-size: 0.82rem;
  font-weight: 700;
  color: var(--c-ink-2, #334155);
}

.lista-head span {
  font-size: 0.72rem;
  color: var(--c-ink-3, #64748b);
}

.ticket-list {
  background: var(--c-surface, #fff);
  border: 1px solid var(--c-line, #e6e9ef);
  border-radius: var(--r-lg, 14px);
  overflow: hidden;
}

.ticket {
  width: 100%;
  display: grid;
  grid-template-columns: 8.5rem minmax(0, 1fr) auto;
  align-items: center;
  gap: 1rem;
  padding: 0.85rem 1rem;
  border: none;
  border-bottom: 1px solid var(--c-line, #e6e9ef);
  background: transparent;
  color: inherit;
  font-family: inherit;
  text-align: left;
  cursor: pointer;
  transition: background 0.15s var(--ease);
}

.ticket:last-child {
  border-bottom: none;
}

.ticket:hover {
  background: var(--c-surface-2, #f8fafc);
}

.ticket:focus-visible {
  outline: 2px solid var(--c-primary, #2563eb);
  outline-offset: -2px;
}

.ticket-status {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 0.35rem;
}

.ticket-tag {
  font-size: 0.64rem;
  font-weight: 700;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  color: var(--c-warn-ink, #92400e);
}

.ticket-body {
  display: flex;
  flex-direction: column;
  gap: 0.2rem;
  min-width: 0;
}

.ticket-desc {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  font-size: 0.86rem;
  font-weight: 600;
  line-height: 1.4;
  color: var(--c-ink, #0f172a);
}

.ticket-context {
  min-width: 0;
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
  font-size: 0.74rem;
  color: var(--c-ink-3, #64748b);
}

.ticket-auditoria {
  color: var(--c-ink-2, #334155);
}

.ticket-sep {
  margin: 0 0.3rem;
  color: var(--c-ink-4, #94a3b8);
}

.ticket-side {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 0.35rem;
  white-space: nowrap;
}

.ticket-plazo {
  display: inline-flex;
  align-items: center;
  gap: 0.3rem;
  font-size: 0.72rem;
  font-weight: 600;
  color: var(--c-ink-3, #64748b);
}

.ticket-plazo svg {
  width: 0.85rem;
  height: 0.85rem;
}

.ticket-plazo--vencido {
  color: var(--c-danger-ink, #b91c1c);
}

.ticket-accion {
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
  font-size: 0.74rem;
  font-weight: 700;
  color: var(--c-ink-3, #64748b);
  transition: color 0.15s var(--ease);
}

.ticket-accion svg {
  width: 0.8rem;
  height: 0.8rem;
}

.ticket:hover .ticket-accion,
.ticket:focus-visible .ticket-accion {
  color: var(--c-primary, #2563eb);
}

/* --- Carga --- */
.ticket-skel {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1rem;
  border-bottom: 1px solid var(--c-line, #e6e9ef);
}

.ticket-skel:last-child {
  border-bottom: none;
}

.ticket-skel-badge,
.ticket-skel-line {
  display: block;
  border-radius: 5px;
  background: linear-gradient(
    90deg,
    var(--c-surface-3, #f1f5f9) 25%,
    var(--c-line, #e6e9ef) 37%,
    var(--c-surface-3, #f1f5f9) 63%
  );
  background-size: 400% 100%;
  animation: ticket-shimmer 1.4s ease infinite;
}

.ticket-skel-badge {
  width: 4.5rem;
  height: 1.2rem;
}

.ticket-skel-body {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 0.45rem;
}

.ticket-skel-line--desc {
  width: 60%;
  height: 0.8rem;
}

.ticket-skel-line--meta {
  width: 38%;
  height: 0.65rem;
}

@keyframes ticket-shimmer {
  from {
    background-position: 100% 50%;
  }
  to {
    background-position: 0 50%;
  }
}

.fecha-atrasada {
  color: var(--c-danger, #dc2626);
  font-weight: 600;
}

.tag-atrasado,
.tag-reincidente {
  display: inline-block;
  margin-left: 0.35rem;
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

.detalle-modal {
  width: min(720px, calc(100% - 2rem));
}

.detalle-header {
  flex-direction: column;
  align-items: stretch;
  gap: 0.55rem;
}

.detalle-titulo-row {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 1rem;
}

.detalle-header h2 {
  margin: 0;
  font-size: 1.05rem;
  line-height: 1.35;
  letter-spacing: -0.01em;
  color: var(--c-ink, #0f172a);
}

.detalle-sub {
  display: flex;
  align-items: center;
  gap: 0.45rem;
  flex-wrap: wrap;
}

.detalle-ticket {
  font-size: 0.72rem;
  font-weight: 600;
  color: var(--c-ink-3, #64748b);
}

.detalle-sep {
  color: var(--c-ink-4, #94a3b8);
}

.detalle-auditoria {
  font-size: 0.78rem;
  color: var(--c-ink-3, #64748b);
}

.detalle-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 0.9rem 1.5rem;
  margin: 0;
}

.dato--full {
  grid-column: 1 / -1;
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

.evidencias-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  margin-bottom: 0.5rem;
}

.evidencia-thumb {
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
  resize: vertical;
}

.acciones-fila {
  display: flex;
  gap: 0.6rem;
  flex-wrap: wrap;
}

.btn.ghost {
  background: transparent;
  border: 1px dashed var(--c-line, #cbd5e1);
  color: var(--c-ink-2, #334155);
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
  position: relative;
  display: flex;
  flex-direction: column;
  gap: 0.15rem;
  padding: 0.5rem 0.7rem 0.5rem 1.5rem;
  background: var(--c-surface-2, #f8fafc);
  border-radius: var(--r-sm, 8px);
}

.timeline-item::before {
  content: '';
  position: absolute;
  top: 0.8rem;
  left: 0.7rem;
  width: 0.35rem;
  height: 0.35rem;
  border-radius: 50%;
  background: var(--c-ink-4, #94a3b8);
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

@media (max-width: 720px) {
  .barra {
    align-items: stretch;
  }

  .vistas {
    width: 100%;
  }

  .vista {
    flex: 1;
    justify-content: center;
  }

  .barra-meta {
    width: 100%;
    margin-left: 0;
    justify-content: space-between;
  }

  .area-select {
    width: 100%;
  }

  .ticket {
    grid-template-columns: 1fr;
    gap: 0.6rem;
    padding: 0.85rem 0.9rem;
  }

  .ticket-status {
    flex-direction: row;
    align-items: center;
    gap: 0.5rem;
  }

  .ticket-desc {
    -webkit-line-clamp: 3;
  }

  .ticket-side {
    flex-direction: row;
    align-items: center;
    justify-content: space-between;
    gap: 0.75rem;
    padding-top: 0.55rem;
    border-top: 1px solid var(--c-line, #e6e9ef);
  }
}

@media (max-width: 560px) {
  .detalle-grid {
    grid-template-columns: 1fr;
  }

  .detalle-header h2 {
    font-size: 0.98rem;
  }
}

@media (prefers-reduced-motion: reduce) {
  .ticket-skel-badge,
  .ticket-skel-line {
    animation: none;
  }
}
</style>
