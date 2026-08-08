export interface Auditoria {
  id: number
  nombre: string
  descripcion: string | null
  activa: boolean
  capa_id: number
  frecuencia_id: number
  area_id: number | null
  capa_nombre: string
  frecuencia_nombre: string
  area_nombre: string | null
}

export interface AuditoriaCreate {
  nombre: string
  descripcion?: string
  activa: boolean
  capa_id: number
  frecuencia_id: number
  area_id: number | null
}

export interface AuditoriaUpdate {
  nombre?: string
  descripcion?: string
  activa?: boolean
  capa_id?: number
  frecuencia_id?: number
  area_id?: number
}
