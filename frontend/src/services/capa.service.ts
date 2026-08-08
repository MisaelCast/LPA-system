import api from '@/api/api'
import type { Capa, CapaCreate, CapaUpdate } from '@/types/capa'

export function obtenerCapas(): Promise<Capa[]> {
  return api.get<Capa[]>('/capas').then((res) => res.data)
}

export function crearCapa(datos: CapaCreate): Promise<Capa> {
  return api.post<Capa>('/capas', datos).then((res) => res.data)
}

export function actualizarCapa(
  id: number,
  datos: CapaUpdate,
): Promise<Capa> {
  return api.put<Capa>(`/capas/${id}`, datos).then((res) => res.data)
}

export function cambiarEstadoCapa(
  id: number,
  activa: boolean,
): Promise<Capa> {
  return api
    .patch<Capa>(`/capas/${id}/estado`, { activa })
    .then((res) => res.data)
}
