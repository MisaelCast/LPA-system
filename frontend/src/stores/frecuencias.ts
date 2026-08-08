import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { Frecuencia } from '@/types/frecuencia'
import { obtenerFrecuencias } from '@/services/frecuencia.service'

export const useFrecuenciasStore = defineStore('frecuencias', () => {
  const frecuencias = ref<Frecuencia[]>([])

  async function cargarFrecuencias() {
    frecuencias.value = await obtenerFrecuencias()
  }

  return { frecuencias, cargarFrecuencias }
})
