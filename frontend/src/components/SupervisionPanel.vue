<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import {
  iniciarPendiente,
  listarEjecuciones,
  listarPendientes,
} from '@/services/ejecucion.service'
import { listarHallazgos } from '@/services/hallazgo.service'
import type {
  EjecucionAuditoriaListItem,
  PendienteItem,
} from '@/types/ejecucion'
import type { HallazgoDetallado } from '@/types/hallazgo'

const router = useRouter()

const cargando = ref(true)
const actualizando = ref(false)
const error = ref('')
const parcial = ref(false)
const accionError = ref('')
const actualizadoEn = ref<Date | null>(null)
const iniciandoId = ref<number | null>(null)

const pendientes = ref<PendienteItem[]>([])
const ejecuciones = ref<EjecucionAuditoriaListItem[]>([])
const hallazgos = ref<HallazgoDetallado[]>([])

const misAuditorias = computed(() => pendientes.value.slice(0, 3))
const ejecucionesRecientes = computed(() => ejecuciones.value.slice(0, 4))
const hallazgosAbiertos = computed(() =>
  hallazgos.value.filter((h) => h.estado !== 'cerrado'),
)

const conteos = computed(() => {
  const abiertos = hallazgosAbiertos.value
  return {
    abiertos: abiertos.length,
    atrasados: abiertos.filter((h) => h.atrasado).length,
    porCerrar: abiertos.filter((h) => h.estado === 'cierre_solicitado').length,
    reincidentes: abiertos.filter((h) => h.reincidente).length,
  }
})

const prioritarios = computed(() => {
  const relevantes = hallazgosAbiertos.value.filter(
    (h) => h.atrasado || h.estado === 'cierre_solicitado' || h.reincidente,
  )
  return relevantes
    .slice()
    .sort((a, b) => urgenciaHallazgo(a) - urgenciaHallazgo(b))
    .slice(0, 2)
})

const horaActualizacion = computed(() =>
  actualizadoEn.value
    ? actualizadoEn.value.toLocaleTimeString('es-MX', {
        hour: '2-digit',
        minute: '2-digit',
      })
    : '',
)

onMounted(() => {
  cargar()
})

async function cargar(silencioso = false) {
  if (silencioso) actualizando.value = true
  else cargando.value = true
  error.value = ''
  parcial.value = false
  accionError.value = ''

  const [pendientesRes, ejecucionesRes, hallazgosRes] = await Promise.allSettled(
    [
      listarPendientes(),
      listarEjecuciones({
        solo_auditores: true,
        tipo_respuesta: 'semaforo',
        limit: 20,
      }),
      listarHallazgos({ solo_auditores: true }),
    ],
  )

  let fallos = 0

  if (pendientesRes.status === 'fulfilled') {
    pendientes.value = pendientesRes.value
  } else {
    pendientes.value = []
    fallos += 1
  }

  if (ejecucionesRes.status === 'fulfilled') {
    ejecuciones.value = ejecucionesRes.value
  } else {
    ejecuciones.value = []
    fallos += 1
  }

  if (hallazgosRes.status === 'fulfilled') {
    hallazgos.value = hallazgosRes.value
  } else {
    hallazgos.value = []
    fallos += 1
  }

  if (fallos === 3) {
    error.value = 'No se pudo cargar el panel de supervisión.'
  } else if (fallos > 0) {
    parcial.value = true
  }

  if (fallos < 3) {
    actualizadoEn.value = new Date()
  }

  cargando.value = false
  actualizando.value = false
}

function areaCelula(item: {
  area_nombre: string | null
  celula_numero: number | null
}): string {
  return [
    item.area_nombre,
    item.celula_numero ? `Célula ${item.celula_numero}` : null,
  ]
    .filter(Boolean)
    .join(' · ')
}

function estadoPendiente(p: PendienteItem): string {
  const estados: Record<string, string> = {
    atrasada: 'Atrasada',
    en_progreso: 'En progreso',
    disponible: 'Disponible',
    bloqueada: 'Bloqueada',
  }
  return estados[p.estado] || p.estado
}

