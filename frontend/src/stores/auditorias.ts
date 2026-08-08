import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { Auditoria, AuditoriaCreate, AuditoriaUpdate } from '@/types/auditoria'
import {
  obtenerAuditorias,
  crearAuditoria,
  actualizarAuditoria,
  cambiarEstadoAuditoria,
} from '@/services/auditoria.service'

export const useAuditoriasStore = defineStore('auditorias', () => {
  const auditorias = ref<Auditoria[]>([])
  const cargando = ref(false)

  async function cargarAuditorias() {
    cargando.value = true
    try {
      auditorias.value = await obtenerAuditorias()
    } finally {
      cargando.value = false
    }
  }

  async function crear(datos: AuditoriaCreate): Promise<Auditoria> {
    const auditoria = await crearAuditoria(datos)
    await cargarAuditorias()
    return auditoria
  }

  async function actualizar(id: number, datos: AuditoriaUpdate): Promise<void> {
    await actualizarAuditoria(id, datos)
    await cargarAuditorias()
  }

  async function cambiarEstado(id: number, activa: boolean): Promise<void> {
    await cambiarEstadoAuditoria(id, activa)
    await cargarAuditorias()
  }

  return {
    auditorias,
    cargando,
    cargarAuditorias,
    crear,
    actualizar,
    cambiarEstado,
  }
})
