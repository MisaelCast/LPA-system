export interface Asignacion {
  area_ids: number[]
  celula_ids: number[]
  supervisor_ids: number[]
}

export interface AsignacionOpciones {
  areas: {
    id: number
    nombre: string
    descripcion: string | null
    activa: boolean
  }[]
  celulas: {
    id: number
    numero: number
    activa: boolean
    area_id: number
  }[]
  supervisores: {
    id: number
    nombre: string
    correo: string
    activo: boolean
    rol_id: number
    rol_nombre: string
  }[]
}