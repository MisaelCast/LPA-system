import type { Area, Celula } from '@/types/area'
import type { Usuario } from '@/types/auth'

export interface CriterioRespuesta {
  id: number
  descripcion: string
  orden: number
  seccion?: string | null
  subseccion?: string | null
  subtitulo?: string | null
  respuesta_valor: string | null
  respuesta_observaciones: string | null
  respuesta_id: number | null
  hallazgo_id: number | null
  hallazgo_descripcion: string | null
}

export interface EjecucionAuditoria {
  id: number
  fecha: string
  observaciones: string | null
  estado: string
  auditoria_id: number
  usuario_id: number
  celula_id: number | null
  auditoria_nombre: string
  area_nombre: string | null
  celula_numero: number | null
  auditor_nombre: string
  tipo_respuesta?: string
  criterios: CriterioRespuesta[]
}

export interface RespuestaItem {
  criterio_id: number
  valor: string
  observaciones: string | null
}

export interface GuardarRespuestasRequest {
  respuestas: RespuestaItem[]
}

export interface IniciarEjecucionRequest {
  celula_id: number | null
}

export interface EjecucionResumen {
  total_criterios: number
  total_v: number
  total_a: number
  total_r: number
  total_cumple?: number
  total_no_cumple?: number
  total_na?: number
}

export interface EjecucionAuditoriaListItem {
  id: number
  fecha: string
  estado: string
  auditoria_id: number
  auditoria_nombre: string
  usuario_id: number
  usuario_nombre: string
  celula_id: number | null
  celula_numero: number | null
  area_id: number | null
  area_nombre: string | null
  tipo_respuesta?: string
  resumen: EjecucionResumen
}

export interface EjecucionAuditoriaDetalle extends EjecucionAuditoria {
  area_id: number | null
  resumen: EjecucionResumen
}

export interface EjecucionesFiltros {
  skip?: number
  limit?: number
  auditoria_id?: number
  celula_id?: number
  usuario_id?: number
  estado?: string
  fecha_desde?: string
  fecha_hasta?: string
  area_id?: number
  tipo_respuesta?: string
  solo_auditores?: boolean
  solo_propias?: boolean
}

export interface OpcionesFiltrosRevision {
  areas: Area[]
  celulas: Celula[]
  auditores: Usuario[]
}