export interface Capa {
  id: number
  nombre: string
  descripcion: string | null
  activa: boolean
}

export interface CapaCreate {
  nombre: string
  descripcion?: string
  activa: boolean
}

export interface CapaUpdate {
  nombre?: string
  descripcion?: string
  activa?: boolean
}
