import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { Usuario, UsuarioUpdate } from '@/types/auth'
import { obtenerUsuarios, actualizarUsuario, cambiarEstadoUsuario } from '@/services/usuario.service'

export const useUsuariosStore = defineStore('usuarios', () => {
  const usuarios = ref<Usuario[]>([])
  const cargando = ref(false)

  async function cargarUsuarios() {
    cargando.value = true
    try {
      usuarios.value = await obtenerUsuarios()
    } finally {
      cargando.value = false
    }
  }

  async function actualizar(id: number, datos: UsuarioUpdate): Promise<void> {
    await actualizarUsuario(id, datos)
    await cargarUsuarios()
  }

  async function cambiarEstado(id: number, activo: boolean): Promise<void> {
    await cambiarEstadoUsuario(id, activo)
    await cargarUsuarios()
  }

  return { usuarios, cargando, cargarUsuarios, actualizar, cambiarEstado }
})
