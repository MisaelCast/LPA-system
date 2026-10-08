<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import type { EjecucionAuditoriaListItem } from '@/types/ejecucion'
import {
  listarPendientes,
  iniciarPendiente,
} from '@/services/ejecucion.service'

const router = useRouter()

const cargando = ref(false)
const error = ref('')
const pendientes = ref<EjecucionAuditoriaListItem[]>([])
const iniciandoId = ref<number | null>(null)

onMounted(cargar)

async function cargar() {
  cargando.value = true
  error.value = ''
  try {
    pendientes.value = await listarPendientes()
  } catch (err) {
    error.value =
      (err as { response?: { data?: { detail?: string } } })?.response?.data
        ?.detail || 'Error al cargar las auditorías pendientes.'
  } finally {
    cargando.value = false
  }
}

function formatearFecha(iso: string | null | undefined): string {
  if (!iso) return '—'
  const d = new Date(iso)
  if (Number.isNaN(d.getTime())) return iso
  return `${String(d.getDate()).padStart(2, '0')}/${String(d.getMonth() + 1).padStart(2, '0')}/${d.getFullYear()}`
}

async function iniciar(p: EjecucionAuditoriaListItem) {
  iniciandoId.value = p.id
  error.value = ''
  try {
    const ejecucion = await iniciarPendiente(p.id)
    router.push({ name: 'ejecutar', query: { id: String(ejecucion.id) } })
  } catch (err) {
    error.value =
      (err as { response?: { data?: { detail?: string } } })?.response?.data
        ?.detail || 'Error al iniciar la auditoría.'
    pendientes.value = pendientes.value.filter((x) => x.id !== p.id)
  } finally {
    iniciandoId.value = null
  }
}

function continuar(p: EjecucionAuditoriaListItem) {
  router.push({ name: 'ejecutar', query: { id: String(p.id) } })
}

function estadoInfo(p: EjecucionAuditoriaListItem) {
  if (p.vencida) return { label: 'Vencida', cls: 'badge-vencida' }
  if (p.estado === 'pendiente') return { label: 'Pendiente', cls: 'badge-pendiente' }
  return { label: 'En progreso', cls: 'badge-progreso' }
}
</script>

<template>
  <div class="page">
    <header class="page-header">
      <div class="page-header-info">
        <h1>Mis auditorías pendientes</h1>
        <p class="subtitle">
          Ejecuciones programadas por iniciar y las que quedaron en progreso.
        </p>
      </div>
    </header>

    <p v-if="error" class="msg msg-err">{{ error }}</p>

    <div v-if="cargando" class="msg msg-info">Cargando…</div>

    <div
      v-else-if="pendientes.length === 0"
      class="state state-empty"
    >
      <svg class="state-icon" viewBox="0 0 24 24" aria-hidden="true">
        <circle cx="12" cy="12" r="8.6" />
        <path d="M12 7.2V12l3.2 2" />
      </svg>
      <h2>No tienes auditorías pendientes</h2>
      <p>Las ejecuciones programadas aparecerán aquí cuando el sistema las genere.</p>
    </div>

    <div v-else class="table-wrap">
      <table class="table">
        <thead>
          <tr>
            <th>Programada</th>
            <th>Auditoría</th>
            <th>Área</th>
            <th>Célula</th>
            <th>Estado</th>
            <th class="col-acciones">Acciones</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="p in pendientes" :key="p.id" class="row">
            <td class="col-fecha">{{ formatearFecha(p.fecha_programada) }}</td>
            <td class="col-auditoria">{{ p.auditoria_nombre }}</td>
            <td>{{ p.area_nombre || '—' }}</td>
            <td>{{ p.celula_numero ? `Célula ${p.celula_numero}` : '—' }}</td>
            <td>
              <span
                class="badge"
                :class="estadoInfo(p).cls"
              >
                {{ estadoInfo(p).label }}
              </span>
            </td>
            <td class="col-acciones">
              <button
                v-if="p.estado === 'pendiente'"
                class="btn btn-sm primary"
                :disabled="iniciandoId === p.id"
                @click="iniciar(p)"
              >
                {{ iniciandoId === p.id ? 'Iniciando…' : 'Iniciar' }}
              </button>
              <button
                v-else
                class="btn btn-sm primary"
                @click="continuar(p)"
              >
                Continuar
              </button>
            </td>
          </tr>
        </tbody>
      </table>
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
</style>