function estadoEjecucion(e: EjecucionAuditoriaListItem): {
  label: string
  cls: string
} {
  if (e.vencida) return { label: 'Vencida', cls: 'badge-vencida' }
  if (e.estado === 'no_elaborada') {
    return { label: 'No elaborada', cls: 'badge-no-elaborada' }
  }
  if (e.estado === 'pendiente') {
    return { label: 'Pendiente', cls: 'badge-pendiente' }
  }
  if (e.estado === 'finalizada') {
    return { label: 'Finalizada', cls: 'badge-finalizada' }
  }
  return { label: 'En progreso', cls: 'badge-progreso' }
}

function urgenciaHallazgo(h: HallazgoDetallado): number {
  if (h.atrasado) return 0
  if (h.estado === 'cierre_solicitado') return 1
  if (h.reincidente) return 2
  return 3
}

function etiquetaPrioridad(h: HallazgoDetallado): {
  label: string
  cls: string
} {
  if (h.atrasado) return { label: 'Atrasado', cls: 'priority-tag--late' }
  if (h.estado === 'cierre_solicitado') {
    return { label: 'Por cerrar', cls: 'priority-tag--close' }
  }
  return { label: 'Reincidente', cls: 'priority-tag--repeat' }
}

function metaHallazgo(h: HallazgoDetallado): string {
  return [h.area_responsable_nombre, h.auditoria_nombre]
    .filter(Boolean)
    .join(' · ')
}

async function accionar(p: PendienteItem) {
  if (!p.ejecucion_id || !p.accion) return

  if (p.accion === 'continuar') {
    router.push({ name: 'ejecutar', query: { id: String(p.ejecucion_id) } })
    return
  }

  iniciandoId.value = p.ejecucion_id
  try {
    const ejecucion = await iniciarPendiente(p.ejecucion_id)
    router.push({ name: 'ejecutar', query: { id: String(ejecucion.id) } })
  } catch (err) {
    const mensaje =
      (err as { response?: { data?: { detail?: string } } })?.response?.data
        ?.detail || 'No se pudo iniciar la auditoría.'
    await cargar(true)
    accionError.value = mensaje
  } finally {
    iniciandoId.value = null
  }
}
</script>

