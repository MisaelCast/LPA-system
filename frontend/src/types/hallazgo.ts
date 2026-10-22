export type EstadoHallazgo =
  | 'abierto'
  | 'en_correccion'
  | 'cierre_solicitado'
  | 'cerrado'

export interface Evidencia {
  id: number
  fecha_carga: string
  tipo_archivo: string
  tipo: 'original' | 'correccion'
  url: string | null
}

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
  fecha_limite: string | null
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
  evidencias: Evidencia[]
  responsable_id: number | null
  responsable_nombre: string | null
  atrasado: boolean
  dias_sin_actualizar: number | null
  reincidente: boolean
}

export interface Seguimiento {
  id: number
  hallazgo_id: number
  usuario_id: number
  usuario_nombre: string
  tipo: string
  detalle: string | null
  estado_desde: string | null
  estado_hasta: string | null
  fecha_creacion: string
}

export interface ResponsableResumen {
  id: number
  nombre: string
  correo: string
}

export interface HallazgoCreate {
  descripcion: string
  area_responsable_id?: number | null
  responsable_id?: number | null
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
  solo_propios?: boolean
  solo_auditores?: boolean
  solo_asignados?: boolean
  atrasados?: boolean
  sin_actualizar?: boolean
  cierre_pendiente?: boolean
  reincidencia?: boolean
}

export interface AsignarResponsableRequest {
  responsable_id: number
  fecha_limite?: string | null
}

export interface AvanceTicketRequest {
  accion_correctiva?: string | null
  comentario?: string | null
}

export interface CierreSolicitudRequest {
  comentario?: string | null
}

export interface CierreResolucionRequest {
  aprobar: boolean
  observacion?: string | null
}
