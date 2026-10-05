export interface Criterio {
  id: number
  descripcion: string
  orden: number
  activo: boolean
  auditoria_id: number
  seccion?: string | null
  subseccion?: string | null
  subtitulo?: string | null
}

export interface CriterioCreate {
  descripcion: string
  orden: number
  activo: boolean
}

export interface CriterioUpdate {
  descripcion?: string
  orden?: number
  activo?: boolean
}