<template>
  <section class="supervision" aria-labelledby="supervision-title">
    <header class="supervision-head">
      <div class="supervision-heading">
        <h2 id="supervision-title">Tu supervisión</h2>
        <p>Auditorías propias, ejecuciones por revisar y señales de tus áreas.</p>
      </div>

      <div class="supervision-meta">
        <span class="supervision-stamp">
          <span
            class="stamp-dot"
            :class="{ 'stamp-dot--busy': cargando || actualizando }"
            aria-hidden="true"
          ></span>
          <template v-if="cargando">Cargando…</template>
          <template v-else-if="actualizadoEn">
            Actualizado {{ horaActualizacion }}
          </template>
        </span>
        <button
          class="icon-btn supervision-refresh"
          type="button"
          aria-label="Actualizar panel de supervisión"
          :disabled="cargando || actualizando"
          @click="cargar(true)"
        >
          <svg
            viewBox="0 0 24 24"
            aria-hidden="true"
            :class="{ 'refresh-spin': actualizando }"
          >
            <path
              d="M20 11a8 8 0 1 0-2.3 6.4"
              fill="none"
              stroke="currentColor"
              stroke-width="1.7"
              stroke-linecap="round"
            />
            <path
              d="M20 5.5V11h-5.5"
              fill="none"
              stroke="currentColor"
              stroke-width="1.7"
              stroke-linecap="round"
              stroke-linejoin="round"
            />
          </svg>
        </button>
      </div>
    </header>

    <p v-if="error" class="msg msg-err panel-alert" role="alert">{{ error }}</p>
    <p v-else-if="parcial" class="panel-note">
      Algunas señales no se pudieron actualizar.
    </p>
    <p v-if="accionError" class="msg msg-err panel-alert" role="alert">
      {{ accionError }}
    </p>

    <div v-if="cargando" class="supervision-loading" aria-live="polite">
      <span class="spinner" aria-hidden="true"></span>
      <span>Cargando tu supervisión…</span>
    </div>

    <template v-else>
      <div class="supervision-top">
        <section class="supervision-block" aria-labelledby="mis-auditorias-title">
          <header class="block-head">
            <div>
              <h3 id="mis-auditorias-title">Mis auditorías</h3>
              <p class="block-sub">Pendientes de tu capa</p>
            </div>
            <RouterLink to="/mis-pendientes" class="block-link">
              Ver todas
              <svg viewBox="0 0 16 16" aria-hidden="true">
                <path
                  d="M3 8h10M9 4l4 4-4 4"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="1.5"
                  stroke-linecap="round"
                  stroke-linejoin="round"
                />
              </svg>
            </RouterLink>
          </header>

          <p v-if="!pendientes.length" class="block-empty">
            No tienes auditorías pendientes.
          </p>

          <ul v-else class="rows">
            <li
              v-for="p in misAuditorias"
              :key="p.auditoria_id + '-' + (p.ejecucion_id ?? 'x')"
              class="audit-row"
            >
              <div class="row-main">
                <p class="row-title">{{ p.auditoria_nombre }}</p>
                <p v-if="areaCelula(p)" class="row-meta">
                  {{ areaCelula(p) }}
                </p>
                <p class="row-status" :class="'row-status--' + p.estado">
                  <span class="status-dot" aria-hidden="true"></span>
                  {{ p.contador || estadoPendiente(p) }}
                </p>
              </div>

              <button
                v-if="p.accion"
                class="audit-action"
                type="button"
                :disabled="iniciandoId === p.ejecucion_id"
                :aria-label="
                  (p.accion === 'continuar' ? 'Continuar ' : 'Iniciar ') +
                  p.auditoria_nombre
                "
                @click="accionar(p)"
              >
                {{
                  iniciandoId === p.ejecucion_id
                    ? 'Iniciando…'
                    : p.accion === 'continuar'
                      ? 'Continuar'
                      : 'Iniciar'
                }}
                <svg viewBox="0 0 16 16" aria-hidden="true">
                  <path
                    d="M3 8h10M9 4l4 4-4 4"
                    fill="none"
                    stroke="currentColor"
                    stroke-width="1.5"
                    stroke-linecap="round"
                    stroke-linejoin="round"
                  />
                </svg>
              </button>
            </li>
          </ul>
        </section>

        <section
          class="supervision-block"
          aria-labelledby="revisiones-title"
        >
          <header class="block-head">
            <div>
              <h3 id="revisiones-title">Ejecuciones de auditores</h3>
              <p class="block-sub">Últimas en tus áreas</p>
            </div>
            <RouterLink to="/revision-auditorias" class="block-link">
              Abrir revisión
              <svg viewBox="0 0 16 16" aria-hidden="true">
                <path
                  d="M3 8h10M9 4l4 4-4 4"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="1.5"
                  stroke-linecap="round"
                  stroke-linejoin="round"
                />
              </svg>
            </RouterLink>
          </header>

          <p v-if="!ejecuciones.length" class="block-empty">
            Sin ejecuciones de auditores en tus áreas.
          </p>

          <ul v-else class="rows">
            <li v-for="e in ejecucionesRecientes" :key="e.id">
              <RouterLink
                :to="{ name: 'revision-auditorias', query: { ejecucion: e.id } }"
                class="exec-row"
              >
                <div class="row-main">
                  <p class="row-title">{{ e.auditoria_nombre }}</p>
                  <p class="row-meta">
                    {{ e.usuario_nombre }}
                    <template v-if="areaCelula(e)"> · {{ areaCelula(e) }}</template>
                  </p>
                  <div
                    class="semaforo"
                    role="img"
                    :aria-label="`${e.resumen.total_v} verde, ${e.resumen.total_a} amarillo, ${e.resumen.total_r} rojo`"
                  >
                    <span
                      class="sem sem--v"
                      :class="{ 'sem--zero': !e.resumen.total_v }"
                    >
                      <i aria-hidden="true"></i>{{ e.resumen.total_v }}
                    </span>
                    <span
                      class="sem sem--a"
                      :class="{ 'sem--zero': !e.resumen.total_a }"
                    >
                      <i aria-hidden="true"></i>{{ e.resumen.total_a }}
                    </span>
                    <span
                      class="sem sem--r"
                      :class="{ 'sem--zero': !e.resumen.total_r }"
                    >
                      <i aria-hidden="true"></i>{{ e.resumen.total_r }}
                    </span>
                  </div>
                </div>
                <span class="badge" :class="estadoEjecucion(e).cls">
                  {{ estadoEjecucion(e).label }}
                </span>
              </RouterLink>
            </li>
          </ul>
        </section>
      </div>

      <div class="supervision-signals">
        <section class="signals-block" aria-labelledby="senales-title">
          <header class="block-head">
            <div>
              <h3 id="senales-title">Señales de calidad</h3>
              <p class="block-sub">Hallazgos de auditorías de piso</p>
            </div>
            <RouterLink to="/hallazgos-auditores" class="block-link">
              Ver hallazgos
              <svg viewBox="0 0 16 16" aria-hidden="true">
                <path
                  d="M3 8h10M9 4l4 4-4 4"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="1.5"
                  stroke-linecap="round"
                  stroke-linejoin="round"
                />
              </svg>
            </RouterLink>
          </header>

          <div class="signal-grid">
            <RouterLink
              :to="{ name: 'hallazgos-auditores', query: { vista: 'abiertos' } }"
              class="signal"
              :class="{ 'signal--zero': !conteos.abiertos }"
            >
              <span class="signal-dot signal-dot--open" aria-hidden="true"></span>
              <span class="signal-label">Abiertos</span>
              <span class="signal-count">{{ conteos.abiertos }}</span>
            </RouterLink>

            <RouterLink
              :to="{ name: 'hallazgos-auditores', query: { vista: 'atrasados' } }"
              class="signal"
              :class="{ 'signal--zero': !conteos.atrasados }"
            >
              <span class="signal-dot signal-dot--late" aria-hidden="true"></span>
              <span class="signal-label">Atrasados</span>
              <span class="signal-count">{{ conteos.atrasados }}</span>
            </RouterLink>

            <RouterLink
              :to="{
                name: 'hallazgos-auditores',
                query: { vista: 'cierre_pendiente' },
              }"
              class="signal"
              :class="{ 'signal--zero': !conteos.porCerrar }"
            >
              <span class="signal-dot signal-dot--close" aria-hidden="true"></span>
              <span class="signal-label">Por cerrar</span>
              <span class="signal-count">{{ conteos.porCerrar }}</span>
            </RouterLink>

            <RouterLink
              :to="{
                name: 'hallazgos-auditores',
                query: { vista: 'reincidencia' },
              }"
              class="signal"
              :class="{ 'signal--zero': !conteos.reincidentes }"
            >
              <span class="signal-dot signal-dot--repeat" aria-hidden="true"></span>
              <span class="signal-label">Reincidentes</span>
              <span class="signal-count">{{ conteos.reincidentes }}</span>
            </RouterLink>
          </div>
        </section>

        <section class="attention-block" aria-labelledby="atencion-title">
          <header class="block-head">
            <div>
              <h3 id="atencion-title">Atención prioritaria</h3>
              <p class="block-sub">Lo que no debería esperar</p>
            </div>
          </header>

          <p v-if="!prioritarios.length" class="block-empty block-empty--ok">
            Sin hallazgos que requieran atención.
          </p>

          <ul v-else class="attention-list">
            <li v-for="h in prioritarios" :key="h.id">
              <RouterLink
                :to="{
                  name: 'hallazgos-auditores',
                  query: { hallazgo: h.id },
                }"
                class="priority-link"
              >
                <span
                  class="priority-tag"
                  :class="etiquetaPrioridad(h).cls"
                >{{ etiquetaPrioridad(h).label }}</span>
                <p class="priority-desc">{{ h.descripcion }}</p>
                <p class="priority-meta">{{ metaHallazgo(h) }}</p>
              </RouterLink>
            </li>
          </ul>
        </section>
      </div>
    </template>
  </section>
