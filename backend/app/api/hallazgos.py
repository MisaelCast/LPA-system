"""Endpoints para la gestion de hallazgos."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import Session

from app.auth.dependencies import get_current_active_user
from app.db.database import get_session
from app.models.usuario import Usuario
from app.schemas.hallazgo import (
    AvanceTicketRequest,
    CierreResolucionRequest,
    CierreSolicitudRequest,
    HallazgoCreate,
    HallazgoCreateRequest,
    HallazgoDetallado,
    HallazgoSeguimientoUpdate,
    HallazgoUpdate,
    ResponsableAsignarRequest,
    ResponsableResumen,
    SeguimientoRead,
)
from app.services.hallazgo_service import HallazgoService

router = APIRouter(tags=["hallazgos"])


def _a_http_error(error: ValueError) -> HTTPException:
    mensaje = str(error).lower()
    if "no encontrad" in mensaje:
        return HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        )
    if "permiso" in mensaje:
        return HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(error),
        )
    if (
        "ya existe" in mensaje
        or "finalizada" in mensaje
        or "valor" in mensaje
        or "estado invalido" in mensaje
        or "inactiva" in mensaje
    ):
        return HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(error),
        )
    return HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=str(error),
    )


@router.get(
    "/hallazgos",
    response_model=list[HallazgoDetallado],
)
def listar_hallazgos(
    estado: str | None = Query(default=None),
    area_responsable_id: int | None = Query(default=None),
    solo_propios: bool = Query(default=False),
    solo_auditores: bool = Query(default=False),
    solo_asignados: bool = Query(default=False),
    atrasados: bool = Query(default=False),
    sin_actualizar: bool = Query(default=False),
    cierre_pendiente: bool = Query(default=False),
    reincidencia: bool = Query(default=False),
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_active_user),
):
    """Lista hallazgos con filtros opcionales.

    ``solo_propios`` devuelve solo los hallazgos del usuario autenticado;
    ``solo_auditores`` los de la capa inferior (auditores);
    ``solo_asignados`` los tickets asignados al usuario como responsable.
    ``atrasados`` / ``sin_actualizar`` / ``cierre_pendiente`` / ``reincidencia``
    son filtros de seguimiento para supervisión.
    """
    service = HallazgoService(session)
    try:
        return service.listar(
            usuario,
            estado=estado,
            area_responsable_id=area_responsable_id,
            solo_propios=solo_propios,
            solo_auditores=solo_auditores,
            solo_asignados=solo_asignados,
            atrasados=atrasados,
            sin_actualizar=sin_actualizar,
            cierre_pendiente=cierre_pendiente,
            reincidencia=reincidencia,
        )
    except ValueError as error:
        raise _a_http_error(error)


@router.post(
    "/respuestas/{respuesta_id}/hallazgo",
    response_model=HallazgoDetallado,
    status_code=status.HTTP_201_CREATED,
)
def crear_hallazgo(
    respuesta_id: int,
    datos: HallazgoCreateRequest,
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_active_user),
):
    """Crea un hallazgo asociado a una respuesta con valor ``A`` o ``R``.

    El ``respuesta_id`` proviene del path; el body requiere ``descripcion`` y
    acepta ``area_responsable_id`` (opcional, se hereda del área de la
    auditoría) y ``responsable_id`` para asignar de inmediato al Responsable
    de Manufactura que atenderá el hallazgo.
    """
    payload = HallazgoCreate(
        descripcion=datos.descripcion,
        respuesta_id=respuesta_id,
        area_responsable_id=datos.area_responsable_id,
        responsable_id=datos.responsable_id,
    )
    service = HallazgoService(session)
    try:
        return service.crear(payload, usuario)
    except ValueError as error:
        raise _a_http_error(error)


@router.get(
    "/hallazgos/{hallazgo_id}",
    response_model=HallazgoDetallado,
)
def obtener_hallazgo(
    hallazgo_id: int,
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_active_user),
):
    """Obtiene un hallazgo con su contexto de ejecucion, auditoria, celula y criterio."""
    service = HallazgoService(session)
    try:
        return service.obtener_por_id(hallazgo_id)
    except ValueError as error:
        raise _a_http_error(error)


@router.patch(
    "/hallazgos/{hallazgo_id}/seguimiento",
    response_model=HallazgoDetallado,
)
def actualizar_seguimiento_hallazgo(
    hallazgo_id: int,
    datos: HallazgoSeguimientoUpdate,
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_active_user),
):
    """Actualiza estado, accion correctiva y area responsable del hallazgo.

    Permitido al auditor dueño del hallazgo y a Supervisor/Gerente/Administrador.
    """
    service = HallazgoService(session)
    try:
        return service.actualizar_seguimiento(hallazgo_id, datos, usuario)
    except ValueError as error:
        raise _a_http_error(error)


@router.put(
    "/hallazgos/{hallazgo_id}",
    response_model=HallazgoDetallado,
)
def actualizar_hallazgo(
    hallazgo_id: int,
    datos: HallazgoUpdate,
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_active_user),
):
    """Actualiza la descripcion de un hallazgo mientras la ejecucion no este finalizada."""
    service = HallazgoService(session)
    try:
        return service.actualizar(hallazgo_id, datos, usuario)
    except ValueError as error:
        raise _a_http_error(error)


@router.delete(
    "/hallazgos/{hallazgo_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def eliminar_hallazgo(
    hallazgo_id: int,
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_active_user),
):
    """Elimina un hallazgo de forma controlada mientras la ejecucion este en proceso."""
    service = HallazgoService(session)
    try:
        service.eliminar(hallazgo_id, usuario)
    except ValueError as error:
        raise _a_http_error(error)
    return None


@router.put(
    "/hallazgos/{hallazgo_id}/responsable",
    response_model=HallazgoDetallado,
)
def asignar_responsable(
    hallazgo_id: int,
    datos: ResponsableAsignarRequest,
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_active_user),
):
    """Asigna o reasigna el Responsable de Manufactura (solo auditor dueño)."""
    service = HallazgoService(session)
    try:
        return service.asignar_responsable(
            hallazgo_id, datos.responsable_id, datos.fecha_limite, usuario
        )
    except ValueError as error:
        raise _a_http_error(error)


@router.get(
    "/hallazgos/{hallazgo_id}/responsables",
    response_model=list[ResponsableResumen],
)
def responsables_del_area(
    hallazgo_id: int,
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_active_user),
):
    """Lista los Responsables de Manufactura del área del hallazgo."""
    service = HallazgoService(session)
    try:
        return service.responsables_del_area(hallazgo_id, usuario)
    except ValueError as error:
        raise _a_http_error(error)


@router.post(
    "/hallazgos/{hallazgo_id}/avance",
    response_model=HallazgoDetallado,
)
def registrar_avance(
    hallazgo_id: int,
    datos: AvanceTicketRequest,
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_active_user),
):
    """El responsable registra acción correctiva y/o comentario."""
    service = HallazgoService(session)
    try:
        return service.registrar_avance(
            hallazgo_id,
            datos.accion_correctiva,
            datos.comentario,
            usuario,
        )
    except ValueError as error:
        raise _a_http_error(error)


@router.post(
    "/hallazgos/{hallazgo_id}/solicitar-cierre",
    response_model=HallazgoDetallado,
)
def solicitar_cierre(
    hallazgo_id: int,
    datos: CierreSolicitudRequest,
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_active_user),
):
    """El responsable solicita el cierre del ticket."""
    service = HallazgoService(session)
    try:
        return service.solicitar_cierre(hallazgo_id, datos.comentario, usuario)
    except ValueError as error:
        raise _a_http_error(error)


@router.post(
    "/hallazgos/{hallazgo_id}/resolver-cierre",
    response_model=HallazgoDetallado,
)
def resolver_cierre(
    hallazgo_id: int,
    datos: CierreResolucionRequest,
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_active_user),
):
    """El auditor aprueba o rechaza la solicitud de cierre."""
    service = HallazgoService(session)
    try:
        return service.resolver_cierre(
            hallazgo_id, datos.aprobar, datos.observacion, usuario
        )
    except ValueError as error:
        raise _a_http_error(error)


@router.get(
    "/hallazgos/{hallazgo_id}/historial",
    response_model=list[SeguimientoRead],
)
def historial_hallazgo(
    hallazgo_id: int,
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_active_user),
):
    """Devuelve el historial de seguimiento (trazabilidad) del hallazgo."""
    service = HallazgoService(session)
    try:
        return service.historial(hallazgo_id, usuario)
    except ValueError as error:
        raise _a_http_error(error)
