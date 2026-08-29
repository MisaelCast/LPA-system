"""Endpoints para la gestion de auditorias."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import Session

from app.auth.permissions import require_roles
from app.db.database import get_session
from app.models.auditoria import Auditoria
from app.models.usuario import Usuario
from app.schemas.auditoria import (
    AuditoriaCreate,
    AuditoriaEstadoUpdate,
    AuditoriaRead,
    AuditoriaUpdate,
)
from app.services.auditoria_service import AuditoriaService

router = APIRouter(tags=["auditorias"])


@router.get("/auditorias", response_model=list[AuditoriaRead])
def listar_auditorias(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=1000),
    session: Session = Depends(get_session),
    _: Usuario = Depends(require_roles("Administrador")),
) -> list[Auditoria]:
    """Lista las auditorias del sistema con paginacion.

    Solo accesible por usuarios con rol **Administrador**.
    """
    return AuditoriaService(session).listar(skip=skip, limit=limit)


@router.get("/auditorias/{auditoria_id}", response_model=AuditoriaRead)
def obtener_auditoria(
    auditoria_id: int,
    session: Session = Depends(get_session),
    _: Usuario = Depends(require_roles("Administrador")),
) -> Auditoria:
    """Consulta una auditoria por su identificador.

    Solo accesible por usuarios con rol **Administrador**.
    """
    service = AuditoriaService(session)
    try:
        return service.obtener_por_id(auditoria_id)
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        )


@router.patch("/auditorias/{auditoria_id}/estado", response_model=AuditoriaRead)
def cambiar_estado_auditoria(
    auditoria_id: int,
    datos: AuditoriaEstadoUpdate,
    session: Session = Depends(get_session),
    _: Usuario = Depends(require_roles("Administrador")),
) -> Auditoria:
    """Activa o desactiva una auditoria del sistema.

    Solo accesible por usuarios con rol **Administrador**.
    """
    service = AuditoriaService(session)
    try:
        return service.cambiar_estado(auditoria_id, datos.activa)
    except ValueError as error:
        if "no encontrada" in str(error).lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(error),
            )
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(error),
        )


@router.delete("/auditorias/{auditoria_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_auditoria(
    auditoria_id: int,
    session: Session = Depends(get_session),
    _: Usuario = Depends(require_roles("Administrador")),
) -> None:
    """Elimina fisicamente una auditoria del sistema.

    Solo accesible por usuarios con rol **Administrador**.
    """
    service = AuditoriaService(session)
    try:
        service.eliminar(auditoria_id)
    except ValueError as error:
        if "no encontrada" in str(error).lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(error),
            )
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(error),
        )


@router.put("/auditorias/{auditoria_id}", response_model=AuditoriaRead)
def actualizar_auditoria(
    auditoria_id: int,
    datos: AuditoriaUpdate,
    session: Session = Depends(get_session),
    _: Usuario = Depends(require_roles("Administrador")),
) -> Auditoria:
    """Actualiza los datos de una auditoria existente.

    Solo los campos enviados en el cuerpo seran modificados.
    Solo accesible por usuarios con rol **Administrador**.
    """
    service = AuditoriaService(session)
    try:
        return service.actualizar(auditoria_id, datos)
    except ValueError as error:
        if "no encontrada" in str(error).lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(error),
            )
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(error),
        )


@router.post(
    "/auditorias",
    response_model=AuditoriaRead,
    status_code=status.HTTP_201_CREATED,
)
def crear_auditoria(
    datos: AuditoriaCreate,
    session: Session = Depends(get_session),
    _: Usuario = Depends(require_roles("Administrador")),
) -> Auditoria:
    """Crea una nueva auditoria en el sistema.

    Solo accesible por usuarios con rol **Administrador**.
    """
    service = AuditoriaService(session)
    try:
        return service.crear(datos)
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(error),
        )