</template>

<style scoped>
.supervision {
  container-type: inline-size;
  background: var(--c-surface);
  border: 1px solid var(--c-line);
  border-radius: 16px;
  overflow: hidden;
}

.supervision-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 0.85rem 1rem;
  padding: 1.4rem 1.5rem 1.15rem;
}

.supervision-heading h2 {
  font-family: var(--font-display);
  font-size: 1.18rem;
  font-weight: 600;
  letter-spacing: -0.022em;
  color: var(--c-ink);
}

.supervision-heading p {
  margin-top: 0.25rem;
  color: var(--c-ink-3);
  font-size: 0.82rem;
}

.supervision-meta {
  display: flex;
  align-items: center;
  gap: 0.55rem;
  flex-shrink: 0;
}

.supervision-stamp {
  display: inline-flex;
  align-items: center;
  gap: 0.38rem;
  color: var(--c-ink-3);
  font-family: var(--font-code);
  font-size: 0.62rem;
  letter-spacing: 0.015em;
  white-space: nowrap;
}

.stamp-dot {
  width: 0.4rem;
  height: 0.4rem;
  flex-shrink: 0;
  border-radius: 50%;
  background: var(--c-ok);
  box-shadow: 0 0 0 3px var(--c-ok-soft);
}

.stamp-dot--busy {
  background: var(--c-warn);
  box-shadow: 0 0 0 3px var(--c-warn-soft);
}

