import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { Area, AreaCreate, AreaUpdate, Celula, CelulaCreate, CelulaUpdate } from '@/types/area'
import {
  obtenerAreas,
  crearArea,
  actualizarArea,
  cambiarEstadoArea,
  obtenerCelulas,
  crearCelula,
  actualizarCelula,
  cambiarEstadoCelula,
} from '@/services/area.service'

export const useAreasStore = defineStore('areas', () => {
  const areas = ref<Area[]>([])
  const cargando = ref(false)

  /* --- Áreas --- */
  async function cargarAreas() {
    cargando.value = true
    try {
      areas.value = await obtenerAreas()
    } finally {
      cargando.value = false
    }
  }

  async function actualizar(id: number, datos: AreaUpdate): Promise<void> {
    await actualizarArea(id, datos)
    await cargarAreas()
  }

  async function cambiarEstado(id: number, activa: boolean): Promise<void> {
    await cambiarEstadoArea(id, activa)
    await cargarAreas()
  }

  async function crear(datos: AreaCreate): Promise<void> {
    await crearArea(datos)
    await cargarAreas()
  }

  /* --- Células --- */
  const celulas = ref<Celula[]>([])
  const cargandoCelulas = ref(false)

  async function cargarCelulas(areaId: number) {
    cargandoCelulas.value = true
    try {
      celulas.value = await obtenerCelulas(areaId)
    } finally {
      cargandoCelulas.value = false
    }
  }

  async function crearCelulaEnArea(areaId: number, datos: CelulaCreate): Promise<void> {
    await crearCelula(areaId, datos)
    await cargarCelulas(areaId)
  }

  async function actualizarCelulaEnArea(
    celulaId: number,
    areaId: number,
    datos: CelulaUpdate,
  ): Promise<void> {
    await actualizarCelula(celulaId, datos)
    await cargarCelulas(areaId)
  }

  async function cambiarEstadoCelulaEnArea(
    celulaId: number,
    areaId: number,
    activa: boolean,
  ): Promise<void> {
    await cambiarEstadoCelula(celulaId, activa)
    await cargarCelulas(areaId)
  }

  return {
    areas,
    cargando,
    cargarAreas,
    actualizar,
    cambiarEstado,
    crear,
    celulas,
    cargandoCelulas,
    cargarCelulas,
    crearCelulaEnArea,
    actualizarCelulaEnArea,
    cambiarEstadoCelulaEnArea,
  }
})
