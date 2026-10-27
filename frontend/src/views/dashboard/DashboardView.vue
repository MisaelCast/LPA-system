<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import PlanSemanal from '@/components/PlanSemanal.vue'
import { listarHallazgos } from '@/services/hallazgo.service'
import { useAuthStore } from '@/stores/auth'
import type { HallazgoDetallado } from '@/types/hallazgo'

const authStore = useAuthStore()

// Por ahora Supervisores y Gerentes no ven la planificación semanal
// (aún no tienen plan propio): su dashboard queda vacío.
const vePlanificacion = computed(
  () =>
    !authStore.isSupervisor &&
    !authStore.isGerente &&
    !authStore.isResponsable,
)

const cargandoHallazgos = ref(false)
const hallazgosNuevos = ref<HallazgoDetallado[]>([])

const mostrarAlerta = computed(() => authStore.isResponsable)

const tituloAlerta = computed(() => {
  const total = hallazgosNuevos.value.length
  if (total === 1) return 'Tienes un hallazgo por atender'
  return `Tienes ${total} hallazgos por atender`
})

const hallazgosVisibles = computed(() => hallazgosNuevos.value.slice(0, 3))
const restantes = computed(() =>
  Math.max(hallazgosNuevos.value.length - hallazgosVisibles.value.length, 0),
)

onMounted(async () => {
  if (!authStore.isResponsable) return
  cargandoHallazgos.value = true
  try {
    hallazgosNuevos.value = await listarHallazgos({
      solo_asignados: true,
      estado: 'abierto',
    })
  } catch {
    hallazgosNuevos.value = []
  } finally {
    cargandoHallazgos.value = false
  }
})

function formatearLimite(iso: string | null): string {
  if (!iso) return ''
  const fecha = new Date(iso)
  if (Number.isNaN(fecha.getTime())) return ''
  return `Límite ${fecha.toLocaleDateString('es-MX', {
    day: 'numeric',
    month: 'short',
  })}`
}
</script>

<template>
  <div class="dashboard">
    <section
      v-if="mostrarAlerta"
      class="alerta-hallazgos"
      aria-live="polite"
      aria-label="Hallazgos asignados"
    >
      <template v-if="cargandoHallazgos">
        <span class="alerta-icono alerta-icono--cargando" aria-hidden="true"></span>
        <div class="alerta-cargando">
          <span class="alerta-skel alerta-skel--titulo"></span>
          <span class="alerta-skel alerta-skel--texto"></span>
        </div>
      </template>

      <template v-else-if="hallazgosNuevos.length">
        <span class="alerta-icono" aria-hidden="true">
          <svg viewBox="0 0 24 24">
            <path d="M6 4v16" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round"/>
            <path d="M6 5h10l-1.8 3.5L16 12H6" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linejoin="round"/>
          </svg>
        </span>

        <div class="alerta-cuerpo">
          <h2 class="alerta-titulo">{{ tituloAlerta }}</h2>
          <p class="alerta-texto">
            Se te asignaron nuevos hallazgos que requieren acción correctiva.
          </p>

          <ul class="alerta-lista">
            <li
              v-for="hallazgo in hallazgosVisibles"
              :key="hallazgo.id"
              class="alerta-item"
            >
              <span class="alerta-item-punto" aria-hidden="true"></span>
              <div class="alerta-item-texto">
                <p class="alerta-item-desc">{{ hallazgo.descripcion }}</p>
                <p class="alerta-item-meta">
                  {{ hallazgo.auditoria_nombre }}
                  <template v-if="hallazgo.celula_numero">
                    · Célula {{ hallazgo.celula_numero }}
                  </template>
                </p>
              </div>
              <span
                v-if="hallazgo.atrasado"
                class="alerta-item-plazo alerta-item-plazo--vencido"
              >Vencido</span>
              <span
                v-else-if="hallazgo.fecha_limite"
                class="alerta-item-plazo"
              >{{ formatearLimite(hallazgo.fecha_limite) }}</span>
            </li>
          </ul>

          <p v-if="restantes > 0" class="alerta-mas">
            y {{ restantes }} hallazgo{{ restantes === 1 ? '' : 's' }} más
          </p>
        </div>

        <RouterLink to="/hallazgos-asignados" class="alerta-cta">
          Atender hallazgos
          <svg viewBox="0 0 24 24" aria-hidden="true">
            <path d="M5 12h13M13 6l6 6-6 6" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
        </RouterLink>
      </template>

      <template v-else>
        <span class="alerta-icono alerta-icono--ok" aria-hidden="true">
          <svg viewBox="0 0 24 24">
            <path d="M5 12.5l4.2 4.2L19 7" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
        </span>

        <div class="alerta-cuerpo">
          <h2 class="alerta-titulo">
            No tienes hallazgos nuevos por atender
          </h2>
          <p class="alerta-texto">
            Cuando te asignen un hallazgo, aparecerá aquí.
          </p>
        </div>

        <RouterLink
          to="/hallazgos-asignados"
          class="alerta-cta alerta-cta--secundaria"
        >
          Ver mis hallazgos
        </RouterLink>
      </template>
    </section>

    <PlanSemanal v-if="vePlanificacion" mostrar-vacio />
  </div>