.supervision-refresh {
  width: 1.85rem;
  height: 1.85rem;
}

.refresh-spin {
  animation: refresh-spin 0.8s linear infinite;
}

.panel-alert,
.panel-note {
  margin: 0 1.5rem 1rem;
}

.panel-note {
  padding: 0.55rem 0.75rem;
  border: 1px solid var(--c-warn-soft);
  border-radius: var(--r-md);
  background: var(--c-warn-soft);
  color: var(--c-warn-ink);
  font-size: 0.75rem;
}

.supervision-loading {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.65rem;
  min-height: 18rem;
  border-top: 1px solid var(--c-line);
  color: var(--c-ink-3);
  font-size: 0.8rem;
}

.supervision-loading .spinner {
  width: 1.35rem;
  height: 1.35rem;
  border-width: 2px;
}

.supervision-top {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);
  border-top: 1px solid var(--c-line);
}

.supervision-block {
  min-width: 0;
  padding: 1.15rem 1.5rem 1.35rem;
}

.supervision-block + .supervision-block {
  border-left: 1px solid var(--c-line);
}

.block-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 0.75rem;
  margin-bottom: 0.8rem;
}

.block-head h3 {
  font-family: var(--font-display);
  font-size: 0.96rem;
  font-weight: 600;
  letter-spacing: -0.012em;
  color: var(--c-ink);
}

.block-sub {
  margin-top: 0.14rem;
  color: var(--c-ink-3);
  font-size: 0.71rem;
  line-height: 1.35;
}

.block-link {
  display: inline-flex;
  align-items: center;
  gap: 0.22rem;
  flex-shrink: 0;
  color: var(--c-primary);
  font-size: 0.71rem;
  font-weight: 600;
  text-decoration: none;
  white-space: nowrap;
}

.block-link:hover {
  color: var(--c-primary-hover);
  text-decoration: underline;
  text-underline-offset: 3px;
}

.block-link svg {
  width: 0.78rem;
  height: 0.78rem;
}

.rows {
  display: flex;
  flex-direction: column;
  margin: 0;
  padding: 0;
  list-style: none;
}

.audit-row {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 0.8rem;
  padding: 0.7rem 0;
  border-top: 1px solid var(--c-line);
}

.audit-row:first-child {
  padding-top: 0;
  border-top: 0;
}

.audit-row:last-child {
  padding-bottom: 0;
}

.row-main {
  min-width: 0;
  flex: 1;
}

.row-title {
  color: var(--c-ink);
  font-size: 0.81rem;
  font-weight: 600;
  line-height: 1.35;
  overflow-wrap: anywhere;
}

