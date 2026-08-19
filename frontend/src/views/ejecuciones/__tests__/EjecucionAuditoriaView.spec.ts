import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { createRouter, createMemoryHistory } from 'vue-router'

vi.mock('@/services/ejecucion.service', () => ({
  obtenerAuditoriasDisponibles: vi.fn().mockResolvedValue([
    { id: 1, nombre: 'Ensamble Final', area_nombre: 'Ensamble', capa_nombre: 'C1' },
  ]),
  obtenerCelulasDisponibles: vi.fn().mockResolvedValue([
    { id: 1, numero: 1, activa: true, area_id: 1 },
  ]),
  iniciarEjecucion: vi.fn().mockResolvedValue({
    id: 10,
    fecha: '2026-08-13T10:00:00',
    observaciones: null,
    estado: 'en_proceso',
    auditoria_id: 1,
    usuario_id: 1,
    celula_id: 1,
    auditoria_nombre: 'Ensamble Final',
    area_nombre: 'Ensamble',
    celula_numero: 1,
    auditor_nombre: 'Auditor 1',
    criterios: [],
  }),
  guardarRespuestas: vi.fn().mockImplementation(async (_id, payload) => {
    const criterios = payload.respuestas.map((r) => ({
      id: r.criterio_id,
      descripcion: 'c' + r.criterio_id,
      orden: r.criterio_id,
      respuesta_valor: r.valor,
      respuesta_observaciones: r.observaciones,
      respuesta_id: 100 + r.criterio_id,
      hallazgo_id: null,
      hallazgo_descripcion: null,
    }))
    return {
      id: 10,
      fecha: '2026-08-13T10:00:00',
      observaciones: null,
      estado: 'en_proceso',
      auditoria_id: 1,
      usuario_id: 1,
      celula_id: 1,
      auditoria_nombre: 'Ensamble Final',
      area_nombre: 'Ensamble',
      celula_numero: 1,
      auditor_nombre: 'Auditor 1',
      criterios,
    }
  }),
  obtenerEjecucion: vi.fn(),
  finalizarEjecucion: vi.fn(),
}))

const crearHallazgoMock = vi.fn().mockImplementation(async (respuestaId, payload) => ({
  id: 999,
  descripcion: payload.descripcion,
  fecha_creacion: '2026-08-13T10:00:00',
  respuesta_id: respuestaId,
  tipo: 'A',
  respuesta_valor: 'A',
  criterio_id: 1,
  criterio_descripcion: 'c1',
  criterio_orden: 1,
  ejecucion_id: 10,
  ejecucion_estado: 'en_proceso',
  auditoria_id: 1,
  auditoria_nombre: 'Ensamble Final',
  celula_id: 1,
  celula_numero: 1,
}))

const actualizarHallazgoMock = vi.fn()
const eliminarHallazgoMock = vi.fn()

vi.mock('@/services/hallazgo.service', () => ({
  crearHallazgo: (...args) => crearHallazgoMock(...args),
  actualizarHallazgo: (...args) => actualizarHallazgoMock(...args),
  eliminarHallazgo: (...args) => eliminarHallazgoMock(...args),
  obtenerHallazgo: vi.fn(),
  listarHallazgosDeEjecucion: vi.fn().mockResolvedValue([]),
}))

import EjecucionAuditoriaView from '../EjecucionAuditoriaView.vue'

function makeRouter() {
  return createRouter({
    history: createMemoryHistory(),
    routes: [
      { path: '/', name: 'dashboard', component: { template: '<div/>' } },
    ],
  })
}

const baseEjecucion = () => ({
  id: 10,
  fecha: '2026-08-13T10:00:00',
  observaciones: null,
  estado: 'en_proceso',
  auditoria_id: 1,
  usuario_id: 1,
  celula_id: 1,
  auditoria_nombre: 'Ensamble Final',
  area_nombre: 'Ensamble',
  celula_numero: 1,
  auditor_nombre: 'Auditor 1',
  criterios: [
    {
      id: 1,
      descripcion: 'Criterio 1',
      orden: 1,
      respuesta_valor: null,
      respuesta_observaciones: null,
      respuesta_id: null,
      hallazgo_id: null,
      hallazgo_descripcion: null,
    },
  ],
})

