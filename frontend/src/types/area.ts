export interface Area {
  id: number
  nombre: string
  descripcion: string | null
  activa: boolean
}

export interface AreaCreate {
  nombre: string
  descripcion?: string
  activa: boolean
}

export interface AreaUpdate {
  nombre?: string
  descripcion?: string
  activa?: boolean
}

export interface Celula {
  id: number
  numero: number
  activa: boolean
  area_id: number
}

export interface CelulaCreate {
  numero: number
  activa: boolean
}

export interface CelulaUpdate {
  numero?: number
  activa?: boolean
}
