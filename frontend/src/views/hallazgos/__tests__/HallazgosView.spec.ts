import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { useAuthStore } from '@/stores/auth'

const hallazgoBase = {
  id: 1,
  descripcion: 'Falta de EPP',
  fecha_creacion: '2026-10-05T10:00:00+00:00',
  respuesta_id: 100,
  estado: 'abierto',
  accion_correctiva: null,
  area_responsable_id: 1,
  area_responsable_nombre: 'Pulido',
  fecha_cierre: null,
  tipo: 'A',
  respuesta_valor: 'A',
  criterio_id: 1,
  criterio_descripcion: 'Criterio uno',
  criterio_orden: 1,
  ejecucion_id: 10,
  ejecucion_estado: 'finalizada',
  auditoria_id: 1,
  auditoria_nombre: 'Auditoría de Proceso - Pulido',
  auditor_id: 1,
  celula_id: null,
  celula_numero: null,
}

const listarHallazgosMock = vi.fn().mockResolvedValue([hallazgoBase])
const actualizarSeguimientoMock = vi.fn().mockResolvedValue({
  ...hallazgoBase,
  estado: 'cerrado',
  fecha_cierre: '2026-10-05T12:00:00+00:00',
})

vi.mock('@/services/hallazgo.service', () => ({
  listarHallazgos: (...args) => listarHallazgosMock(...args),
  actualizarSeguimiento: (...args) => actualizarSeguimientoMock(...args),
}))

vi.mock('@/services/area.service', () => ({
  obtenerAreasActivas: vi.fn().mockResolvedValue([
    { id: 1, nombre: 'Pulido', descripcion: null, activa: true },
  ]),
}))

import HallazgosView from '../HallazgosView.vue'

function autenticar(usuarioId: number) {
  const auth = useAuthStore()
  auth.usuario = {
    id: usuarioId,
    nombre: 'Usuario',
    correo: 'u@lpa.com',
    activo: true,
    rol_id: 1,
    rol_nombre: usuarioId === 1 ? 'Auditor' : 'Supervisor',
  }
}

describe('HallazgosView', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    listarHallazgosMock.mockClear()
    actualizarSeguimientoMock.mockClear()
  })

  it('lista los hallazgos con su estado y área responsable', async () => {
    autenticar(2)
    const wrapper = mount(HallazgosView)
    await flushPromises()

    expect(listarHallazgosMock).toHaveBeenCalledTimes(1)
    const filas = wrapper.findAll('tbody .row')
    expect(filas.length).toBe(1)
    expect(filas[0].text()).toContain('Falta de EPP')
    expect(filas[0].text()).toContain('Pulido')
    expect(filas[0].text()).toContain('Abierto')
  })

  it('el auditor dueño puede cerrar el hallazgo desde el modal', async () => {
    autenticar(1)
    const wrapper = mount(HallazgosView)
    await flushPromises()

    await wrapper.find('tbody .row').trigger('click')
    await flushPromises()

    expect(wrapper.find('.seguimiento-form').exists()).toBe(true)
    const selects = wrapper.findAll('.seguimiento-form select')
    await selects[0].setValue('cerrado')
    await wrapper.find('.modal-footer .btn-primary').trigger('click')
    await flushPromises()

    expect(actualizarSeguimientoMock).toHaveBeenCalledWith(
      1,
      expect.objectContaining({ estado: 'cerrado' }),
    )
    expect(wrapper.text()).toContain('Seguimiento guardado correctamente')
  })

  it('un supervisor solo visualiza: no muestra formulario de edición', async () => {
    autenticar(2)
    const wrapper = mount(HallazgosView)
    await flushPromises()

    await wrapper.find('tbody .row').trigger('click')
    await flushPromises()

    expect(wrapper.find('.seguimiento-form').exists()).toBe(false)
    expect(wrapper.find('.aviso-lectura').exists()).toBe(true)
    expect(wrapper.text()).toContain('Falta de EPP')
  })
})
