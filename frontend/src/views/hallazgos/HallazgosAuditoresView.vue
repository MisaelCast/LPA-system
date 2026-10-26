<script setup lang="ts">
import { computed, nextTick, onMounted, onUnmounted, ref } from 'vue'
import { listarHallazgos, listarHistorial } from '@/services/hallazgo.service'
import type {
  EstadoHallazgo,
  HallazgoDetallado,
  Seguimiento,
} from '@/types/hallazgo'

type Vista = 'todos' | 'atrasados' | 'cierre_pendiente' | 'sin_actualizar' | 'reincidencia'

const vistas: { valor: Vista; etiqueta: string }[] = [
  { valor: 'todos', etiqueta: 'Todos' },
  { valor: 'atrasados', etiqueta: 'Atrasados' },
  { valor: 'cierre_pendiente', etiqueta: 'Por cerrar' },
  { valor: 'sin_actualizar', etiqueta: 'Sin actualizar' },
  { valor: 'reincidencia', etiqueta: 'Reincidentes' },
]

const ESTADO_LABEL: Record<EstadoHallazgo, string> = {
  abierto: 'Abierto',
  en_correccion: 'En corrección',
  cierre_solicitado: 'Cierre solicitado',
  cerrado: 'Cerrado',
}

const SEGUIMIENTO_LABEL: Record<string, string> = {
  asignacion: 'Responsable asignado',
  comentario: 'Comentario',
  accion_correctiva: 'Acción correctiva',
  estado: 'Cambio de estado',
  solicitud_cierre: 'Solicitud de cierre',
  cierre_aprobado: 'Cierre aprobado',
  cierre_rechazado: 'Cierre rechazado',
}

const hallazgos = ref<HallazgoDetallado[]>([])
const cargando = ref(false)
const error = ref('')

const vista = ref<Vista>('todos')
const busqueda = ref('')

const drawerAbierto = ref(false)
const hallazgoSeleccionado = ref<HallazgoDetallado | null>(null)
const historial = ref<Seguimiento[]>([])
const historialCargando = ref(false)
const historialError = ref('')
const btnCerrarDetalles = ref<HTMLButtonElement | null>(null)

let focoPrevio: HTMLElement | null = null
let overflowPrevio = ''

onMounted(() => {
  cargar()
  window.addEventListener('keydown', alPresionarTecla)
})

onUnmounted(() => {
  window.removeEventListener('keydown', alPresionarTecla)
  document.body.style.overflow = overflowPrevio
})

async function cargar() {
  cargando.value = true
  error.value = ''
  try {
    hallazgos.value = await listarHallazgos({ solo_auditores: true })
  } catch {
    hallazgos.value = []
    error.value = 'No se pudieron cargar los hallazgos. Verifica tu conexión e intenta de nuevo.'
  } finally {
    cargando.value = false
  }
}

function coincideVista(h: HallazgoDetallado, valor: Vista): boolean {
  if (valor === 'atrasados') return h.atrasado && h.estado !== 'cerrado'
  if (valor === 'cierre_pendiente') return h.estado === 'cierre_solicitado'
  if (valor === 'sin_actualizar') {
    return h.estado !== 'cerrado' && (h.dias_sin_actualizar ?? 0) > 0
  }
  if (valor === 'reincidencia') return h.estado !== 'cerrado' && h.reincidente
  return true
}

const conteos = computed<Record<Vista, number>>(() => {
  const resultado = {} as Record<Vista, number>
  for (const v of vistas) {
    resultado[v.valor] = hallazgos.value.filter((h) => coincideVista(h, v.valor)).length
  }
  return resultado
})

function normalizar(texto: string): string {
  return texto.normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase()
}

function coincideBusqueda(h: HallazgoDetallado): boolean {
  const q = normalizar(busqueda.value.trim())
  if (!q) return true
  return [
    h.descripcion,
    h.auditoria_nombre,
    h.area_responsable_nombre ?? '',
    h.responsable_nombre ?? '',
    h.criterio_descripcion,
  ].some((campo) => normalizar(campo).includes(q))
}

function urgencia(h: HallazgoDetallado): number {
  if (h.estado === 'cerrado') return 5
  if (h.atrasado) return 0
  if (h.estado === 'cierre_solicitado') return 1
  if (h.estado === 'en_correccion') return 2
  return 3
}

