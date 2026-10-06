export type EstadoHallazgo = 'abierto' | 'en_proceso' | 'cerrado'

export interface HallazgoDetallado {
  id: number
  descripcion: string
  fecha_creacion: string
  respuesta_id: number
  estado: EstadoHallazgo
  accion_correctiva: string | null
  area_responsable_id: number | null
  area_responsable_nombre: string | null
  fecha_cierre: string | null
  tipo: string
  respuesta_valor: string
  criterio_id: number
  criterio_descripcion: string
  criterio_orden: number
  ejecucion_id: number
  ejecucion_estado: string
  auditoria_id: number
  auditoria_nombre: string
  auditor_id: number
  celula_id: number | null
  celula_numero: number | null
}

export interface HallazgoCreate {
  descripcion: string
  area_responsable_id?: number | null
}

export interface HallazgoUpdate {
  descripcion?: string
}

export interface HallazgoSeguimientoUpdate {
  estado?: EstadoHallazgo
  accion_correctiva?: string | null
  area_responsable_id?: number
}

export interface HallazgoFiltros {
  estado?: EstadoHallazgo
  area_responsable_id?: number
}
