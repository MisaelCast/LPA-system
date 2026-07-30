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
  rol_nombre: string
}

export interface UsuarioUpdate {
  nombre?: string
  correo?: string
  rol_id?: number
}

export interface UsuarioCreate {
  nombre: string
  correo: string
  contrasena: string
  rol_id: number
  activo: boolean
}
