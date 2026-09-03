import api from '@/api/api'
import type { Auditoria } from '@/types/auditoria'
import type { Celula } from '@/types/area'
import type {
  EjecucionAuditoria,
  EjecucionAuditoriaDetalle,
  EjecucionAuditoriaListItem,
  EjecucionesFiltros,
  GuardarRespuestasRequest,
  IniciarEjecucionRequest,
  OpcionesFiltrosRevision,
} from '@/types/ejecucion'

export function obtenerAuditoriasDisponibles(): Promise<Auditoria[]> {
  return api
    .get<Auditoria[]>('/ejecuciones-auditoria/disponibles')
    .then((res) => res.data)
}

export function obtenerCelulasDisponibles(auditoriaId: number): Promise<Celula[]> {
  return api
    .get<Celula[]>(`/ejecuciones-auditoria/auditorias/${auditoriaId}/celulas`)
    .then((res) => res.data)
}

export function iniciarEjecucion(
  auditoriaId: number,
  datos: IniciarEjecucionRequest,
): Promise<EjecucionAuditoria> {
  return api
    .post<EjecucionAuditoria>(
      `/ejecuciones-auditoria/auditorias/${auditoriaId}/ejecuciones`,
      datos,
    )
    .then((res) => res.data)
}

export function obtenerEjecucion(ejecucionId: number): Promise<EjecucionAuditoria> {
  return api
    .get<EjecucionAuditoria>(
      `/ejecuciones-auditoria/ejecuciones-auditoria/${ejecucionId}`,
    )
    .then((res) => res.data)
}

export function guardarRespuestas(
  ejecucionId: number,
  datos: GuardarRespuestasRequest,
): Promise<EjecucionAuditoria> {
  return api
    .put<EjecucionAuditoria>(
      `/ejecuciones-auditoria/ejecuciones-auditoria/${ejecucionId}/respuestas`,
      datos,
    )
    .then((res) => res.data)
}

export function finalizarEjecucion(ejecucionId: number): Promise<EjecucionAuditoria> {
  return api
    .post<EjecucionAuditoria>(
      `/ejecuciones-auditoria/ejecuciones-auditoria/${ejecucionId}/finalizar`,
    )
    .then((res) => res.data)
}

export function listarEjecuciones(
  filtros: EjecucionesFiltros = {},
): Promise<EjecucionAuditoriaListItem[]> {
  return api
    .get<EjecucionAuditoriaListItem[]>('/ejecuciones-auditoria', { params: filtros })
    .then((res) => res.data)
}

export function obtenerEjecucionDetalle(
  ejecucionId: number,
): Promise<EjecucionAuditoriaDetalle> {
  return api
    .get<EjecucionAuditoriaDetalle>(`/ejecuciones-auditoria/${ejecucionId}`)
    .then((res) => res.data)
}

export function obtenerOpcionesFiltrosRevision(): Promise<OpcionesFiltrosRevision> {
  return api
    .get<OpcionesFiltrosRevision>('/ejecuciones-auditoria/filtros')
    .then((res) => res.data)
}
