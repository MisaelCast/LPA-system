import api from '@/api/api'
import type {
  AsignarResponsableRequest,
  AvanceTicketRequest,
  CierreResolucionRequest,
  CierreSolicitudRequest,
  Evidencia,
  HallazgoCreate,
  HallazgoDetallado,
  HallazgoFiltros,
  HallazgoSeguimientoUpdate,
  HallazgoUpdate,
  ResponsableResumen,
  Seguimiento,
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

export function listarHallazgos(
  filtros: HallazgoFiltros = {},
): Promise<HallazgoDetallado[]> {
  return api
    .get<HallazgoDetallado[]>('/hallazgos', { params: filtros })
    .then((res) => res.data)
}

export function obtenerHallazgo(hallazgoId: number): Promise<HallazgoDetallado> {
  return api
    .get<HallazgoDetallado>(`/hallazgos/${hallazgoId}`)
    .then((res) => res.data)
}

export function actualizarSeguimiento(
  hallazgoId: number,
  datos: HallazgoSeguimientoUpdate,
): Promise<HallazgoDetallado> {
  return api
    .patch<HallazgoDetallado>(`/hallazgos/${hallazgoId}/seguimiento`, datos)
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

export function subirEvidencia(
  hallazgoId: number,
  archivo: File,
  tipo: 'original' | 'correccion' = 'original',
): Promise<Evidencia> {
  const formData = new FormData()
  formData.append('archivo', archivo)
  formData.append('tipo', tipo)
  return api
    .post<Evidencia>(`/hallazgos/${hallazgoId}/evidencias`, formData)
    .then((res) => res.data)
}

export function listarEvidencias(hallazgoId: number): Promise<Evidencia[]> {
  return api
    .get<Evidencia[]>(`/hallazgos/${hallazgoId}/evidencias`)
    .then((res) => res.data)
}

export function eliminarEvidencia(evidenciaId: number): Promise<void> {
  return api.delete(`/evidencias/${evidenciaId}`).then(() => undefined)
}

export function listarResponsables(
  hallazgoId: number,
): Promise<ResponsableResumen[]> {
  return api
    .get<ResponsableResumen[]>(`/hallazgos/${hallazgoId}/responsables`)
    .then((res) => res.data)
}

export function asignarResponsable(
  hallazgoId: number,
  datos: AsignarResponsableRequest,
): Promise<HallazgoDetallado> {
  return api
    .put<HallazgoDetallado>(`/hallazgos/${hallazgoId}/responsable`, datos)
    .then((res) => res.data)
}

export function registrarAvance(
  hallazgoId: number,
  datos: AvanceTicketRequest,
): Promise<HallazgoDetallado> {
  return api
    .post<HallazgoDetallado>(`/hallazgos/${hallazgoId}/avance`, datos)
    .then((res) => res.data)
}

export function solicitarCierre(
  hallazgoId: number,
  datos: CierreSolicitudRequest,
): Promise<HallazgoDetallado> {
  return api
    .post<HallazgoDetallado>(`/hallazgos/${hallazgoId}/solicitar-cierre`, datos)
    .then((res) => res.data)
}

export function resolverCierre(
  hallazgoId: number,
  datos: CierreResolucionRequest,
): Promise<HallazgoDetallado> {
  return api
    .post<HallazgoDetallado>(`/hallazgos/${hallazgoId}/resolver-cierre`, datos)
    .then((res) => res.data)
}

export function listarHistorial(hallazgoId: number): Promise<Seguimiento[]> {
  return api
    .get<Seguimiento[]>(`/hallazgos/${hallazgoId}/historial`)
    .then((res) => res.data)
}