function tiempo(iso: string | null): number {
  if (!iso) return Number.MAX_SAFE_INTEGER
  const t = new Date(iso).getTime()
  return Number.isNaN(t) ? Number.MAX_SAFE_INTEGER : t
}

const listaMostrada = computed(() =>
  hallazgos.value
    .filter((h) => coincideVista(h, vista.value) && coincideBusqueda(h))
    .sort(
      (a, b) =>
        urgencia(a) - urgencia(b) ||
        tiempo(a.fecha_limite) - tiempo(b.fecha_limite) ||
        tiempo(b.fecha_creacion) - tiempo(a.fecha_creacion),
    ),
)

function tipoInfo(tipo: string): { etiqueta: string; clase: string } {
  if (tipo === 'R') return { etiqueta: 'Mayor', clase: 'tipo--mayor' }
  if (tipo === 'no_cumple') return { etiqueta: 'No cumple', clase: 'tipo--no-cumple' }
  return { etiqueta: 'Menor', clase: 'tipo--menor' }
}

const fmtFecha = new Intl.DateTimeFormat('es-MX', {
  day: '2-digit',
  month: 'short',
  year: 'numeric',
})

const fmtFechaHora = new Intl.DateTimeFormat('es-MX', {
  day: '2-digit',
  month: 'short',
  year: 'numeric',
  hour: '2-digit',
  minute: '2-digit',
})

function fechaCorta(iso: string | null): string {
  if (!iso) return 'Sin fecha'
  const d = new Date(iso)
  return Number.isNaN(d.getTime()) ? '—' : fmtFecha.format(d)
}

function fechaHora(iso: string): string {
  const d = new Date(iso)
  return Number.isNaN(d.getTime()) ? iso : fmtFechaHora.format(d)
}

function diasAtraso(h: HallazgoDetallado): number {
  if (!h.fecha_limite) return 0
  const limite = new Date(h.fecha_limite).getTime()
  if (Number.isNaN(limite)) return 0
  return Math.max(0, Math.floor((Date.now() - limite) / 86_400_000))
}

function textoLimite(h: HallazgoDetallado): string {
  if (!h.fecha_limite) return 'Sin fecha límite'
  const base = `Límite ${fechaCorta(h.fecha_limite)}`
  if (!h.atrasado || h.estado === 'cerrado') return base
  const dias = diasAtraso(h)
  return dias > 0 ? `${base} · ${dias} días de atraso` : `${base} · atrasado`
}

const alertasDetalle = computed(() => {
  const h = hallazgoSeleccionado.value
  if (!h || h.estado === 'cerrado') return []
  const alertas: { texto: string; clase: string }[] = []
  if ((h.dias_sin_actualizar ?? 0) > 0) {
    alertas.push({
      texto: `Sin actualizar ${h.dias_sin_actualizar} días`,
      clase: 'chip--aviso',
    })
  }
  if (h.reincidente) alertas.push({ texto: 'Reincidente', clase: 'chip--neutro' })
  return alertas
})

function etiquetaSeguimiento(tipo: string): string {
  return SEGUIMIENTO_LABEL[tipo] ?? tipo
}

function claseEvento(tipo: string): string {
  if (tipo === 'cierre_aprobado') return 'ok'
  if (tipo === 'cierre_rechazado') return 'peligro'
  if (tipo === 'solicitud_cierre') return 'cierre'
  if (tipo === 'accion_correctiva') return 'aviso'
  if (tipo === 'asignacion') return 'primario'
  return 'neutro'
}

async function abrirDetalles(h: HallazgoDetallado) {
  hallazgoSeleccionado.value = h
  drawerAbierto.value = true
  focoPrevio = document.activeElement as HTMLElement | null
  overflowPrevio = document.body.style.overflow
  document.body.style.overflow = 'hidden'
  historial.value = []
  historialError.value = ''
  historialCargando.value = true
  await nextTick()
  btnCerrarDetalles.value?.focus()
  await cargarHistorial(h.id)
}

async function cargarHistorial(hallazgoId: number) {
  historialCargando.value = true
  historialError.value = ''
  try {
    const datos = await listarHistorial(hallazgoId)
    if (hallazgoSeleccionado.value?.id === hallazgoId) {
      historial.value = datos
    }
  } catch {
    historialError.value = 'No se pudo cargar el historial.'
  } finally {
    historialCargando.value = false
  }
}

