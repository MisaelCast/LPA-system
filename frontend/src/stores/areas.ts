import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { Area, AreaCreate, AreaUpdate, Celula, CelulaCreate, CelulaUpdate } from '@/types/area'
import {
  obtenerAreas,
  crearArea,
  actualizarArea,
  cambiarEstadoArea,
  eliminarArea,
  obtenerCelulas,
  crearCelula,
  actualizarCelula,
  cambiarEstadoCelula,
  eliminarCelula,
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

  async function crear(datos: AreaCreate): Promise<Area> {
    const area = await crearArea(datos)
    await cargarAreas()
    return area
  }

  /* --- Células: mapa por área --- */
  const celulasPorArea = ref<Record<number, Celula[]>>({})

  function celulasDe(areaId: number): Celula[] {
    return celulasPorArea.value[areaId] ?? []
  }

  async function cargarCelulas(areaId: number) {
    celulasPorArea.value[areaId] = await obtenerCelulas(areaId)
  }

  async function cargarTodasLasCelulas(areaIds: number[]) {
    const resultados = await Promise.all(
      areaIds.map((id) =>
        obtenerCelulas(id)
          .then((celulas) => [id, celulas] as const)
          .catch(() => [id, [] as Celula[]] as const),
      ),
    )
    const mapa: Record<number, Celula[]> = {}
    for (const [id, celulas] of resultados) {
      mapa[id] = celulas
    }
    celulasPorArea.value = mapa
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

  async function eliminar(id: number): Promise<void> {
    await eliminarArea(id)
    await cargarAreas()
  }

  async function eliminarCelulaEnArea(
    celulaId: number,
    areaId: number,
  ): Promise<void> {
    await eliminarCelula(celulaId)
    await cargarCelulas(areaId)
  }

  return {
    areas,
    cargando,
    cargarAreas,
    actualizar,
    cambiarEstado,
    crear,
    celulasPorArea,
    celulasDe,
    cargarCelulas,
    cargarTodasLasCelulas,
    crearCelulaEnArea,
    actualizarCelulaEnArea,
    cambiarEstadoCelulaEnArea,
    eliminar,
    eliminarCelulaEnArea,
  }
})
