export interface HallazgoDetallado {
  id: number
  descripcion: string
  fecha_creacion: string
  respuesta_id: number
  tipo: string
  respuesta_valor: string
  criterio_id: number
  criterio_descripcion: string
  criterio_orden: number
  ejecucion_id: number
  ejecucion_estado: string
  auditoria_id: number
  auditoria_nombre: string
  celula_id: number | null
  celula_numero: number | null
}

export interface HallazgoCreate {
  descripcion: string
}

export interface HallazgoUpdate {
  descripcion?: string
}