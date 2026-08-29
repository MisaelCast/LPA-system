import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { Capa, CapaCreate, CapaUpdate } from '@/types/capa'
import {
  obtenerCapas,
  crearCapa,
  actualizarCapa,
  cambiarEstadoCapa,
  eliminarCapa,
} from '@/services/capa.service'

export const useCapasStore = defineStore('capas', () => {
  const capas = ref<Capa[]>([])
  const cargando = ref(false)

  async function cargarCapas() {
    cargando.value = true
    try {
      capas.value = await obtenerCapas()
    } finally {
      cargando.value = false
    }
  }

  async function crear(datos: CapaCreate): Promise<Capa> {
    const capa = await crearCapa(datos)
    await cargarCapas()
    return capa
  }

  async function actualizar(id: number, datos: CapaUpdate): Promise<void> {
    await actualizarCapa(id, datos)
    await cargarCapas()
  }

  async function cambiarEstado(id: number, activa: boolean): Promise<void> {
    await cambiarEstadoCapa(id, activa)
    await cargarCapas()
  }

  async function eliminar(id: number): Promise<void> {
    await eliminarCapa(id)
    await cargarCapas()
  }

  return {
    capas,
    cargando,
    cargarCapas,
    crear,
    actualizar,
    cambiarEstado,
    eliminar,
  }
})
