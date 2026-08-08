export interface Criterio {
  id: number
  descripcion: string
  orden: number
  activo: boolean
  auditoria_id: number
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
