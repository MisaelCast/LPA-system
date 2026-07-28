import api from '@/api/api'
import type { Usuario } from '@/types/auth'

export function obtenerUsuarios(): Promise<Usuario[]> {
  return api.get<Usuario[]>('/usuarios').then((res) => res.data)
}
