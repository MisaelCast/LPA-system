import api from '@/api/api'
import type { Usuario, UsuarioUpdate } from '@/types/auth'

export function obtenerUsuarios(): Promise<Usuario[]> {
  return api.get<Usuario[]>('/usuarios').then((res) => res.data)
}

export function actualizarUsuario(
  id: number,
  datos: UsuarioUpdate,
): Promise<Usuario> {
  return api.put<Usuario>(`/usuarios/${id}`, datos).then((res) => res.data)
}
