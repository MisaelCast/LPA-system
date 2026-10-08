"""Endpoints para la ejecucion de auditorias."""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import Session

from app.auth.dependencies import get_current_active_user
from app.auth.permissions import require_roles
from app.db.database import get_session
from app.models.usuario import Usuario
from app.schemas.auditoria import AuditoriaRead
from app.schemas.celula import CelulaRead
from app.schemas.ejecucion_auditoria import (
    EjecucionAuditoriaDetalle,
    EjecucionAuditoriaListItem,
    EjecucionAuditoriaRead,
    GuardarRespuestasRequest,
    IniciarEjecucionRequest,
    OpcionesFiltrosRevision,
    PendienteItem,
)
from app.schemas.hallazgo import HallazgoDetallado
from app.services.ejecucion_auditoria_service import (
    DiaNoHabilitadoError,
    EjecucionAbiertaError,
    EjecucionAuditoriaService,
)
from app.services.hallazgo_service import HallazgoService

router = APIRouter(
    prefix="/ejecuciones-auditoria",
    tags=["ejecuciones-auditoria"],
)


@router.get("", response_model=list[EjecucionAuditoriaListItem])
def listar_ejecuciones(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=1000),
    auditoria_id: int | None = Query(default=None),
    celula_id: int | None = Query(default=None),
    usuario_id: int | None = Query(default=None),
    estado: str | None = Query(default=None),
    fecha_desde: datetime | None = Query(default=None),
    fecha_hasta: datetime | None = Query(default=None),
    area_id: int | None = Query(default=None),
    tipo_respuesta: str | None = Query(default=None),
    solo_auditores: bool = Query(default=False),
    solo_propias: bool = Query(default=False),
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_active_user),
):
    """Lista el historial de ejecuciones de auditoria, mas recientes primero."""
    service = EjecucionAuditoriaService(session)
    return service.listar_ejecuciones(
        usuario,
        skip=skip,
        limit=limit,
        auditoria_id=auditoria_id,
        celula_id=celula_id,
        usuario_id=usuario_id,
        estado=estado,
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
        area_id=area_id,
        tipo_respuesta=tipo_respuesta,
        solo_auditores=solo_auditores,
        solo_propias=solo_propias,
    )


@router.get("/filtros", response_model=OpcionesFiltrosRevision)
def opciones_filtros_revision(
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(require_roles("Supervisor", "Gerente", "Administrador")),
):
    """Devuelve las opciones de filtro (áreas, células y auditores).

    Solo accesible por usuarios con rol **Supervisor**, **Gerente** o
    **Administrador**. Para Supervisores y Gerentes, las áreas se limitan a las
    asignadas.
    """
    service = EjecucionAuditoriaService(session)
    return service.obtener_opciones_filtros(usuario)


@router.get("/disponibles", response_model=list[AuditoriaRead])
def listar_auditorias_disponibles(
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_active_user),
) -> list:
    """Lista las auditorias activas disponibles para ser ejecutadas."""
    service = EjecucionAuditoriaService(session)
    return service.listar_disponibles(usuario)


@router.get(
    "/auditorias/{auditoria_id}/celulas",
    response_model=list[CelulaRead],
)
def listar_celulas_disponibles(
    auditoria_id: int,
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_active_user),
) -> list:
    """Devuelve las celulas del area de una auditoria especifica.

    Si el usuario tiene células a cargo, se limita a ellas.
    """
    service = EjecucionAuditoriaService(session)
    try:
        return service.obtener_celulas_disponibles(auditoria_id, usuario)
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND if "no encontrada" in str(error).lower()
            else status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        )


@router.post("/generar-programadas", response_model=dict)
def generar_programadas(
    session: Session = Depends(get_session),
    _: Usuario = Depends(require_roles("Administrador")),
):
    """Genera (idempotente) las ejecuciones pendientes del periodo vigente.

    Solo accesible por **Administrador** (o herramienta de pruebas).
    """
    from app.services.programacion_service import generar_pendientes

    return generar_pendientes(session)


@router.get("/pendientes", response_model=list[PendienteItem])
def listar_pendientes(
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_active_user),
):
    """Lista la agenda de auditorías programadas del usuario autenticado.

    Genera (de forma diferida) las ejecuciones del periodo vigente cuando
    corresponde.
    """
    service = EjecucionAuditoriaService(session)
    return service.mis_pendientes(usuario)


