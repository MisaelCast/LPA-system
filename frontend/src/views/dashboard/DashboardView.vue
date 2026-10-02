<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import type { Auditoria } from '@/types/auditoria'
import type { EjecucionAuditoriaListItem } from '@/types/ejecucion'
import {
  listarEjecuciones,
  obtenerAuditoriasDisponibles,
} from '@/services/ejecucion.service'

const router = useRouter()
const authStore = useAuthStore()

const cargando = ref(true)
const error = ref('')
const auditorias = ref<Auditoria[]>([])
const ejecuciones = ref<EjecucionAuditoriaListItem[]>([])

const puedeRevisar = computed(
  () => authStore.isAdmin || authStore.isSupervisor || authStore.isGerente,
)

const kpis = computed(() => {
  const enProgreso = ejecuciones.value.filter((e) => e.estado === 'en_proceso').length
  const finalizadas = ejecuciones.value.filter((e) => e.estado === 'finalizada').length
  return [
    {
      label: 'Auditorías activas',
      valor: auditorias.value.filter((a) => a.activa).length,
      detalle: `${auditorias.value.length} en total`,
      activo: false,
    },
    {
      label: 'En progreso',
      valor: enProgreso,
      detalle: 'ejecuciones abiertas',
      activo: false,
    },
    {
      label: 'Finalizadas',
      valor: finalizadas,
      detalle: 'ejecuciones completadas',
      activo: true,
    },
  ]
})

const recientes = computed(() =>
  [...ejecuciones.value]
    .sort((a, b) => b.fecha.localeCompare(a.fecha))
    .slice(0, 6),
)

const acciones = computed(() => {
  const items = [
    {
      to: '/ejecutar',
      titulo: 'Ejecutar auditoría',
      desc: 'Inicia una nueva auditoría en una célula.',
      icon: 'play',
    },
    {
      to: '/auditorias-realizadas',
      titulo: 'Auditorías realizadas',
      desc: 'Historial y continuar ejecuciones en curso.',
      icon: 'history',
    },
  ]
  if (authStore.isAdmin) {
    items.push({
      to: '/auditorias',
      titulo: 'Gestionar auditorías',
      desc: 'Plantillas, criterios, áreas y capas.',
      icon: 'clipboard',
    })
  }
  return items
})

onMounted(async () => {
  try {
    const [auds, ejecs] = await Promise.all([
      obtenerAuditoriasDisponibles().catch(() => [] as Auditoria[]),
      listarEjecuciones(puedeRevisar.value ? {} : { solo_propias: true }).catch(
        () => [] as EjecucionAuditoriaListItem[],
      ),
    ])
    auditorias.value = auds
    ejecuciones.value = ejecs
  } catch (err) {
    error.value =
      (err as { response?: { data?: { detail?: string } } })?.response?.data
        ?.detail || 'No se pudieron cargar los datos del panel.'
  } finally {
    cargando.value = false
  }
})

function formatearFecha(iso: string): string {
  const d = new Date(iso)
  if (Number.isNaN(d.getTime())) return iso
  const dia = String(d.getDate()).padStart(2, '0')
  const mes = String(d.getMonth() + 1).padStart(2, '0')
  const anio = d.getFullYear()
  return `${dia}/${mes}/${anio}`
}

function estadoLabel(estado: string): string {
  return estado === 'finalizada' ? 'Finalizada' : 'En progreso'
}

function esFinalizada(estado: string): boolean {
  return estado === 'finalizada'
}

function abrirEjecucion(e: EjecucionAuditoriaListItem) {
  router.push({ name: 'ejecutar', query: { id: String(e.id) } })
}
</script>