describe('EjecucionAuditoriaView - hallazgos flow', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    crearHallazgoMock.mockClear()
    actualizarHallazgoMock.mockClear()
    eliminarHallazgoMock.mockClear()
  })

  it('al pulsar "Registrar hallazgo" sin respuesta_id, primero persiste la respuesta y luego crea el hallazgo', async () => {
    const { guardarRespuestas } = await import('@/services/ejecucion.service')
    const router = makeRouter()
    await router.push('/')
    await router.isReady()

    const wrapper = mount(EjecucionAuditoriaView, {
      global: { plugins: [router] },
    })
    await flushPromises()

    wrapper.vm.ejecucion = baseEjecucion()
    wrapper.vm.paso = 'ejecutando'
    await flushPromises()

    const crit = wrapper.vm.ejecucion.criterios[0]
    crit.respuesta_valor = 'A'
    wrapper.vm.hallazgosInputs[crit.id] = 'Falta de EPP'

    await wrapper.vm.guardarHallazgo(crit)
    await flushPromises()

    expect(guardarRespuestas).toHaveBeenCalledTimes(1)
    const payload = (guardarRespuestas as ReturnType<typeof vi.fn>).mock.calls[0][1]
    expect(payload.respuestas).toEqual([
      expect.objectContaining({ criterio_id: 1, valor: 'A' }),
    ])
    expect(crearHallazgoMock).toHaveBeenCalledTimes(1)
    expect(crearHallazgoMock).toHaveBeenCalledWith(
      expect.any(Number),
      expect.objectContaining({ descripcion: 'Falta de EPP' }),
    )
    const critActualizado = wrapper.vm.ejecucion.criterios[0]
    expect(critActualizado.hallazgo_id).toBe(999)
    expect(critActualizado.hallazgo_descripcion).toBe('Falta de EPP')
  })

  it('preserva los borradores locales tras guardar respuestas si el servidor aún no devolvio hallazgo_descripcion', async () => {
    const router = makeRouter()
    await router.push('/')
    await router.isReady()

    const wrapper = mount(EjecucionAuditoriaView, {
      global: { plugins: [router] },
    })
    await flushPromises()

    wrapper.vm.ejecucion = baseEjecucion()
    wrapper.vm.paso = 'ejecutando'
    wrapper.vm.hallazgosInputs[1] = 'Borrador aun sin guardar'
    await flushPromises()

    await wrapper.vm.guardar()
    await flushPromises()

    expect(wrapper.vm.hallazgosInputs[1]).toBe('Borrador aun sin guardar')
  })

  it('muestra el badge "Hallazgo pendiente" cuando hay A/R sin hallazgo guardado', async () => {
    const router = makeRouter()
    await router.push('/')
    await router.isReady()

    const wrapper = mount(EjecucionAuditoriaView, {
      global: { plugins: [router] },
    })
    await flushPromises()

    wrapper.vm.ejecucion = baseEjecucion()
    wrapper.vm.paso = 'ejecutando'
    const crit = wrapper.vm.ejecucion.criterios[0]
    crit.respuesta_valor = 'R'
    await flushPromises()

    expect(wrapper.find('.badge-pendiente').exists()).toBe(true)
    expect(wrapper.find('.badge-pendiente').text()).toBe('Hallazgo pendiente')
    expect(wrapper.find('.badge-pendiente').classes()).toContain('badge-rojo')
  })

  it('oculta el badge cuando ya hay un hallazgo guardado', async () => {
    const router = makeRouter()
    await router.push('/')
    await router.isReady()

    const wrapper = mount(EjecucionAuditoriaView, {
      global: { plugins: [router] },
    })
    await flushPromises()

    wrapper.vm.ejecucion = baseEjecucion()
    wrapper.vm.paso = 'ejecutando'
    const crit = wrapper.vm.ejecucion.criterios[0]
    crit.respuesta_valor = 'A'
    crit.hallazgo_id = 5
    crit.hallazgo_descripcion = 'ya guardado'
    await flushPromises()

    expect(wrapper.find('.badge-pendiente').exists()).toBe(false)
  })
})