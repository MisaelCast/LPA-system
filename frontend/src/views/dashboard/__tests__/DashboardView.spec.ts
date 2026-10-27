import { describe, it, expect, beforeEach, vi } from 'vitest'
import { flushPromises, mount, RouterLinkStub } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { useAuthStore } from '@/stores/auth'
import type { HallazgoDetallado } from '@/types/hallazgo'

const listarHallazgosMock = vi.fn()

vi.mock('@/services/hallazgo.service', () => ({
  listarHallazgos: (...args: unknown[]) => listarHallazgosMock(...args),
}))

vi.mock('@/components/PlanSemanal.vue', () => ({
  default: { template: '<div class="plan-stub" />' },
}))

import DashboardView from '../DashboardView.vue'

function autenticar(rolNombre: string) {
  const auth = useAuthStore()
  auth.usuario = {
    id: 1,
    nombre: 'Usuario',
    correo: 'u@lpa.com',
    activo: true,
    rol_id: 1,
    rol_nombre: rolNombre,
  }
}

function hallazgo(
  id: number,
  cambios: Partial<HallazgoDetallado> = {},
): HallazgoDetallado {
  return {
    id,
    descripcion: `Hallazgo ${id}`,
    fecha_creacion: '2026-10-27T10:00:00+00:00',
    respuesta_id: 100 + id,
    estado: 'abierto',
    accion_correctiva: null,
    area_responsable_id: 1,
    area_responsable_nombre: 'Ensamble Final',
    fecha_cierre: null,
    fecha_limite: '2026-10-30T10:00:00+00:00',
    tipo: 'R',
    respuesta_valor: 'R',
    criterio_id: id,
    criterio_descripcion: 'Criterio',
    criterio_orden: id,
    ejecucion_id: 10,
    ejecucion_estado: 'finalizada',
    auditoria_id: 1,
    auditoria_nombre: 'Auditoría de Proceso - Ensamble Final',
    auditor_id: 2,
    celula_id: 1,
    celula_numero: 6,
    evidencias: [],
    responsable_id: 1,
    responsable_nombre: 'Usuario',
    atrasado: false,
    dias_sin_actualizar: 0,
    reincidente: false,
    ...cambios,
  }
}

function montar() {
  return mount(DashboardView, {
    global: { stubs: { RouterLink: RouterLinkStub } },
  })
}

describe('DashboardView - alerta de hallazgos asignados', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    listarHallazgosMock.mockReset()
  })

  it('muestra los hallazgos nuevos asignados al responsable', async () => {
    autenticar('Responsable de Manufactura')
    listarHallazgosMock.mockResolvedValue([hallazgo(1), hallazgo(2)])

    const wrapper = montar()
    await flushPromises()

    expect(listarHallazgosMock).toHaveBeenCalledWith({
      solo_asignados: true,
      estado: 'abierto',
    })
    expect(wrapper.find('.alerta-hallazgos').exists()).toBe(true)
    expect(wrapper.text()).toContain('Tienes 2 hallazgos por atender')
    expect(wrapper.text()).toContain(
      'Se te asignaron nuevos hallazgos que requieren acción correctiva',
    )
    expect(wrapper.findAll('.alerta-item')).toHaveLength(2)
    expect(wrapper.findComponent(RouterLinkStub).props('to')).toBe(
      '/hallazgos-asignados',
    )
  })

  it('no consulta ni muestra la alerta para otros roles', async () => {
    autenticar('Auditor')

    const wrapper = montar()
    await flushPromises()

    expect(listarHallazgosMock).not.toHaveBeenCalled()
    expect(wrapper.find('.alerta-hallazgos').exists()).toBe(false)
  })

  it('muestra el estado al día cuando no hay hallazgos abiertos', async () => {
    autenticar('Responsable de Manufactura')
    listarHallazgosMock.mockResolvedValue([])

    const wrapper = montar()
    await flushPromises()

    expect(wrapper.find('.alerta-hallazgos').exists()).toBe(true)
    expect(wrapper.text()).toContain('No tienes hallazgos nuevos por atender')
    expect(wrapper.findAll('.alerta-item')).toHaveLength(0)
  })
})
