<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { obtenerPlanSemanal } from '@/services/ejecucion.service'
import type { PlanSemanal } from '@/types/programacion'

const cargando = ref(true)
const plan = ref<PlanSemanal | null>(null)

onMounted(async () => {
  try {
    plan.value = await obtenerPlanSemanal()
  } catch {
    plan.value = null
  } finally {
    cargando.value = false
  }
})

const tienePlan = computed(() => (plan.value?.areas.length ?? 0) > 0)

const rango = computed(() => {
  const p = plan.value
  if (!p) return ''
  const inicio = new Date(`${p.semana_inicio}T00:00:00`)
  const fin = new Date(`${p.semana_fin}T00:00:00`)
  const fmt = (d: Date) => d.toLocaleDateString('es-MX', { day: 'numeric', month: 'short' })
  return `${fmt(inicio)} – ${fmt(fin)}`
})

const corto = (nombre: string) => nombre.slice(0, 3)
</script>

<template>
  <section v-if="cargando || tienePlan" class="plan">
    <header class="plan-header">
      <div class="plan-header-texto">
        <h2>Planificación de la semana</h2>
        <p v-if="plan && rango">Semana del {{ rango }}</p>
      </div>
      <span v-if="plan" class="plan-badge">Lunes a viernes</span>
    </header>

    <div v-if="cargando" class="plan-loading">
      <div class="plan-spinner"></div>
    </div>

    <div v-else v-for="area in plan?.areas" :key="area.area_id" class="plan-area">
      <div class="plan-dias">
        <div
          v-for="dia in area.dias"
          :key="dia.dia_semana"
          class="plan-dia"
          :class="{ 'plan-dia--hoy': dia.es_hoy }"
        >
          <div class="plan-dia-top">
            <span class="plan-dia-nombre">{{ corto(dia.nombre_dia) }}</span>
            <span class="plan-dia-fecha">{{ dia.fecha.slice(8, 10) }}</span>
            <span v-if="dia.es_hoy" class="plan-hoy">Hoy</span>
          </div>
          <p class="plan-dia-auditoria">{{ dia.auditoria_nombre || 'Sin auditoría' }}</p>
        </div>
      </div>
    </div>
  </section>
</template>

<style scoped>
.plan {
  background: #fff;
  border: 1px solid #e2e8f0;
  border-radius: 0.6rem;
  padding: 1rem 1.1rem 1.1rem;
  box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04);
  margin-bottom: 1.25rem;
}

.plan-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 1rem;
  margin-bottom: 0.85rem;
}

.plan-header h2 {
  margin: 0;
  font-size: 0.95rem;
  font-weight: 700;
  color: #0f172a;
}

.plan-header p {
  margin: 0.15rem 0 0;
  font-size: 0.78rem;
  color: #64748b;
}

.plan-badge {
  flex-shrink: 0;
  font-size: 0.68rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  color: #1d4ed8;
  background: #eff6ff;
  border-radius: 999px;
  padding: 0.2rem 0.6rem;
}

.plan-loading {
  display: flex;
  justify-content: center;
  padding: 1rem 0;
}

.plan-spinner {
  width: 1.4rem;
  height: 1.4rem;
  border: 3px solid #e2e8f0;
  border-top-color: #3b82f6;
  border-radius: 50%;
  animation: plan-spin 0.8s linear infinite;
}

@keyframes plan-spin {
  to {
    transform: rotate(360deg);
  }
}

.plan-area + .plan-area {
  margin-top: 0.75rem;
  padding-top: 0.75rem;
  border-top: 1px solid #f1f5f9;
}

.plan-dias {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 0.5rem;
}

.plan-dia {
  border: 1px solid #e2e8f0;
  border-radius: 0.5rem;
  padding: 0.55rem 0.6rem;
  background: #f8fafc;
  min-width: 0;
}

.plan-dia--hoy {
  border-color: #93c5fd;
  background: #eff6ff;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.plan-dia-top {
  display: flex;
  align-items: center;
  gap: 0.35rem;
  margin-bottom: 0.3rem;
}

.plan-dia-nombre {
  font-size: 0.68rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: #64748b;
}

.plan-dia-fecha {
  font-size: 0.68rem;
  font-weight: 600;
  color: #94a3b8;
}

.plan-hoy {
  margin-left: auto;
  font-size: 0.6rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  color: #1d4ed8;
}

.plan-dia-auditoria {
  margin: 0;
  font-size: 0.8rem;
  font-weight: 600;
  line-height: 1.3;
  color: #0f172a;
  overflow-wrap: anywhere;
}

.plan-dia--hoy .plan-dia-auditoria {
  color: #1e3a8a;
}

@media (max-width: 900px) {
  .plan-dias {
    grid-template-columns: repeat(2, 1fr);
  }
}
</style>