function reintentarHistorial() {
  if (hallazgoSeleccionado.value) cargarHistorial(hallazgoSeleccionado.value.id)
}

function cerrarDetalles() {
  drawerAbierto.value = false
  document.body.style.overflow = overflowPrevio
  focoPrevio?.focus()
}

function alPresionarTecla(evento: KeyboardEvent) {
  if (evento.key === 'Escape' && drawerAbierto.value) cerrarDetalles()
}
</script>

<template>
  <div class="page">
    <header class="page-header">
      <div class="page-header-info">
        <h1>Hallazgos de auditores</h1>
        <p class="subtitle">
          Prioriza atrasos y cierres pendientes de los hallazgos detectados por
          los auditores a tu cargo.
        </p>
      </div>
      <button class="btn btn-sm" type="button" :disabled="cargando" @click="cargar">
        <svg
          class="icon-refresh"
          :class="{ 'icon-refresh--gira': cargando }"
          viewBox="0 0 24 24"
          aria-hidden="true"
        >
          <path
            d="M20 11a8 8 0 1 0-2.3 6.2M20 5v6h-6"
            fill="none"
            stroke="currentColor"
            stroke-width="1.8"
            stroke-linecap="round"
            stroke-linejoin="round"
          />
        </svg>
        {{ cargando ? 'Actualizando…' : 'Actualizar' }}
      </button>
    </header>

    <div class="barra">
      <div class="vistas" role="group" aria-label="Filtrar hallazgos">
        <button
          v-for="v in vistas"
          :key="v.valor"
          type="button"
          class="vista"
          :class="{ 'vista--activa': vista === v.valor }"
          :aria-pressed="vista === v.valor"
          @click="vista = v.valor"
        >
          {{ v.etiqueta }}
          <span class="vista-conteo">{{ cargando ? '–' : conteos[v.valor] }}</span>
        </button>
      </div>

      <div class="search">
        <svg class="search-icon" viewBox="0 0 24 24" aria-hidden="true">
          <circle
            cx="11"
            cy="11"
            r="6.4"
            fill="none"
            stroke="currentColor"
            stroke-width="1.8"
          />
          <path
            d="M16 16l4 4"
            fill="none"
            stroke="currentColor"
            stroke-width="1.8"
            stroke-linecap="round"
          />
        </svg>
        <input
          v-model="busqueda"
          type="text"
          inputmode="search"
          placeholder="Buscar por descripción, área o responsable"
          aria-label="Buscar hallazgos"
        />
        <button
          v-if="busqueda"
          type="button"
          class="search-clear"
          aria-label="Limpiar búsqueda"
          @click="busqueda = ''"
        >
          <svg viewBox="0 0 16 16" aria-hidden="true">
            <path
              d="M4 4l8 8M12 4l-8 8"
              stroke="currentColor"
              stroke-width="1.6"
              stroke-linecap="round"
            />
          </svg>
        </button>
      </div>
    </div>

    <p v-if="error" class="msg msg-err">
      {{ error }}
      <button class="btn btn-sm" type="button" @click="cargar">Reintentar</button>
    </p>

    <div v-if="cargando" class="registro" aria-hidden="true">
      <div v-for="i in 4" :key="i" class="esqueleto">
        <div class="esqueleto-linea esqueleto-linea--corta"></div>
        <div class="esqueleto-linea"></div>
        <div class="esqueleto-linea esqueleto-linea--media"></div>
      </div>
    </div>

    <div v-else-if="!error && hallazgos.length === 0" class="state state-empty">
      <svg class="state-icon" viewBox="0 0 24 24" aria-hidden="true">
        <path d="M6 4v16M6 5h10l-1.8 3.5L16 12H6" />
      </svg>
      <h2>Sin hallazgos de auditores</h2>
      <p>
        Cuando los auditores a tu cargo registren hallazgos, aparecerán aquí
        ordenados por urgencia.
      </p>
    </div>

    <div v-else-if="!error && listaMostrada.length === 0" class="state state-empty">
      <svg class="state-icon" viewBox="0 0 24 24" aria-hidden="true">
        <circle
          cx="11"
          cy="11"
          r="6.4"
          fill="none"
          stroke="currentColor"
          stroke-width="1.6"
        />
        <path
          d="M16 16l4 4M8.5 11h5"
          fill="none"
          stroke="currentColor"
          stroke-width="1.6"
          stroke-linecap="round"
        />
      </svg>
      <h2>Sin resultados en esta vista</h2>
      <p>No hay hallazgos que coincidan con el filtro o la búsqueda actual.</p>
      <button
        class="btn btn-sm"
        type="button"
        @click="
          () => {
            vista = 'todos'
            busqueda = ''
          }
        "
      >
        Ver todos los hallazgos
      </button>
    </div>

    <ul v-else-if="!error" class="registro">
      <li v-for="h in listaMostrada" :key="h.id" class="reg">
        <div class="reg-principal">
          <div class="reg-cabecera">
            <span class="tipo" :class="tipoInfo(h.tipo).clase">
              {{ tipoInfo(h.tipo).etiqueta }}
            </span>
            <span class="reg-auditoria">{{ h.auditoria_nombre }}</span>
          </div>

          <p class="reg-descripcion">{{ h.descripcion }}</p>
        </div>

        <div class="reg-lateral">
          <span class="badge" :class="'badge-' + h.estado">
            {{ ESTADO_LABEL[h.estado] }}
          </span>

          <p
            class="reg-limite"
            :class="{ 'reg-limite--vencida': h.atrasado && h.estado !== 'cerrado' }"
          >
            <svg viewBox="0 0 24 24" aria-hidden="true">
              <circle
                cx="12"
                cy="12"
                r="8.2"
                fill="none"
                stroke="currentColor"
                stroke-width="1.6"
              />
              <path
                d="M12 8v4.4l2.6 2.6"
                fill="none"
                stroke="currentColor"
                stroke-width="1.6"
                stroke-linecap="round"
              />
            </svg>
            {{ textoLimite(h) }}
          </p>

          <button class="btn btn-sm reg-accion" type="button" @click="abrirDetalles(h)">
            <svg viewBox="0 0 24 24" aria-hidden="true">
              <path
                d="M2.6 12S6.2 5.7 12 5.7 21.4 12 21.4 12 17.8 18.3 12 18.3 2.6 12 2.6 12z"
                fill="none"
                stroke="currentColor"
                stroke-width="1.7"
                stroke-linejoin="round"
              />
              <circle
                cx="12"
                cy="12"
                r="2.8"
                fill="none"
                stroke="currentColor"
                stroke-width="1.7"
              />
            </svg>
            Ver detalles
          </button>
        </div>
      </li>
    </ul>

    <Teleport to="body">
      <Transition name="drawer">
        <div
          v-if="drawerAbierto"
          class="drawer-fondo"
          @click.self="cerrarDetalles"
        >
          <aside
            class="drawer"
            role="dialog"
            aria-modal="true"
            aria-labelledby="detalles-titulo"
          >
            <header class="drawer-cabecera">
              <div>
                <h2 id="detalles-titulo">Detalles del hallazgo</h2>
                <p class="drawer-sub">
                  {{ hallazgoSeleccionado?.auditoria_nombre }}
                </p>
              </div>
              <button
                ref="btnCerrarDetalles"
                type="button"
                class="drawer-cerrar"
                aria-label="Cerrar detalles"
                @click="cerrarDetalles"
              >
                <svg viewBox="0 0 16 16" aria-hidden="true">
                  <path
                    d="M4 4l8 8M12 4l-8 8"
                    stroke="currentColor"
                    stroke-width="1.6"
                    stroke-linecap="round"
                  />
                </svg>
              </button>
            </header>

            <div v-if="hallazgoSeleccionado" class="drawer-cuerpo">
              <section class="resumen">
                <div class="resumen-cabecera">
                  <span class="tipo" :class="tipoInfo(hallazgoSeleccionado.tipo).clase">
                    {{ tipoInfo(hallazgoSeleccionado.tipo).etiqueta }}
                  </span>
                  <span
                    class="badge"
                    :class="'badge-' + hallazgoSeleccionado.estado"
                  >
                    {{ ESTADO_LABEL[hallazgoSeleccionado.estado] }}
                  </span>
                </div>

                <p class="resumen-descripcion">
                  {{ hallazgoSeleccionado.descripcion }}
                </p>

                <dl class="resumen-datos">
                  <div>
                    <dt>Área responsable</dt>
                    <dd>{{ hallazgoSeleccionado.area_responsable_nombre || '—' }}</dd>
                  </div>
                  <div>
                    <dt>Responsable</dt>
                    <dd>{{ hallazgoSeleccionado.responsable_nombre || 'Sin asignar' }}</dd>
                  </div>
                  <div>
                    <dt>Célula</dt>
                    <dd>
                      {{
                        hallazgoSeleccionado.celula_numero
                          ? `Célula ${hallazgoSeleccionado.celula_numero}`
                          : '—'
                      }}
                    </dd>
                  </div>
                  <div>
                    <dt>Fecha límite</dt>
                    <dd
                      :class="{
                        'dato--vencido':
                          hallazgoSeleccionado.atrasado &&
                          hallazgoSeleccionado.estado !== 'cerrado',
                      }"
                    >
                      {{ fechaCorta(hallazgoSeleccionado.fecha_limite) }}
                    </dd>
                  </div>
                  <div>
                    <dt>Registrado</dt>
                    <dd>{{ fechaCorta(hallazgoSeleccionado.fecha_creacion) }}</dd>
                  </div>
                </dl>

                <div v-if="alertasDetalle.length" class="resumen-alertas">
                  <span
                    v-for="alerta in alertasDetalle"
                    :key="alerta.texto"
                    class="chip"
                    :class="alerta.clase"
                  >
                    {{ alerta.texto }}
                  </span>
                </div>

                <div v-if="hallazgoSeleccionado.accion_correctiva" class="accion">
                  <h3>Acción correctiva</h3>
                  <p>{{ hallazgoSeleccionado.accion_correctiva }}</p>
                </div>
              </section>

              <section class="movimientos">
                <h3>Movimientos</h3>

                <div v-if="historialCargando" class="esqueleto-timeline" aria-hidden="true">
                  <div v-for="i in 3" :key="i" class="esqueleto-evento">
                    <span class="esqueleto-punto"></span>
                    <div class="esqueleto-linea esqueleto-linea--media"></div>
                    <div class="esqueleto-linea esqueleto-linea--corta"></div>
                  </div>
                </div>

                <p v-else-if="historialError" class="msg msg-err">
                  {{ historialError }}
                  <button class="btn btn-sm" type="button" @click="reintentarHistorial">
                    Reintentar
                  </button>
                </p>

                <p v-else-if="historial.length === 0" class="movimientos-vacio">
                  Todavía no hay movimientos registrados para este hallazgo.
                </p>

                <ol v-else class="timeline">
                  <li
                    v-for="ev in historial"
                    :key="ev.id"
                    class="evento"
                    :class="'evento--' + claseEvento(ev.tipo)"
                  >
                    <span class="evento-punto" aria-hidden="true"></span>
                    <div class="evento-cuerpo">
                      <div class="evento-cabecera">
                        <span class="evento-tipo">{{ etiquetaSeguimiento(ev.tipo) }}</span>
                        <time class="evento-fecha">{{ fechaHora(ev.fecha_creacion) }}</time>
                      </div>
                      <p class="evento-usuario">{{ ev.usuario_nombre }}</p>
                      <div
                        v-if="ev.estado_desde || ev.estado_hasta"
                        class="evento-transicion"
                      >
                        <span
                          v-if="ev.estado_desde"
                          class="badge badge-plano"
                          :class="'badge-' + ev.estado_desde"
                        >
                          {{ ESTADO_LABEL[ev.estado_desde as EstadoHallazgo] ?? ev.estado_desde }}
                        </span>
                        <span class="evento-flecha" aria-hidden="true">→</span>
                        <span
                          v-if="ev.estado_hasta"
                          class="badge badge-plano"
                          :class="'badge-' + ev.estado_hasta"
                        >
                          {{ ESTADO_LABEL[ev.estado_hasta as EstadoHallazgo] ?? ev.estado_hasta }}
                        </span>
                      </div>
                      <p v-if="ev.detalle" class="evento-detalle">{{ ev.detalle }}</p>
                    </div>
                  </li>
                </ol>
              </section>
            </div>

            <footer class="drawer-pie">
              <button class="btn-secondary" type="button" @click="cerrarDetalles">
                Cerrar
              </button>
            </footer>
          </aside>
        </div>
      </Transition>
    </Teleport>
  </div>
