export interface Auditoria {
  id: number
  nombre: string
  descripcion: string | null
  activa: boolean
  tipo_respuesta?: string
  dia_semana?: number | null
  requiere_celula: boolean
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

export interface OpcionCatalogo {
  id: number
  nombre: string
}

export interface PermisosGestionAuditorias {
  puede_gestionar: boolean
  /** IDs de capa permitidos; `null` = sin restricción. */
  capa_ids: number[] | null
  /** IDs de área permitidos; `null` = sin restricción. */
  area_ids: number[] | null
  capas: OpcionCatalogo[]
  areas: OpcionCatalogo[]
  frecuencias: OpcionCatalogo[]
}
