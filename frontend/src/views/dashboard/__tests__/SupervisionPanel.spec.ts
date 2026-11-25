import { describe, it, expect, beforeEach, vi } from 'vitest'
import { flushPromises, mount, RouterLinkStub } from '@vue/test-utils'
import type {
  EjecucionAuditoriaListItem,
  PendienteItem,
} from '@/types/ejecucion'
import type { HallazgoDetallado } from '@/types/hallazgo'

const { push, listarPendientes, listarEjecuciones, iniciarPendiente, listarHallazgos } =
  vi.hoisted(() => ({
    push: vi.fn(),
    listarPendientes: vi.fn(),
    listarEjecuciones: vi.fn(),
    iniciarPendiente: vi.fn(),
    listarHallazgos: vi.fn(),
  }))

vi.mock('vue-router', () => ({
  useRouter: () => ({ push }),
}))

vi.mock('@/services/ejecucion.service', () => ({
  listarPendientes,
  listarEjecuciones,
  iniciarPendiente,
}))

vi.mock('@/services/hallazgo.service', () => ({
  listarHallazgos,
}))

import SupervisionPanel from '@/components/SupervisionPanel.vue'

function pendiente(
  id: number,
  cambios: Partial<PendienteItem> = {},
): PendienteItem {
  return {
    ejecucion_id: id,
    auditoria_id: 1,
    auditoria_nombre: 'Auditoría Supervisor - Ensamble Final',
    area_nombre: 'Ensamble Final',
    celula_numero: null,
    estado: 'atrasada',
    fecha_habilita: '2026-11-16T10:00:00+00:00',
    contador: 'Atrasada hace 2 días',
    dias: 2,
    accion: 'iniciar',
    tooltip: null,
    requiere_celula: false,
    ...cambios,
  }
}

function ejecucion(
  id: number,
  cambios: Partial<EjecucionAuditoriaListItem> = {},
): EjecucionAuditoriaListItem {
  return {
    id,
    fecha: '2026-11-17T10:00:00+00:00',
    estado: 'finalizada',
    auditoria_id: 1,
    auditoria_nombre: 'Auditoría de Proceso - Ensamble Final',
    usuario_id: 2,
    usuario_nombre: 'Luis Auditor',
    celula_id: 1,
    celula_numero: 6,
    area_id: 1,
    area_nombre: 'Ensamble Final',
    tipo_respuesta: 'semaforo',
    fecha_programada: null,
    fecha_limite: null,
    programada: true,
    vencida: false,
    resumen: {
      total_criterios: 15,
      total_v: 10,
      total_a: 3,
      total_r: 2,
    },
    ...cambios,
  }
}

function hallazgo(
  id: number,
  cambios: Partial<HallazgoDetallado> = {},
): HallazgoDetallado {
  return {
    id,
    descripcion: `Hallazgo ${id}`,
    fecha_creacion: '2026-11-10T10:00:00+00:00',
    respuesta_id: 100 + id,
    estado: 'abierto',
    accion_correctiva: null,
    area_responsable_id: 1,
    area_responsable_nombre: 'Ensamble Final',
    fecha_cierre: null,
    fecha_limite: '2026-11-15T10:00:00+00:00',
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
  return mount(SupervisionPanel, {
    global: { stubs: { RouterLink: RouterLinkStub } },
  })
}

describe('SupervisionPanel', () => {
  beforeEach(() => {
    push.mockReset()
    listarPendientes.mockReset()
    listarEjecuciones.mockReset()
    iniciarPendiente.mockReset()
    listarHallazgos.mockReset()

    listarPendientes.mockResolvedValue([
      pendiente(10),
      pendiente(11, {
        estado: 'en_progreso',
        contador: 'En progreso',
        accion: 'continuar',
      }),
    ])
    listarEjecuciones.mockResolvedValue([ejecucion(5)])
    listarHallazgos.mockResolvedValue([
      hallazgo(1, { atrasado: true }),
      hallazgo(2, { estado: 'cierre_solicitado' }),
      hallazgo(3, { reincidente: true }),
      hallazgo(4, { estado: 'cerrado' }),
    ])
    iniciarPendiente.mockResolvedValue({ id: 10 })
  })

  it('muestra auditorías propias, ejecuciones y señales de calidad', async () => {
    const wrapper = montar()
    await flushPromises()

    expect(wrapper.text()).toContain('Mis auditorías')
    expect(wrapper.text()).toContain('Auditoría Supervisor - Ensamble Final')
    expect(wrapper.text()).toContain('Ejecuciones de auditores')
    expect(wrapper.text()).toContain('Luis Auditor')
    expect(wrapper.text()).toContain('Finalizada')
    expect(wrapper.text()).toContain('Señales de calidad')
    expect(wrapper.findAll('.signal-count').map((n) => n.text())).toEqual([
      '3',
      '1',
      '1',
      '1',
    ])
    expect(wrapper.findAll('.priority-link')).toHaveLength(2)
    expect(listarEjecuciones).toHaveBeenCalledWith({
      solo_auditores: true,
      tipo_respuesta: 'semaforo',
      limit: 20,
    })
  })

  it('inicia una auditoría y navega a su ejecución', async () => {
    const wrapper = montar()
    await flushPromises()

    await wrapper.find('.audit-action').trigger('click')
    await flushPromises()

    expect(iniciarPendiente).toHaveBeenCalledWith(10)
    expect(push).toHaveBeenCalledWith({
      name: 'ejecutar',
      query: { id: '10' },
    })
  })

  it('muestra estados vacíos cuando no hay datos', async () => {
    listarPendientes.mockResolvedValue([])
    listarEjecuciones.mockResolvedValue([])
    listarHallazgos.mockResolvedValue([])

    const wrapper = montar()
    await flushPromises()

    expect(wrapper.text()).toContain('No tienes auditorías pendientes')
    expect(wrapper.text()).toContain('Sin ejecuciones de auditores')
    expect(wrapper.text()).toContain('Sin hallazgos que requieran atención')
  })

  it('muestra un error cuando fallan las tres cargas', async () => {
    listarPendientes.mockRejectedValue(new Error('fallo'))
    listarEjecuciones.mockRejectedValue(new Error('fallo'))
    listarHallazgos.mockRejectedValue(new Error('fallo'))

    const wrapper = montar()
    await flushPromises()

    expect(wrapper.find('.panel-alert').text()).toContain(
      'No se pudo cargar el panel de supervisión',
    )
  })
})
