"""Endpoints para la ejecucion de auditorias."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from app.auth.dependencies import get_current_active_user
from app.auth.permissions import require_roles
from app.db.database import get_session
from app.models.usuario import Usuario
from app.schemas.auditoria import AuditoriaRead
from app.schemas.celula import CelulaRead
from app.schemas.ejecucion_auditoria import (
    EjecucionAuditoriaRead,
    GuardarRespuestasRequest,
    IniciarEjecucionRequest,
)
from app.schemas.hallazgo import HallazgoDetallado
from app.services.ejecucion_auditoria_service import EjecucionAuditoriaService
from app.services.hallazgo_service import HallazgoService

router = APIRouter(
    prefix="/ejecuciones-auditoria",
    tags=["ejecuciones-auditoria"],
)


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
    _: Usuario = Depends(get_current_active_user),
) -> list:
    """Devuelve las celulas del area de una auditoria especifica."""
    service = EjecucionAuditoriaService(session)
    try:
        return service.obtener_celulas_disponibles(auditoria_id)
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND if "no encontrada" in str(error).lower()
            else status.HTTP_400_BAD_REQUEST,
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
    """Inicia una nueva ejecucion de auditoria sobre una celula."""
    service = EjecucionAuditoriaService(session)
    try:
        ejecucion = service.iniciar(
            auditoria_id=auditoria_id,
            usuario=usuario,
            celula_id=datos.celula_id,
        )
        return service.obtener_por_id(ejecucion.id)
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
