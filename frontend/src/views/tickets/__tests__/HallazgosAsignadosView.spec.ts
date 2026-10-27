import { describe, it, expect, beforeEach, vi } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
import type { HallazgoDetallado } from '@/types/hallazgo'

const listarHallazgosMock = vi.fn()
const listarHistorialMock = vi.fn().mockResolvedValue([])

vi.mock('@/services/hallazgo.service', () => ({
  listarHallazgos: (...args: unknown[]) => listarHallazgosMock(...args),
  listarHistorial: (...args: unknown[]) => listarHistorialMock(...args),
  registrarAvance: vi.fn(),
  solicitarCierre: vi.fn(),
  subirEvidencia: vi.fn(),
}))

import HallazgosAsignadosView from '../HallazgosAsignadosView.vue'

function hallazgo(
  id: number,
  cambios: Partial<HallazgoDetallado> = {},
): HallazgoDetallado {
  return {
    id,
    descripcion: `Hallazgo ${id}`,
    fecha_creacion: '2026-10-20T10:00:00+00:00',
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
    criterio_descripcion: 'Criterio de prueba',
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
    responsable_nombre: 'Responsable Prueba',
    atrasado: false,
    dias_sin_actualizar: 0,
    reincidente: false,
    ...cambios,
  }
}

async function montar(hallazgos: HallazgoDetallado[]) {
  listarHallazgosMock.mockResolvedValue(hallazgos)
  const wrapper = mount(HallazgosAsignadosView)
  await flushPromises()
  return wrapper
}

describe('HallazgosAsignadosView', () => {
  beforeEach(() => {
    listarHallazgosMock.mockReset()
    listarHistorialMock.mockClear()
  })

  it('muestra solo los pendientes por defecto y prioriza los vencidos', async () => {
    const wrapper = await montar([
      hallazgo(1, {
        descripcion: 'Pendiente normal',
        fecha_limite: '2026-11-05T10:00:00+00:00',
      }),
      hallazgo(2, {
        descripcion: 'Pendiente vencido',
        atrasado: true,
        fecha_limite: '2026-10-20T10:00:00+00:00',
      }),
      hallazgo(3, {
        descripcion: 'Hallazgo cerrado',
        estado: 'cerrado',
        fecha_cierre: '2026-10-21T10:00:00+00:00',
      }),
    ])

    expect(listarHallazgosMock).toHaveBeenCalledWith({ solo_asignados: true })

    const tickets = wrapper.findAll('.ticket')
    expect(tickets).toHaveLength(2)
    expect(tickets[0].text()).toContain('Pendiente vencido')
    expect(wrapper.text()).not.toContain('Hallazgo cerrado')
    expect(wrapper.find('.vista--activa').text()).toContain('Pendientes')
  })

  it('cambia al historial para consultar los cerrados', async () => {
    const wrapper = await montar([
      hallazgo(1, { descripcion: 'Pendiente normal' }),
      hallazgo(2, {
        descripcion: 'Hallazgo cerrado',
        estado: 'cerrado',
        fecha_cierre: '2026-10-21T10:00:00+00:00',
      }),
    ])

    await wrapper.findAll('.vista')[1]!.trigger('click')

    const tickets = wrapper.findAll('.ticket')
    expect(tickets).toHaveLength(1)
    expect(tickets[0]!.text()).toContain('Hallazgo cerrado')
  })

  it('abre el detalle con la descripción como título', async () => {
    const wrapper = await montar([
      hallazgo(1, { descripcion: 'Falta de EPP en la estación' }),
    ])

    await wrapper.find('.ticket').trigger('click')
    await flushPromises()

    expect(wrapper.find('.detalle-header h2').text()).toBe(
      'Falta de EPP en la estación',
    )
    expect(listarHistorialMock).toHaveBeenCalledWith(1)
  })
})