<template>
  <div class="dashboard">
    <header class="page-header">
      <div class="page-header-info">
        <h1>Dashboard</h1>
        <p class="subtitle">
          Resumen de auditorías y acceso rápido a las tareas del día.
        </p>
      </div>
    </header>

    <p v-if="error" class="msg msg-err">{{ error }}</p>

    <!-- Cargando -->
    <div v-if="cargando" class="state state-loading">
      <div class="spinner"></div>
      <p>Cargando panel…</p>
    </div>

    <template v-else>
      <!-- KPIs -->
      <div class="stats">
        <div v-for="k in kpis" :key="k.label" class="stat">
          <span class="stat-label">{{ k.label }}</span>
          <span class="stat-value" :class="{ 'stat-active': k.activo }" data-num>
            {{ k.valor }}
          </span>
          <span class="stat-detalle">{{ k.detalle }}</span>
        </div>
      </div>

      <!-- Acciones rápidas -->
      <section class="panel">
        <div class="panel-head">
          <h2>Acciones rápidas</h2>
        </div>
        <div class="quick-actions">
          <button
            v-for="acc in acciones"
            :key="acc.to"
            class="quick-action"
            @click="router.push(acc.to)"
          >
            <span class="quick-icon">
              <svg viewBox="0 0 24 24" aria-hidden="true">
                <template v-if="acc.icon === 'play'">
                  <rect x="4" y="4" width="16" height="16" rx="2.2" />
                  <path d="M10.4 8.8l4.6 3.2-4.6 3.2V8.8z" fill="currentColor" stroke="none" />
                </template>
                <template v-else-if="acc.icon === 'history'">
                  <circle cx="12" cy="12" r="8.6" />
                  <path d="M12 7.2V12l3.2 2" />
                </template>
                <template v-else-if="acc.icon === 'clipboard'">
                  <path d="M8 4h1.2a1.6 1.6 0 0 1 3.2 0h1.2" />
                  <rect x="5" y="4" width="14" height="16.5" rx="1.8" />
                  <path d="M9 10h6M9 13.5h6M9 17h4" />
                </template>
              </svg>
            </span>
            <span class="quick-text">
              <strong>{{ acc.titulo }}</strong>
              <small>{{ acc.desc }}</small>
            </span>
            <svg class="quick-arrow" viewBox="0 0 24 24" aria-hidden="true">
              <path d="M9 6l6 6-6 6" />
            </svg>
          </button>
        </div>
      </section>

      <!-- Recientes -->
      <section class="panel">
        <div class="panel-head">
          <h2>Ejecuciones recientes</h2>
          <RouterLink class="panel-link" to="/auditorias-realizadas">
            Ver todas
          </RouterLink>
        </div>

        <div v-if="recientes.length === 0" class="state state-empty">
          <svg class="state-icon" viewBox="0 0 24 24" aria-hidden="true">
            <circle cx="12" cy="12" r="8.6" />
            <path d="M12 7.2V12l3.2 2" />
          </svg>
          <h2>Aún no hay ejecuciones</h2>
          <p>Inicia tu primera auditoría para ver el historial aquí.</p>
          <button class="btn-primary" @click="router.push('/ejecutar')">
            Ejecutar auditoría
          </button>
        </div>

        <div v-else class="table-wrap">
          <table class="table">
            <thead>
              <tr>
                <th>Fecha</th>
                <th>Auditoría</th>
                <th>Área · Célula</th>
                <th>Resultado</th>
                <th>Estado</th>
                <th class="col-acciones">Acciones</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="e in recientes" :key="e.id">
                <td class="dash-fecha">{{ formatearFecha(e.fecha) }}</td>
                <td class="dash-nombre">{{ e.auditoria_nombre }}</td>
                <td class="dash-meta">
                  {{ e.area_nombre || '—' }}
                  <template v-if="e.celula_numero">· Célula {{ e.celula_numero }}</template>
                </td>
                <td>
                  <span class="resultado">
                    <span v-if="e.resumen.total_v" class="v">{{ e.resumen.total_v }} V</span>
                    <span v-if="e.resumen.total_a" class="a">{{ e.resumen.total_a }} A</span>
                    <span v-if="e.resumen.total_r" class="r">{{ e.resumen.total_r }} R</span>
                    <span v-if="!e.resumen.total_v && !e.resumen.total_a && !e.resumen.total_r">—</span>
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
                    v-if="!esFinalizada(e.estado)"
                    class="btn btn-sm"
                    @click="abrirEjecucion(e)"
                  >
                    Continuar
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>
    </template>
  </div>
</template>

<style scoped>
.dashboard {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.stat-detalle {
  font-size: 0.75rem;
  color: var(--c-ink-4, #94a3b8);
}

.panel {
  background: var(--c-surface, #fff);
  border: 1px solid var(--c-line, #e6e9ef);
  border-radius: var(--r-lg, 14px);
  box-shadow: var(--sh-sm, 0 1px 2px rgba(15, 23, 42, 0.05));
  padding: 1.1rem 1.25rem 1.25rem;
}

.panel-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  margin-bottom: 0.9rem;
}

.panel-head h2 {
  font-size: var(--text-md, 0.9375rem);
  font-weight: 700;
  letter-spacing: -0.01em;
}

.panel-link {
  font-size: 0.82rem;
  font-weight: 600;
  color: var(--c-primary, #2563eb);
  text-decoration: none;
}

.panel-link:hover {
  color: var(--c-primary-hover, #1d4ed8);
  text-decoration: underline;
}

.quick-actions {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(230px, 1fr));
  gap: 0.75rem;
}

.quick-action {
  display: flex;
  align-items: center;
  gap: 0.85rem;
  padding: 0.95rem 1rem;
  border: 1px solid var(--c-line, #e6e9ef);
  border-radius: var(--r-md, 10px);
  background: var(--c-surface-2, #f8fafc);
  color: var(--c-ink, #0f172a);
  text-align: left;
  cursor: pointer;
  font: inherit;
  transition: border-color 0.15s var(--ease), box-shadow 0.15s var(--ease), background 0.15s var(--ease);
}

.quick-action:hover {
  border-color: var(--c-primary, #2563eb);
  background: var(--c-surface, #fff);
  box-shadow: 0 4px 14px rgba(37, 99, 235, 0.12);
}

.quick-icon {
  width: 2.6rem;
  height: 2.6rem;
  border-radius: 0.65rem;
  background: var(--c-primary-soft, #eef2ff);
  color: var(--c-primary, #2563eb);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.quick-icon svg {
  width: 1.4rem;
  height: 1.4rem;
  fill: none;
  stroke: currentColor;
  stroke-width: 1.6;
  stroke-linecap: round;
  stroke-linejoin: round;
}

.quick-text {
  display: flex;
  flex-direction: column;
  gap: 0.15rem;
  flex: 1;
  min-width: 0;
}

.quick-text strong {
  font-size: 0.9rem;
  font-weight: 600;
}

.quick-text small {
  font-size: 0.78rem;
  color: var(--c-ink-3, #64748b);
  line-height: 1.35;
}

.quick-arrow {
  width: 1.1rem;
  height: 1.1rem;
  color: var(--c-ink-4, #94a3b8);
  fill: none;
  stroke: currentColor;
  stroke-width: 1.8;
  stroke-linecap: round;
  stroke-linejoin: round;
  flex-shrink: 0;
}

.quick-action:hover .quick-arrow {
  color: var(--c-primary, #2563eb);
}

.dash-fecha {
  white-space: nowrap;
  color: var(--c-ink-3, #64748b);
}

.dash-nombre {
  font-weight: 600;
  color: var(--c-ink, #0f172a);
}

.dash-meta {
  color: var(--c-ink-3, #64748b);
  white-space: nowrap;
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

@media (max-width: 768px) {
  .dashboard {
    gap: 1.25rem;
  }
}
</style>