import api from '@/api/api'
import type {
  HallazgoCreate,
  HallazgoDetallado,
  HallazgoUpdate,
} from '@/types/hallazgo'

export function crearHallazgo(
  respuestaId: number,
  datos: HallazgoCreate,
): Promise<HallazgoDetallado> {
  return api
    .post<HallazgoDetallado>(
      `/respuestas/${respuestaId}/hallazgo`,
      datos,
    )
    .then((res) => res.data)
}

export function obtenerHallazgo(hallazgoId: number): Promise<HallazgoDetallado> {
  return api
    .get<HallazgoDetallado>(`/hallazgos/${hallazgoId}`)
    .then((res) => res.data)
}

export function actualizarHallazgo(
  hallazgoId: number,
  datos: HallazgoUpdate,
): Promise<HallazgoDetallado> {
  return api
    .put<HallazgoDetallado>(`/hallazgos/${hallazgoId}`, datos)
    .then((res) => res.data)
}

export function eliminarHallazgo(hallazgoId: number): Promise<void> {
  return api.delete(`/hallazgos/${hallazgoId}`).then(() => undefined)
}

export function listarHallazgosDeEjecucion(
  ejecucionId: number,
): Promise<HallazgoDetallado[]> {
  return api
    .get<HallazgoDetallado[]>(
      `/ejecuciones-auditoria/ejecuciones-auditoria/${ejecucionId}/hallazgos`,
    )
    .then((res) => res.data)
}