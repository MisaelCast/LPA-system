import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { Usuario } from '@/types/auth'
import { obtenerUsuarios } from '@/services/usuario.service'

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

  return { usuarios, cargando, cargarUsuarios }
})