.row-meta {
  margin-top: 0.12rem;
  color: var(--c-ink-3);
  font-size: 0.7rem;
  line-height: 1.35;
}

.row-status {
  display: flex;
  align-items: center;
  gap: 0.3rem;
  margin-top: 0.25rem;
  color: var(--c-ink-3);
  font-size: 0.67rem;
  font-weight: 500;
  line-height: 1.35;
}

.status-dot {
  width: 0.34rem;
  height: 0.34rem;
  flex-shrink: 0;
  border-radius: 50%;
  background: var(--c-ink-4);
}

.row-status--atrasada {
  color: var(--c-danger-ink);
}

.row-status--atrasada .status-dot {
  background: var(--c-danger);
}

.row-status--en_progreso {
  color: var(--c-warn-ink);
}

.row-status--en_progreso .status-dot {
  background: var(--c-warn);
}

.row-status--disponible {
  color: var(--c-ok-ink);
}

.row-status--disponible .status-dot {
  background: var(--c-ok);
}

.audit-action {
  display: inline-flex;
  align-items: center;
  gap: 0.28rem;
  flex-shrink: 0;
  align-self: center;
  padding: 0.34rem 0.55rem;
  border: 1px solid var(--c-line-2);
  border-radius: 8px;
  background: var(--c-surface);
  color: var(--c-ink-2);
  font-size: 0.7rem;
  font-weight: 600;
  cursor: pointer;
  transition:
    background 0.15s var(--ease),
    border-color 0.15s var(--ease),
    color 0.15s var(--ease);
}

.audit-action:hover {
  background: var(--c-primary-soft);
  border-color: var(--c-primary);
  color: var(--c-primary-active);
}

.audit-action:disabled {
  opacity: 0.55;
  cursor: wait;
}

.audit-action svg {
  width: 0.72rem;
  height: 0.72rem;
}

.exec-row {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 0.65rem;
  padding: 0.7rem 0;
  border-top: 1px solid var(--c-line);
  color: inherit;
  text-decoration: none;
}

.rows > li:first-child .exec-row {
  padding-top: 0;
  border-top: 0;
}

.rows > li:last-child .exec-row {
  padding-bottom: 0;
}

.exec-row:hover .row-title {
  color: var(--c-primary);
}

.exec-row .badge {
  flex-shrink: 0;
  align-self: center;
  font-size: 0.62rem;
}

.semaforo {
  display: flex;
  align-items: center;
  gap: 0.55rem;
  margin-top: 0.4rem;
}

.sem {
  display: inline-flex;
  align-items: center;
  gap: 0.22rem;
  color: var(--c-ink-2);
  font-size: 0.68rem;
  font-weight: 600;
  font-variant-numeric: tabular-nums;
}

.sem i {
  width: 0.34rem;
  height: 0.34rem;
  border-radius: 50%;
  background: var(--sem-color);
}

.sem--v {
  --sem-color: var(--c-ok);
}

.sem--a {
  --sem-color: var(--c-warn);
}

.sem--r {
  --sem-color: var(--c-danger);
}

.sem--zero {
  color: var(--c-ink-4);
}

.sem--zero i {
  opacity: 0.4;
}

.block-empty {
  padding: 1.5rem 0 0.35rem;
  color: var(--c-ink-3);
  font-size: 0.78rem;
}

.block-empty--ok {
  color: var(--c-ok-ink);
}

.supervision-signals {
  display: grid;
  grid-template-columns: minmax(0, 1.1fr) minmax(0, 0.9fr);
  border-top: 1px solid var(--c-line);
}

.signals-block,
.attention-block {
  min-width: 0;
  padding: 1.15rem 1.5rem 1.35rem;
}

.attention-block {
  border-left: 1px solid var(--c-line);
}

.signal-grid {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);
  column-gap: 1.4rem;
}

.signal {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.58rem 0;
  border-top: 1px solid var(--c-line);
  color: var(--c-ink-2);
  text-decoration: none;
  transition: color 0.15s var(--ease);
}

.signal:nth-child(-n + 2) {
  border-top: 0;
}

.signal:nth-child(even) {
  padding-left: 1.4rem;
  border-left: 1px solid var(--c-line);
}

