import api from '@/api/api'
import type { Frecuencia } from '@/types/frecuencia'

export function obtenerFrecuencias(): Promise<Frecuencia[]> {
  return api.get<Frecuencia[]>('/frecuencias').then((res) => res.data)
}