</template>

<style scoped>
.dashboard {
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}

.alerta-hallazgos {
  display: flex;
  align-items: flex-start;
  gap: 1rem;
  padding: 1.1rem 1.25rem;
  background: var(--c-surface, #fff);
  border: 1px solid var(--c-line, #e6e9ef);
  border-radius: var(--r-lg, 14px);
}

.alerta-icono {
  width: 2.6rem;
  height: 2.6rem;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 0.75rem;
  background: var(--c-warn-soft, #fef3c7);
  color: var(--c-warn-ink, #92400e);
}

.alerta-icono svg {
  width: 1.35rem;
  height: 1.35rem;
}

.alerta-icono--cargando {
  background: var(--c-surface-3, #f1f5f9);
}

.alerta-icono--ok {
  background: var(--c-ok-soft, #dcfce7);
  color: var(--c-ok-ink, #166534);
}

.alerta-cargando {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 0.55rem;
  padding-top: 0.2rem;
}

.alerta-skel {
  display: block;
  height: 0.75rem;
  border-radius: 4px;
  background: linear-gradient(
    90deg,
    var(--c-surface-3, #f1f5f9) 25%,
    var(--c-line, #e6e9ef) 37%,
    var(--c-surface-3, #f1f5f9) 63%
  );
  background-size: 400% 100%;
  animation: alerta-shimmer 1.4s ease infinite;
}

.alerta-skel--titulo {
  width: min(22rem, 70%);
  height: 0.95rem;
}

.alerta-skel--texto {
  width: min(30rem, 88%);
}

@keyframes alerta-shimmer {
  from {
    background-position: 100% 50%;
  }
  to {
    background-position: 0 50%;
  }
}

.alerta-cuerpo {
  flex: 1;
  min-width: 0;
}

.alerta-titulo {
  font-size: var(--text-lg, 1.0625rem);
  line-height: 1.3;
  letter-spacing: -0.015em;
  color: var(--c-ink, #0f172a);
}

.alerta-texto {
  margin-top: 0.25rem;
  font-size: 0.82rem;
  color: var(--c-ink-3, #64748b);
}

.alerta-lista {
  list-style: none;
  margin: 0.8rem 0 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 0.45rem;
}

.alerta-item {
  display: flex;
  align-items: center;
  gap: 0.65rem;
  padding: 0.55rem 0.7rem;
  background: var(--c-surface-2, #f8fafc);
  border: 1px solid var(--c-line, #e6e9ef);
  border-radius: var(--r-sm, 8px);
}

.alerta-item-punto {
  width: 0.45rem;
  height: 0.45rem;
  flex-shrink: 0;
  border-radius: 50%;
  background: var(--c-warn, #d97706);
}

.alerta-item-texto {
  flex: 1;
  min-width: 0;
}

.alerta-item-desc {
  font-size: 0.82rem;
  color: var(--c-ink-2, #334155);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.alerta-item-meta {
  margin-top: 0.1rem;
  font-size: 0.72rem;
  color: var(--c-ink-3, #64748b);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.alerta-item-plazo {
  flex-shrink: 0;
  font-size: 0.7rem;
  font-weight: 600;
  color: var(--c-ink-3, #64748b);
  white-space: nowrap;
}

.alerta-item-plazo--vencido {
  color: var(--c-danger-ink, #b91c1c);
}

.alerta-mas {
  margin-top: 0.55rem;
  font-size: 0.75rem;
  color: var(--c-ink-3, #64748b);
}

.alerta-cta {
  flex-shrink: 0;
  align-self: center;
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  padding: 0.55rem 0.9rem;
  border-radius: var(--r-md, 10px);
  background: var(--c-primary, #2563eb);
  color: #fff;
  font-size: 0.8rem;
  font-weight: 600;
  text-decoration: none;
  white-space: nowrap;
  transition: background 0.15s var(--ease);
}

.alerta-cta:hover {
  background: var(--c-primary-hover, #1d4ed8);
}

.alerta-cta--secundaria {
  background: var(--c-surface, #fff);
  color: var(--c-ink-2, #334155);
  border: 1px solid var(--c-line-2, #d5dae3);
}

.alerta-cta--secundaria:hover {
  background: var(--c-surface-2, #f8fafc);
  border-color: var(--c-line-3, #cbd5e1);
}

.alerta-cta svg {
  width: 0.9rem;
  height: 0.9rem;
}

@media (max-width: 820px) {
  .alerta-hallazgos {
    flex-wrap: wrap;
    gap: 0.85rem;
    padding: 1rem;
  }

  .alerta-cta {
    width: 100%;
    justify-content: center;
    align-self: stretch;
  }
}

@media (prefers-reduced-motion: reduce) {
  .alerta-skel {
    animation: none;
  }
}
</style>
