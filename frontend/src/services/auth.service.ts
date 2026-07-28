import api from '@/api/api'
import type { CredencialesLogin, Token } from '@/types/auth'

export function login(credentials: CredencialesLogin): Promise<Token> {
  return api.post<Token>('/auth/login', credentials).then((res) => res.data)
}

export function logout(): void {
  // Placeholder — se implementará cuando exista el flujo de cierre de sesión.
}
