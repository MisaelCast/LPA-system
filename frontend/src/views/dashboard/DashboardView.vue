<script setup lang="ts">
import { computed } from 'vue'
import PlanSemanal from '@/components/PlanSemanal.vue'
import { useAuthStore } from '@/stores/auth'

const authStore = useAuthStore()

// Por ahora Supervisores y Gerentes no ven la planificación semanal
// (aún no tienen plan propio): su dashboard queda vacío.
const vePlanificacion = computed(
  () => !authStore.isSupervisor && !authStore.isGerente,
)
</script>

<template>
  <div class="dashboard">
    <PlanSemanal v-if="vePlanificacion" mostrar-vacio />
  </div>
</template>

<style scoped>
.dashboard {
  display: flex;
  flex-direction: column;
}
</style>
