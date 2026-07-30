import api from '@/api/api'
import type { Rol } from '@/types/rol'

export function obtenerRoles(): Promise<Rol[]> {
  return api.get<Rol[]>('/roles').then((res) => res.data)
}
