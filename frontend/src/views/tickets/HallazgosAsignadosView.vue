<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import type { Area } from '@/types/area'
import type {
  EstadoHallazgo,
  HallazgoDetallado,
  HallazgoFiltros,
  Seguimiento,
} from '@/types/hallazgo'
import {
  listarHallazgos,
  listarHistorial,
  registrarAvance,
  solicitarCierre,
  subirEvidencia,
} from '@/services/hallazgo.service'
import { obtenerAreasActivas } from '@/services/area.service'

const cargando = ref(false)
const error = ref('')
const exito = ref('')
const tickets = ref<HallazgoDetallado[]>([])
const areas = ref<Area[]>([])

const fEstado = ref<'' | EstadoHallazgo>('')
const fAreaId = ref<number | null>(null)
const fAtrasados = ref(false)

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

const totales = computed(() => ({
  abierto: tickets.value.filter((t) => t.estado === 'abierto').length,
  en_correccion: tickets.value.filter((t) => t.estado === 'en_correccion').length,
  cierre_solicitado: tickets.value.filter((t) => t.estado === 'cierre_solicitado').length,
  atrasados: tickets.value.filter((t) => t.atrasado).length,
}))

const puedeAvanzar = computed(() => {
  const t = seleccionado.value
  return t !== null && (t.estado === 'abierto' || t.estado === 'en_correccion')
})
const puedeSolicitarCierre = computed(
  () => seleccionado.value?.estado === 'en_correccion',
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
    const filtros: HallazgoFiltros = { solo_asignados: true }
    if (fEstado.value) filtros.estado = fEstado.value
    if (fAreaId.value) filtros.area_responsable_id = fAreaId.value
    if (fAtrasados.value) filtros.atrasados = true
    tickets.value = await listarHallazgos(filtros)
  } catch (err) {
    error.value = mensajeError(err, 'Error al cargar tus tickets.')
  } finally {
    cargando.value = false
  }
}

function limpiarFiltros() {
  fEstado.value = ''
  fAreaId.value = null
  fAtrasados.value = false
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
          Hallazgos asignados a tu área. Registra la corrección y solicita el cierre.
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
        <span class="stat-label">Atrasados</span>
        <span class="stat-value stat-atrasado">{{ totales.atrasados }}</span>
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
        <option :value="null">Área: todas</option>
        <option v-for="a in areas" :key="a.id" :value="a.id">
          {{ a.nombre }}
        </option>
      </select>

      <label class="chk">
        <input v-model="fAtrasados" type="checkbox" @change="cargar" />
        Solo atrasados
      </label>

      <button class="btn-secondary" @click="limpiarFiltros">Limpiar</button>
    </div>

    <p v-if="error && !detalleAbierto" class="msg msg-err">{{ error }}</p>

    <div v-if="cargando" class="msg msg-info">Cargando…</div>

    <div v-else-if="tickets.length === 0" class="state state-empty">
      <h2>Sin tickets asignados</h2>
      <p>Cuando un auditor te asigne un hallazgo aparecerá aquí.</p>
    </div>

    <div v-else class="table-wrap">
      <table class="table">
        <thead>
          <tr>
            <th>Fecha</th>
            <th>Auditoría</th>
            <th>Descripción</th>
            <th>Área</th>
            <th>Fecha límite</th>
            <th>Estado</th>
            <th class="col-acciones">Acciones</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="t in tickets" :key="t.id" class="row" @click="abrirDetalle(t)">
            <td class="col-fecha">{{ formatearFecha(t.fecha_creacion) }}</td>
            <td class="col-auditoria">{{ t.auditoria_nombre }}</td>
            <td class="col-desc">{{ t.descripcion }}</td>
            <td>{{ t.area_responsable_nombre || '—' }}</td>
            <td class="col-fecha" :class="{ 'fecha-atrasada': t.atrasado }">
              {{ formatearFecha(t.fecha_limite) }}
              <span v-if="t.atrasado" class="tag-atrasado">atrasado</span>
            </td>
            <td>
              <span class="badge" :class="'badge-' + t.estado">
                {{ etiquetaEstado(t.estado) }}
              </span>
            </td>
            <td class="col-acciones">
              <button class="btn btn-sm" @click.stop="abrirDetalle(t)">Ver</button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Modal detalle -->
    <div v-if="detalleAbierto && seleccionado" class="modal-backdrop" @click.self="cerrarDetalle">
      <div class="modal detalle-modal" role="dialog" aria-label="Detalle del ticket">
        <header class="modal-header">
          <h2>Ticket #{{ seleccionado.id }}</h2>
          <button class="modal-close" @click="cerrarDetalle" aria-label="Cerrar">
            <svg viewBox="0 0 16 16" aria-hidden="true">
              <path d="M4 4l8 8M12 4l-8 8" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/>
            </svg>
          </button>
        </header>

        <div class="modal-body">
          <div class="detalle-encabezado">
            <span class="badge badge-lg" :class="'badge-' + seleccionado.estado">
              {{ etiquetaEstado(seleccionado.estado) }}
            </span>
            <span v-if="seleccionado.atrasado" class="tag-atrasado">atrasado</span>
            <span v-if="seleccionado.reincidente" class="tag-reincidente">reincidente</span>
          </div>

          <dl class="detalle-grid">
            <div class="dato">
              <dt>Auditoría</dt>
              <dd>{{ seleccionado.auditoria_nombre }}</dd>
            </div>
            <div class="dato">
              <dt>Área responsable</dt>
              <dd>{{ seleccionado.area_responsable_nombre || '—' }}</dd>
            </div>
            <div class="dato">
              <dt>Fecha límite</dt>
              <dd>{{ formatearFecha(seleccionado.fecha_limite) }}</dd>
            </div>
            <div class="dato">
              <dt>Registrado</dt>
              <dd>{{ formatearFecha(seleccionado.fecha_creacion) }}</dd>
            </div>
          </dl>

          <section class="bloque">
            <h4>Descripción del hallazgo</h4>
            <p>{{ seleccionado.descripcion }}</p>
          </section>

          <section class="bloque">
            <h4>Criterio</h4>
            <p>{{ seleccionado.criterio_orden }}. {{ seleccionado.criterio_descripcion }}</p>
          </section>

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
  color: var(--c-primary-active, #1e40af);
}

.stat-atrasado {
  color: var(--c-danger, #dc2626);
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
  max-width: 300px;
  color: var(--c-ink-2, #334155);
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