</template>

<style scoped>
.icon-refresh {
  width: 0.95rem;
  height: 0.95rem;
  flex-shrink: 0;
}

.icon-refresh--gira {
  animation: girar 0.9s linear infinite;
}

@keyframes girar {
  to {
    transform: rotate(360deg);
  }
}

.barra {
  display: flex;
  align-items: center;
  gap: 0.9rem;
  flex-wrap: wrap;
  padding: 0.6rem 0.75rem;
  margin-bottom: 1rem;
  background: var(--c-surface);
  border: 1px solid var(--c-line);
  border-radius: var(--r-lg);
  box-shadow: var(--sh-sm);
}

.vistas {
  display: flex;
  gap: 0.3rem;
  flex-wrap: wrap;
}

.vista {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  padding: 0.42rem 0.7rem;
  border: 1px solid transparent;
  border-radius: var(--r-sm);
  background: transparent;
  color: var(--c-ink-2);
  font-family: inherit;
  font-size: var(--text-sm);
  font-weight: 600;
  cursor: pointer;
  transition:
    background 0.15s var(--ease),
    color 0.15s var(--ease),
    border-color 0.15s var(--ease);
}

.vista:hover {
  background: var(--c-surface-3);
}

.vista:focus-visible {
  outline: none;
  border-color: var(--c-primary);
  box-shadow: 0 0 0 3px var(--c-primary-ring);
}

