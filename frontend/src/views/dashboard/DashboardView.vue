<script setup lang="ts">
import PlanSemanal from '@/components/PlanSemanal.vue'
</script>

<template>
  <div class="dashboard">
    <PlanSemanal mostrar-vacio />
  </div>
</template>

<style scoped>
.dashboard {
  display: flex;
  flex-direction: column;
}
</style>
