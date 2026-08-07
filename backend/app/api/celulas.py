"""Endpoints para la gestion de celulas."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import Session

from app.auth.permissions import require_roles
from app.db.database import get_session
from app.models.celula import Celula
from app.models.usuario import Usuario
from app.schemas.celula import (
    CelulaCreate,
    CelulaEstadoUpdate,
    CelulaRead,
    CelulaUpdate,
)
from app.services.celula_service import CelulaService

router = APIRouter(tags=["celulas"])


@router.get("/areas/{area_id}/celulas", response_model=list[CelulaRead])
def listar_celulas(
    area_id: int,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=1000),
    session: Session = Depends(get_session),
    _: Usuario = Depends(require_roles("Administrador")),
) -> list[Celula]:
    """Lista las celulas de un area.

    Solo accesible por usuarios con rol **Administrador**.
    """
    return CelulaService(session).listar_por_area(
        area_id, skip=skip, limit=limit
    )


@router.post(
    "/areas/{area_id}/celulas",
    response_model=CelulaRead,
    status_code=status.HTTP_201_CREATED,
)
def crear_celula(
    area_id: int,
    datos: CelulaCreate,
    session: Session = Depends(get_session),
    _: Usuario = Depends(require_roles("Administrador")),
) -> Celula:
    """Crea una nueva celula en un area.

    Solo accesible por usuarios con rol **Administrador**.
    """
    service = CelulaService(session)
    try:
        return service.crear(area_id, datos)
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(error),
        )


@router.put("/celulas/{celula_id}", response_model=CelulaRead)
def actualizar_celula(
    celula_id: int,
    datos: CelulaUpdate,
    session: Session = Depends(get_session),
    _: Usuario = Depends(require_roles("Administrador")),
) -> Celula:
    """Actualiza los datos de una celula existente.

    Solo los campos enviados en el cuerpo seran modificados.
    Solo accesible por usuarios con rol **Administrador**.
    """
    service = CelulaService(session)
    try:
        return service.actualizar(celula_id, datos)
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


@router.patch("/celulas/{celula_id}/estado", response_model=CelulaRead)
def cambiar_estado_celula(
    celula_id: int,
    datos: CelulaEstadoUpdate,
    session: Session = Depends(get_session),
    _: Usuario = Depends(require_roles("Administrador")),
) -> Celula:
    """Activa o desactiva una celula.

    Solo accesible por usuarios con rol **Administrador**.
    """
    service = CelulaService(session)
    try:
        return service.cambiar_estado(celula_id, datos.activa)
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