.vista--activa {
  background: var(--c-primary-soft);
  color: var(--c-primary-active);
}

.vista-conteo {
  min-width: 1.35rem;
  padding: 0.05rem 0.35rem;
  border-radius: var(--r-pill);
  background: var(--c-surface-3);
  color: var(--c-ink-2);
  font-size: 0.7rem;
  font-weight: 700;
  font-variant-numeric: tabular-nums;
  text-align: center;
}

.vista--activa .vista-conteo {
  background: var(--c-surface);
  color: var(--c-primary-active);
}

.barra .search {
  flex: 1 1 260px;
  max-width: none;
  min-width: 0;
}

.registro {
  list-style: none;
  margin: 0;
  padding: 0;
  background: var(--c-surface);
  border: 1px solid var(--c-line);
  border-radius: var(--r-lg);
  box-shadow: var(--sh-sm);
  overflow: hidden;
}

.reg {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 0.85rem 1.5rem;
  align-items: start;
  padding: 1rem 1.15rem;
  transition: background 0.15s var(--ease);
}

.reg + .reg {
  border-top: 1px solid var(--c-line);
}

.reg:hover {
  background: var(--c-surface-2);
}

.reg-cabecera {
  display: flex;
  align-items: center;
  gap: 0.55rem;
  flex-wrap: wrap;
}

