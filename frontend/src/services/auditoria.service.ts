import api from '@/api/api'
import type { Auditoria, AuditoriaCreate, AuditoriaUpdate } from '@/types/auditoria'

export function obtenerAuditorias(): Promise<Auditoria[]> {
  return api.get<Auditoria[]>('/auditorias').then((res) => res.data)
}

export function crearAuditoria(datos: AuditoriaCreate): Promise<Auditoria> {
  return api.post<Auditoria>('/auditorias', datos).then((res) => res.data)
}

export function actualizarAuditoria(
  id: number,
  datos: AuditoriaUpdate,
): Promise<Auditoria> {
  return api.put<Auditoria>(`/auditorias/${id}`, datos).then((res) => res.data)
}

export function cambiarEstadoAuditoria(
  id: number,
  activa: boolean,
): Promise<Auditoria> {
  return api
    .patch<Auditoria>(`/auditorias/${id}/estado`, { activa })
    .then((res) => res.data)
}

export function eliminarAuditoria(id: number): Promise<void> {
  return api.delete(`/auditorias/${id}`).then(() => undefined)
}
