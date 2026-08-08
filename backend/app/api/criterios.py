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
from app.services.criterio_service import CriterioService

router = APIRouter(tags=["criterios"])


@router.get(
    "/auditorias/{auditoria_id}/criterios",
    response_model=list[CriterioRead],
)
def listar_criterios(
    auditoria_id: int,
    session: Session = Depends(get_session),
    _: Usuario = Depends(require_roles("Administrador")),
) -> list[Criterio]:
    """Lista los criterios de una auditoria ordenados por orden.

    Solo accesible por usuarios con rol **Administrador**.
    """
    return CriterioService(session).listar_por_auditoria(auditoria_id)


@router.get(
    "/criterios/{criterio_id}",
    response_model=CriterioRead,
)
def obtener_criterio(
    criterio_id: int,
    session: Session = Depends(get_session),
    _: Usuario = Depends(require_roles("Administrador")),
) -> Criterio:
    """Consulta un criterio por su identificador.

    Solo accesible por usuarios con rol **Administrador**.
    """
    service = CriterioService(session)
    try:
        return service.obtener_por_id(criterio_id)
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        )


@router.post(
    "/auditorias/{auditoria_id}/criterios",
    response_model=CriterioRead,
    status_code=status.HTTP_201_CREATED,
)
def crear_criterio(
    auditoria_id: int,
    datos: CriterioCreate,
    session: Session = Depends(get_session),
    _: Usuario = Depends(require_roles("Administrador")),
) -> Criterio:
    """Crea un nuevo criterio dentro de una auditoria.

    Solo accesible por usuarios con rol **Administrador**.
    """
    service = CriterioService(session)
    try:
        return service.crear(auditoria_id, datos)
    except ValueError as error:
        if "no existe" in str(error).lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(error),
            )
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(error),
        )


@router.put("/criterios/{criterio_id}", response_model=CriterioRead)
def actualizar_criterio(
    criterio_id: int,
    datos: CriterioUpdate,
    session: Session = Depends(get_session),
    _: Usuario = Depends(require_roles("Administrador")),
) -> Criterio:
    """Actualiza los datos de un criterio existente.

    El auditoria_id no puede modificarse desde este endpoint.
    Solo los campos enviados en el cuerpo seran modificados.
    Solo accesible por usuarios con rol **Administrador**.
    """
    service = CriterioService(session)
    try:
        return service.actualizar(criterio_id, datos)
    except ValueError as error:
        if "no encontrado" in str(error).lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(error),
            )
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(error),
        )


@router.patch(
    "/criterios/{criterio_id}/estado",
    response_model=CriterioRead,
)
def cambiar_estado_criterio(
    criterio_id: int,
    datos: CriterioEstadoUpdate,
    session: Session = Depends(get_session),
    _: Usuario = Depends(require_roles("Administrador")),
) -> Criterio:
    """Activa o desactiva un criterio.

    Solo accesible por usuarios con rol **Administrador**.
    """
    service = CriterioService(session)
    try:
        return service.cambiar_estado(criterio_id, datos.activo)
    except ValueError as error:
        if "no encontrado" in str(error).lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(error),
            )
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(error),
        )