.tipo {
  display: inline-flex;
  align-items: center;
  padding: 0.1rem 0.5rem;
  border-radius: var(--r-sm);
  font-size: 0.68rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

.tipo--mayor {
  background: var(--c-ink);
  color: #fff;
}

.tipo--no-cumple {
  background: var(--c-warn-soft);
  color: var(--c-warn-ink);
}

.tipo--menor {
  background: var(--c-surface-3);
  color: var(--c-ink-2);
}

.reg-auditoria {
  font-size: var(--text-xs);
  font-weight: 600;
  color: var(--c-ink-3);
}

.reg-descripcion {
  margin: 0.4rem 0 0;
  font-size: var(--text-md);
  font-weight: 600;
  line-height: 1.45;
  color: var(--c-ink);
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.reg-lateral {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 0.45rem;
  text-align: right;
}

.reg-limite {
  display: inline-flex;
  align-items: center;
  gap: 0.32rem;
  font-size: var(--text-xs);
  color: var(--c-ink-3);
  font-variant-numeric: tabular-nums;
}

.reg-limite svg {
  width: 0.85rem;
  height: 0.85rem;
  flex-shrink: 0;
  color: var(--c-ink-4);
}

.reg-limite--vencida {
  color: var(--c-danger);
  font-weight: 600;
}

.reg-limite--vencida svg {
  color: var(--c-danger);
}

.chip {
  display: inline-flex;
  align-items: center;
  padding: 0.1rem 0.45rem;
  border-radius: var(--r-pill);
  font-size: 0.68rem;
  font-weight: 600;
  white-space: nowrap;
}

.chip--aviso {
  background: var(--c-warn-soft);
  color: var(--c-warn-ink);
}

.chip--neutro {
  background: var(--c-surface-3);
  color: var(--c-ink-2);
}

.reg-accion {
  margin-top: 0.15rem;
  gap: 0.35rem;
}

.reg-accion svg {
  width: 0.9rem;
  height: 0.9rem;
  flex-shrink: 0;
  color: var(--c-ink-3);
}

.badge-abierto {
  background: var(--c-surface-3);
  color: var(--c-ink-2);
}

.badge-en_correccion {
  background: var(--c-warn-soft);
  color: var(--c-warn-ink);
}

.badge-cierre_solicitado {
  background: #ede9fe;
  color: #6d28d9;
}

.badge-cerrado {
  background: var(--c-ok-soft);
  color: var(--c-ok-ink);
}

.esqueleto {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  padding: 1rem 1.15rem;
}

.esqueleto + .esqueleto {
  border-top: 1px solid var(--c-line);
}

.esqueleto-linea {
  height: 0.7rem;
  border-radius: 6px;
  background: linear-gradient(
    90deg,
    var(--c-surface-3) 25%,
    var(--c-surface-2) 37%,
    var(--c-surface-3) 63%
  );
  background-size: 400% 100%;
  animation: brillo 1.5s ease infinite;
}

.esqueleto-linea--corta {
  width: 28%;
}

.esqueleto-linea--media {
  width: 62%;
}

@keyframes brillo {
  0% {
    background-position: 100% 50%;
  }
  100% {
    background-position: 0 50%;
  }
}

.drawer-fondo {
  position: fixed;
  inset: 0;
  z-index: 1200;
  display: flex;
  justify-content: flex-end;
  background: rgba(15, 23, 42, 0.45);
}

.drawer {
  display: flex;
  flex-direction: column;
  width: min(480px, 100vw);
  height: 100%;
  background: var(--c-surface);
  box-shadow: var(--sh-xl);
}

.drawer-cabecera {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 1rem;
  padding: 1.15rem 1.3rem;
  border-bottom: 1px solid var(--c-line);
}

.drawer-cabecera h2 {
  font-size: var(--text-lg);
  font-weight: 800;
}

.drawer-sub {
  margin-top: 0.2rem;
  font-size: var(--text-xs);
  color: var(--c-ink-3);
}

.drawer-cerrar {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 2rem;
  height: 2rem;
  border: 1px solid transparent;
  border-radius: var(--r-sm);
  background: transparent;
  color: var(--c-ink-3);
  cursor: pointer;
  flex-shrink: 0;
}

.drawer-cerrar svg {
  width: 0.9rem;
  height: 0.9rem;
}

.drawer-cerrar:hover {
  background: var(--c-surface-3);
  color: var(--c-ink);
}

.drawer-cerrar:focus-visible {
  outline: none;
  border-color: var(--c-primary);
  box-shadow: 0 0 0 3px var(--c-primary-ring);
}

.drawer-cuerpo {
  flex: 1;
  overflow-y: auto;
  padding: 1.15rem 1.3rem 1.5rem;
}

.resumen {
  padding-bottom: 1.15rem;
  border-bottom: 1px solid var(--c-line);
}

.resumen-cabecera {
  display: flex;
  align-items: center;
  gap: 0.45rem;
  flex-wrap: wrap;
}

.resumen-descripcion {
  margin-top: 0.6rem;
  font-size: var(--text-base);
  font-weight: 600;
  line-height: 1.5;
  color: var(--c-ink);
}

.resumen-datos {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0.7rem 1rem;
  margin: 0.95rem 0 0;
}

.resumen-alertas {
  display: flex;
  gap: 0.35rem;
  flex-wrap: wrap;
  margin-top: 0.85rem;
}

.resumen-datos dt {
  font-size: 0.68rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--c-ink-3);
}

.resumen-datos dd {
  margin: 0.12rem 0 0;
  font-size: var(--text-sm);
  font-weight: 500;
  color: var(--c-ink-2);
}

.dato--vencido {
  color: var(--c-danger) !important;
  font-weight: 700 !important;
}

.accion {
  margin-top: 1rem;
  padding: 0.7rem 0.85rem;
  border: 1px solid var(--c-line);
  border-radius: var(--r-md);
  background: var(--c-surface-2);
}

.accion h3 {
  font-size: 0.68rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--c-ink-3);
}

