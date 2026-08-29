import api from '@/api/api'
import type { Area, AreaCreate, AreaUpdate, Celula, CelulaCreate, CelulaUpdate } from '@/types/area'

export function obtenerAreas(): Promise<Area[]> {
  return api.get<Area[]>('/areas').then((res) => res.data)
}

export function crearArea(datos: AreaCreate): Promise<Area> {
  return api.post<Area>('/areas', datos).then((res) => res.data)
}

export function actualizarArea(
  id: number,
  datos: AreaUpdate,
): Promise<Area> {
  return api.put<Area>(`/areas/${id}`, datos).then((res) => res.data)
}

export function cambiarEstadoArea(
  id: number,
  activa: boolean,
): Promise<Area> {
  return api
    .patch<Area>(`/areas/${id}/estado`, { activa })
    .then((res) => res.data)
}

export function eliminarArea(id: number): Promise<void> {
  return api.delete(`/areas/${id}`).then(() => undefined)
}

/* --- Células --- */

export function obtenerCelulas(areaId: number): Promise<Celula[]> {
  return api
    .get<Celula[]>(`/areas/${areaId}/celulas`)
    .then((res) => res.data)
}

export function crearCelula(
  areaId: number,
  datos: CelulaCreate,
): Promise<Celula> {
  return api
    .post<Celula>(`/areas/${areaId}/celulas`, datos)
    .then((res) => res.data)
}

export function actualizarCelula(
  id: number,
  datos: CelulaUpdate,
): Promise<Celula> {
  return api
    .put<Celula>(`/celulas/${id}`, datos)
    .then((res) => res.data)
}

export function cambiarEstadoCelula(
  id: number,
  activa: boolean,
): Promise<Celula> {
  return api
    .patch<Celula>(`/celulas/${id}/estado`, { activa })
    .then((res) => res.data)
}

export function eliminarCelula(id: number): Promise<void> {
  return api.delete(`/celulas/${id}`).then(() => undefined)
}
