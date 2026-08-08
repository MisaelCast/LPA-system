import api from '@/api/api'
import type { Criterio, CriterioCreate, CriterioUpdate } from '@/types/criterio'

export function obtenerCriterios(auditoriaId: number): Promise<Criterio[]> {
  return api
    .get<Criterio[]>(`/auditorias/${auditoriaId}/criterios`)
    .then((res) => res.data)
}

export function crearCriterio(
  auditoriaId: number,
  datos: CriterioCreate,
): Promise<Criterio> {
  return api
    .post<Criterio>(`/auditorias/${auditoriaId}/criterios`, datos)
    .then((res) => res.data)
}

export function actualizarCriterio(
  id: number,
  datos: CriterioUpdate,
): Promise<Criterio> {
  return api
    .put<Criterio>(`/criterios/${id}`, datos)
    .then((res) => res.data)
}

export function cambiarEstadoCriterio(
  id: number,
  activo: boolean,
): Promise<Criterio> {
  return api
    .patch<Criterio>(`/criterios/${id}/estado`, { activo })
    .then((res) => res.data)
}
