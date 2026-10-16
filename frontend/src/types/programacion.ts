export interface DiaPlan {
  dia_semana: number
  fecha: string
  nombre_dia: string
  auditoria_id: number | null
  auditoria_nombre: string | null
  es_hoy: boolean
}

export interface AreaPlan {
  area_id: number
  area_nombre: string
  dias: DiaPlan[]
}

export interface PlanSemanal {
  semana_inicio: string
  semana_fin: string
  areas: AreaPlan[]
}