.signal:hover {
  color: var(--c-primary);
}

.signal-dot {
  width: 0.42rem;
  height: 0.42rem;
  flex-shrink: 0;
  border-radius: 50%;
  background: var(--signal-color);
}

.signal-dot--open {
  --signal-color: var(--c-primary);
}

.signal-dot--late {
  --signal-color: var(--c-danger);
}

.signal-dot--close {
  --signal-color: var(--c-warn);
}

.signal-dot--repeat {
  --signal-color: var(--c-primary-active);
}

.signal-label {
  flex: 1;
  font-size: 0.72rem;
  font-weight: 500;
}

.signal-count {
  color: var(--c-ink);
  font-family: var(--font-code);
  font-size: 0.8rem;
  font-weight: 500;
  font-variant-numeric: tabular-nums;
}

.signal--zero {
  opacity: 0.52;
}

.attention-list {
  display: flex;
  flex-direction: column;
  margin: 0;
  padding: 0;
  list-style: none;
}

.attention-list li + li {
  border-top: 1px solid var(--c-line);
}

.priority-link {
  display: block;
  padding: 0.62rem 0;
  color: inherit;
  text-decoration: none;
}

.attention-list li:first-child .priority-link {
  padding-top: 0;
}

.attention-list li:last-child .priority-link {
  padding-bottom: 0;
}

.priority-link:hover .priority-desc {
  color: var(--c-primary);
}

.priority-tag {
  display: inline-flex;
  align-items: center;
  margin-bottom: 0.28rem;
  padding: 0.1rem 0.42rem;
  border-radius: 999px;
  font-size: 0.61rem;
  font-weight: 700;
  letter-spacing: 0.05em;
  line-height: 1.4;
  text-transform: uppercase;
}

.priority-tag--late {
  background: var(--c-danger-soft);
  color: var(--c-danger-ink);
}

.priority-tag--close {
  background: var(--c-warn-soft);
  color: var(--c-warn-ink);
}

.priority-tag--repeat {
  background: var(--c-primary-soft);
  color: var(--c-primary-active);
}

.priority-desc {
  display: -webkit-box;
  overflow: hidden;
  color: var(--c-ink-2);
  font-size: 0.77rem;
  line-height: 1.4;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
}

.priority-meta {
  margin-top: 0.18rem;
  overflow: hidden;
  color: var(--c-ink-3);
  font-size: 0.66rem;
  white-space: nowrap;
  text-overflow: ellipsis;
}

@keyframes refresh-spin {
  to {
    transform: rotate(360deg);
  }
}

@container (max-width: 860px) {
  .supervision-top {
    grid-template-columns: minmax(0, 1fr);
  }

  .supervision-block + .supervision-block {
    border-top: 1px solid var(--c-line);
    border-left: 0;
  }
}

@container (max-width: 680px) {
  .supervision-signals {
    grid-template-columns: minmax(0, 1fr);
  }

  .attention-block {
    border-top: 1px solid var(--c-line);
    border-left: 0;
  }
}

@container (max-width: 520px) {
  .supervision-head {
    padding: 1.2rem 1.25rem 1rem;
  }

  .supervision-block,
  .signals-block,
  .attention-block {
    padding: 1rem 1.25rem 1.15rem;
  }

  .panel-alert,
  .panel-note {
    margin-right: 1.25rem;
    margin-left: 1.25rem;
  }

  .supervision-heading h2 {
    font-size: 1.08rem;
  }

  .supervision-heading p {
    font-size: 0.78rem;
  }

  .audit-row {
    gap: 0.6rem;
  }

  .audit-action {
    padding: 0.32rem 0.45rem;
    font-size: 0.66rem;
  }

  .signal {
    column-gap: 0.4rem;
  }

  .signal:nth-child(even) {
    padding-left: 1rem;
  }

  .signal-label {
    font-size: 0.7rem;
  }

  .exec-row .badge {
    font-size: 0.58rem;
  }
}

@media (prefers-reduced-motion: reduce) {
  .refresh-spin {
    animation: none;
  }
}
</style>
