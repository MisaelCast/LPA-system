"""Endpoints para la gestion de criterios."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from app.auth.permissions import require_roles
from app.db.database import get_session
from app.models.criterio import Criterio
from app.models.usuario import Usuario
from app.schemas.criterio import (
    CriterioCreate,
    CriterioEstadoUpdate,
    CriterioRead,
    CriterioUpdate,
)
from app.services.auditoria_service import ROLES_GESTION_AUDITORIAS
from app.services.criterio_service import CriterioService

router = APIRouter(tags=["criterios"])

_ROLES = require_roles(*ROLES_GESTION_AUDITORIAS)


def _mapear_error_criterio(error: ValueError) -> HTTPException:
    """Traduce los ValueErrors del servicio a respuestas HTTP."""
    mensaje = str(error)
    if "no tiene permisos" in mensaje.lower():
        return HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=mensaje,
        )
    if "no encontrad" in mensaje.lower() or "no existe" in mensaje.lower():
        return HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=mensaje,
        )
    return HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail=mensaje,
    )


@router.get(
    "/auditorias/{auditoria_id}/criterios",
    response_model=list[CriterioRead],
)
def listar_criterios(
    auditoria_id: int,
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(_ROLES),
) -> list[Criterio]:
    """Lista los criterios de una auditoria ordenados por orden.

    Un Supervisor o Gerente solo puede consultar las auditorías de sus
    capas/áreas.
    """
    service = CriterioService(session)
    try:
        service._validar_auditoria_gestionable(auditoria_id, usuario)
    except ValueError as error:
        raise _mapear_error_criterio(error)
    return service.listar_por_auditoria(auditoria_id)


@router.get(
    "/criterios/{criterio_id}",
    response_model=CriterioRead,
)
def obtener_criterio(
    criterio_id: int,
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(_ROLES),
) -> Criterio:
    """Consulta un criterio por su identificador.

    Un Supervisor o Gerente solo puede consultar criterios de las
    auditorías de sus capas/áreas.
    """
    service = CriterioService(session)
    try:
        criterio = service.obtener_por_id(criterio_id)
        service._validar_auditoria_gestionable(
            criterio.auditoria_id, usuario
        )
        return criterio
    except ValueError as error:
        raise _mapear_error_criterio(error)


@router.post(
    "/auditorias/{auditoria_id}/criterios",
    response_model=CriterioRead,
    status_code=status.HTTP_201_CREATED,
)
def crear_criterio(
    auditoria_id: int,
    datos: CriterioCreate,
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(_ROLES),
) -> Criterio:
    """Crea un nuevo criterio dentro de una auditoria.

    Un Supervisor o Gerente solo puede crear criterios en las auditorías
    de sus capas/áreas.
    """
    service = CriterioService(session)
    try:
        return service.crear(auditoria_id, datos, usuario)
    except ValueError as error:
        raise _mapear_error_criterio(error)


@router.put("/criterios/{criterio_id}", response_model=CriterioRead)
def actualizar_criterio(
    criterio_id: int,
    datos: CriterioUpdate,
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(_ROLES),
) -> Criterio:
    """Actualiza los datos de un criterio existente.

    El auditoria_id no puede modificarse desde este endpoint.
    Solo los campos enviados en el cuerpo seran modificados.
    Un Supervisor o Gerente solo puede modificar criterios de las
    auditorías de sus capas/áreas.
    """
    service = CriterioService(session)
    try:
        return service.actualizar(criterio_id, datos, usuario)
    except ValueError as error:
        raise _mapear_error_criterio(error)


@router.patch(
    "/criterios/{criterio_id}/estado",
    response_model=CriterioRead,
)
def cambiar_estado_criterio(
    criterio_id: int,
    datos: CriterioEstadoUpdate,
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(_ROLES),
) -> Criterio:
    """Activa o desactiva un criterio.

    Un Supervisor o Gerente solo puede modificar criterios de las
    auditorías de sus capas/áreas.
    """
    service = CriterioService(session)
    try:
        return service.cambiar_estado(criterio_id, datos.activo, usuario)
    except ValueError as error:
        raise _mapear_error_criterio(error)
