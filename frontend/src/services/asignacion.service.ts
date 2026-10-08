import api from '@/api/api'
import type { Asignacion, AsignacionOpciones } from '@/types/asignacion'

export function obtenerAsignacionOpciones(): Promise<AsignacionOpciones> {
  return api
    .get<AsignacionOpciones>('/usuarios/asignacion-opciones')
    .then((res) => res.data)
}

export function obtenerAsignacion(usuarioId: number): Promise<Asignacion> {
  return api
    .get<Asignacion>(`/usuarios/${usuarioId}/asignacion`)
    .then((res) => res.data)
}

export function guardarAsignacion(
  usuarioId: number,
  datos: Asignacion,
): Promise<Asignacion> {
  return api
    .put<Asignacion>(`/usuarios/${usuarioId}/asignacion`, datos)
    .then((res) => res.data)
}