@router.post(
    "/pendientes/{ejecucion_id}/iniciar",
    response_model=EjecucionAuditoriaRead,
)
def iniciar_pendiente(
    ejecucion_id: int,
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_active_user),
):
    """Transiciona una ejecución ``pendiente`` a ``en_proceso``."""
    service = EjecucionAuditoriaService(session)
    try:
        return service.iniciar_pendiente(ejecucion_id, usuario)
    except DiaNoHabilitadoError as error:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(error),
        )
    except EjecucionAbiertaError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(error),
        )
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        )


@router.post(
    "/auditorias/{auditoria_id}/ejecuciones",
    response_model=EjecucionAuditoriaRead,
    status_code=status.HTTP_201_CREATED,
)
def iniciar_ejecucion(
    auditoria_id: int,
    datos: IniciarEjecucionRequest,
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_active_user),
):
    """Inicia una nueva ejecucion de auditoria."""
    service = EjecucionAuditoriaService(session)
    try:
        ejecucion = service.iniciar(
            auditoria_id=auditoria_id,
            usuario=usuario,
            celula_id=datos.celula_id,
        )
        return service.obtener_por_id(ejecucion.id)
    except DiaNoHabilitadoError as error:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(error),
        )
    except EjecucionAbiertaError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(error),
        )
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND if "no encontrada" in str(error).lower()
            else status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        )


@router.get(
    "/ejecuciones-auditoria/{ejecucion_id}",
    response_model=EjecucionAuditoriaRead,
)
def obtener_ejecucion(
    ejecucion_id: int,
    session: Session = Depends(get_session),
    _: Usuario = Depends(get_current_active_user),
):
    """Obtiene una ejecucion con sus criterios y respuestas."""
    service = EjecucionAuditoriaService(session)
    try:
        return service.obtener_por_id(ejecucion_id)
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        )


@router.get(
    "/{ejecucion_id}",
    response_model=EjecucionAuditoriaDetalle,
)
def obtener_ejecucion_detalle(
    ejecucion_id: int,
    session: Session = Depends(get_session),
    _: Usuario = Depends(get_current_active_user),
):
    """Consulta el detalle completo de una ejecucion con resumen V/A/R."""
    service = EjecucionAuditoriaService(session)
    try:
        return service.obtener_detalle(ejecucion_id)
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        )


@router.put(
    "/ejecuciones-auditoria/{ejecucion_id}/respuestas",
    response_model=EjecucionAuditoriaRead,
)
def guardar_respuestas(
    ejecucion_id: int,
    datos: GuardarRespuestasRequest,
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_active_user),
):
    """Guarda o actualiza las respuestas de una ejecucion."""
    service = EjecucionAuditoriaService(session)
    try:
        respuestas = [
            {"criterio_id": r.criterio_id, "valor": r.valor, "observaciones": r.observaciones}
            for r in datos.respuestas
        ]
        return service.guardar_respuestas(ejecucion_id, respuestas, usuario)
    except ValueError as error:
        if "no encontrada" in str(error).lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(error),
            )
        if "ya finalizada" in str(error).lower():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=str(error),
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        )


@router.post(
    "/ejecuciones-auditoria/{ejecucion_id}/finalizar",
    response_model=EjecucionAuditoriaRead,
)
def finalizar_ejecucion(
    ejecucion_id: int,
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_active_user),
):
    """Finaliza una ejecucion de auditoria."""
    service = EjecucionAuditoriaService(session)
    try:
        return service.finalizar(ejecucion_id, usuario)
    except ValueError as error:
        if "no encontrada" in str(error).lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(error),
            )
        if "ya esta finalizada" in str(error).lower():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=str(error),
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        )


@router.get(
    "/ejecuciones-auditoria/{ejecucion_id}/hallazgos",
    response_model=list[HallazgoDetallado],
)
def listar_hallazgos_de_ejecucion(
    ejecucion_id: int,
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_active_user),
):
    """Devuelve los hallazgos de una ejecucion ordenados por criterio.orden."""
    service = HallazgoService(session)
    try:
        return service.listar_por_ejecucion(ejecucion_id, usuario)
    except ValueError as error:
        mensaje = str(error).lower()
        if "no encontrad" in mensaje or "no encontrada" in mensaje:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(error),
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        )
