import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { Criterio, CriterioCreate, CriterioUpdate } from '@/types/criterio'
import {
  obtenerCriterios,
  crearCriterio,
  actualizarCriterio,
  cambiarEstadoCriterio,
} from '@/services/criterio.service'

export const useCriteriosStore = defineStore('criterios', () => {
  const criteriosPorAuditoria = ref<Record<number, Criterio[]>>({})

  function criteriosDe(auditoriaId: number): Criterio[] {
    return criteriosPorAuditoria.value[auditoriaId] ?? []
  }

  async function cargarCriterios(auditoriaId: number) {
    criteriosPorAuditoria.value[auditoriaId] = await obtenerCriterios(
      auditoriaId,
    )
  }

  async function cargarTodosLosCriterios(auditoriaIds: number[]) {
    const resultados = await Promise.all(
      auditoriaIds.map((id) =>
        obtenerCriterios(id)
          .then((criterios) => [id, criterios] as const)
          .catch(() => [id, [] as Criterio[]] as const),
      ),
    )
    const mapa: Record<number, Criterio[]> = {}
    for (const [id, criterios] of resultados) {
      mapa[id] = criterios
    }
    criteriosPorAuditoria.value = mapa
  }

  async function crearEnAuditoria(
    auditoriaId: number,
    datos: CriterioCreate,
  ): Promise<void> {
    await crearCriterio(auditoriaId, datos)
    await cargarCriterios(auditoriaId)
  }

  async function actualizar(
    auditoriaId: number,
    criterioId: number,
    datos: CriterioUpdate,
  ): Promise<void> {
    await actualizarCriterio(criterioId, datos)
    await cargarCriterios(auditoriaId)
  }

  async function cambiarEstado(
    auditoriaId: number,
    criterioId: number,
    activo: boolean,
  ): Promise<void> {
    await cambiarEstadoCriterio(criterioId, activo)
    await cargarCriterios(auditoriaId)
  }

  return {
    criteriosPorAuditoria,
    criteriosDe,
    cargarCriterios,
    cargarTodosLosCriterios,
    crearEnAuditoria,
    actualizar,
    cambiarEstado,
  }
})
