<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import type { PendienteItem } from '@/types/ejecucion'
import {
  listarPendientes,
  iniciarPendiente,
} from '@/services/ejecucion.service'

const router = useRouter()

const cargando = ref(false)
const error = ref('')
const pendientes = ref<PendienteItem[]>([])
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

async function iniciar(p: PendienteItem) {
  if (!p.ejecucion_id) return
  iniciandoId.value = p.ejecucion_id
  error.value = ''
  try {
    const ejecucion = await iniciarPendiente(p.ejecucion_id)
    router.push({ name: 'ejecutar', query: { id: String(ejecucion.id) } })
  } catch (err) {
    error.value =
      (err as { response?: { data?: { detail?: string } } })?.response?.data
        ?.detail || 'Error al iniciar la auditoría.'
    await cargar()
  } finally {
    iniciandoId.value = null
  }
}

function continuar(p: PendienteItem) {
  if (p.ejecucion_id) {
    router.push({ name: 'ejecutar', query: { id: String(p.ejecucion_id) } })
  }
}

const ESTADO_INFO: Record<string, { label: string; cls: string }> = {
  bloqueada: { label: 'Bloqueada', cls: 'badge-bloqueada' },
  disponible: { label: 'Disponible', cls: 'badge-disponible' },
  atrasada: { label: 'Atrasada', cls: 'badge-atrasada' },
  en_progreso: { label: 'En progreso', cls: 'badge-en-progreso' },
}

function estadoInfo(p: PendienteItem) {
  return ESTADO_INFO[p.estado] || { label: p.estado, cls: 'badge-off' }
}

function areaCelula(p: PendienteItem): string {
  const partes: string[] = []
  if (p.area_nombre) partes.push(p.area_nombre)
  if (p.celula_numero) partes.push(`Célula ${p.celula_numero}`)
  return partes.join(' · ') || '—'
}
</script>

<template>
  <div class="page">
    <header class="page-header">
      <div class="page-header-info">
        <h1>Mis auditorías pendientes</h1>
        <p class="subtitle">
          Auditorías programadas, bloqueadas o en progreso según su frecuencia.
        </p>
      </div>
    </header>

    <p v-if="error" class="msg msg-err">{{ error }}</p>

    <div v-if="cargando" class="msg msg-info">Cargando…</div>

    <div v-else-if="pendientes.length === 0" class="state state-empty">
      <svg class="state-icon" viewBox="0 0 24 24" aria-hidden="true">
        <circle cx="12" cy="12" r="8.6" />
        <path d="M12 7.2V12l3.2 2" />
      </svg>
      <h2>No tienes auditorías pendientes</h2>
      <p>Las auditorías programadas aparecerán aquí.</p>
    </div>

    <div v-else class="table-wrap">
      <table class="table">
        <thead>
          <tr>
            <th>Programada</th>
            <th>Auditoría</th>
            <th>Área · Célula</th>
            <th>Estado</th>
            <th>Contador</th>
            <th class="col-acciones">Acciones</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="p in pendientes" :key="p.auditoria_id + '-' + (p.ejecucion_id ?? 'x')" class="row">
            <td class="col-fecha">{{ formatearFecha(p.fecha_habilita) }}</td>
            <td class="col-auditoria">{{ p.auditoria_nombre }}</td>
            <td>{{ areaCelula(p) }}</td>
            <td>
              <span class="badge" :class="estadoInfo(p).cls">
                {{ estadoInfo(p).label }}
              </span>
            </td>
            <td class="col-contador">{{ p.contador || '—' }}</td>
            <td class="col-acciones" :title="p.tooltip || undefined">
              <button
                v-if="p.accion === 'iniciar'"
                class="btn btn-sm primary"
                :disabled="iniciandoId === p.ejecucion_id"
                @click="iniciar(p)"
              >
                {{ iniciandoId === p.ejecucion_id ? 'Iniciando…' : 'Iniciar' }}
              </button>
              <button
                v-else-if="p.accion === 'continuar'"
                class="btn btn-sm primary"
                @click="continuar(p)"
              >
                Continuar
              </button>
              <button v-else class="btn btn-sm" disabled title="Se habilita según su programación">
                —
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<style scoped>
.col-fecha,
.col-contador {
  white-space: nowrap;
  color: var(--c-ink-3, #64748b);
}

.col-auditoria {
  font-weight: 600;
  color: var(--c-ink, #0f172a);
}
</style>