export interface CriterioRespuesta {
  id: number
  descripcion: string
  orden: number
  respuesta_valor: string | null
  respuesta_observaciones: string | null
  respuesta_id: number | null
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
