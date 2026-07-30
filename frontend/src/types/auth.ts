export interface Token {
  access_token: string
  token_type: string
}

export interface CredencialesLogin {
  correo: string
  contrasena: string
}

export interface Usuario {
  id: number
  nombre: string
  correo: string
  activo: boolean
  rol_id: number
}

export interface UsuarioUpdate {
  nombre?: string
  correo?: string
  rol_id?: number
}