.accion p {
  margin-top: 0.3rem;
  font-size: var(--text-sm);
  color: var(--c-ink-2);
}

.movimientos {
  margin-top: 1.2rem;
}

.movimientos > h3 {
  font-size: 0.68rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--c-ink-3);
  margin-bottom: 0.8rem;
}

.movimientos-vacio {
  padding: 1.2rem 0.9rem;
  border: 1.5px dashed var(--c-line-2);
  border-radius: var(--r-md);
  text-align: center;
  font-size: var(--text-sm);
  color: var(--c-ink-3);
}

.timeline {
  position: relative;
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.evento {
  position: relative;
  display: grid;
  grid-template-columns: 14px minmax(0, 1fr);
  gap: 0.75rem;
}

.evento:not(:last-child)::before {
  content: '';
  position: absolute;
  left: 6px;
  top: 14px;
  bottom: -1rem;
  width: 2px;
  background: var(--c-line);
}

.evento-punto {
  width: 10px;
  height: 10px;
  margin-top: 0.3rem;
  border-radius: 50%;
  background: var(--c-ink-4);
  box-shadow: 0 0 0 3px var(--c-surface);
  z-index: 1;
}

.evento--ok .evento-punto {
  background: var(--c-ok);
}

.evento--peligro .evento-punto {
  background: var(--c-danger);
}

.evento--cierre .evento-punto {
  background: #7c3aed;
}

.evento--aviso .evento-punto {
  background: var(--c-warn);
}

.evento--primario .evento-punto {
  background: var(--c-primary);
}

.evento-cuerpo {
  padding-bottom: 0.15rem;
}

.evento-cabecera {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 0.6rem;
  flex-wrap: wrap;
}

.evento-tipo {
  font-size: var(--text-sm);
  font-weight: 700;
  color: var(--c-ink);
}

.evento-fecha {
  font-size: 0.68rem;
  color: var(--c-ink-3);
  font-variant-numeric: tabular-nums;
}

.evento-usuario {
  margin-top: 0.1rem;
  font-size: var(--text-xs);
  color: var(--c-ink-3);
}

.evento-transicion {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  margin-top: 0.4rem;
  flex-wrap: wrap;
}

.badge-plano {
  padding: 0.05rem 0.45rem;
  font-size: 0.62rem;
}

.evento-flecha {
  font-size: 0.7rem;
  color: var(--c-ink-3);
}

.evento-detalle {
  margin-top: 0.4rem;
  font-size: var(--text-sm);
  line-height: 1.5;
  color: var(--c-ink-2);
  overflow-wrap: anywhere;
}

.esqueleto-timeline {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.esqueleto-evento {
  display: grid;
  grid-template-columns: 14px minmax(0, 1fr);
  gap: 0.75rem 0.6rem;
  align-items: center;
}

.esqueleto-punto {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: var(--c-surface-3);
  grid-row: span 2;
}

.esqueleto-evento .esqueleto-linea {
  width: 100%;
}

.esqueleto-evento .esqueleto-linea--media {
  width: 55%;
}

.esqueleto-evento .esqueleto-linea--corta {
  width: 30%;
}

.drawer-pie {
  padding: 0.9rem 1.3rem;
  border-top: 1px solid var(--c-line);
  display: flex;
  justify-content: flex-end;
  background: var(--c-surface);
}

.drawer-enter-active,
.drawer-leave-active {
  transition: opacity 0.2s var(--ease);
}

.drawer-enter-active .drawer,
.drawer-leave-active .drawer {
  transition: transform 0.22s var(--ease);
}

.drawer-enter-from,
.drawer-leave-to {
  opacity: 0;
}

.drawer-enter-from .drawer,
.drawer-leave-to .drawer {
  transform: translateX(28px);
}

@media (max-width: 760px) {
  .reg {
    grid-template-columns: minmax(0, 1fr);
    gap: 0.7rem;
  }

  .reg-lateral {
    align-items: flex-start;
    text-align: left;
  }

  .reg-accion {
    width: 100%;
    justify-content: center;
  }

  .barra {
    align-items: stretch;
  }

  .barra .search {
    flex-basis: 100%;
  }

  .resumen-datos {
    grid-template-columns: 1fr;
  }
}

@media (prefers-reduced-motion: reduce) {
  .esqueleto-linea,
  .icon-refresh--gira {
    animation: none;
  }

  .drawer-enter-active,
  .drawer-leave-active,
  .drawer-enter-active .drawer,
  .drawer-leave-active .drawer {
    transition: none;
  }
}
</style>
