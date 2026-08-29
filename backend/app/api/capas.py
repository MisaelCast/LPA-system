"""Endpoints para la gestion de capas."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import Session

from app.auth.permissions import require_roles
from app.db.database import get_session
from app.models.capa import Capa
from app.models.usuario import Usuario
from app.schemas.capa import CapaCreate, CapaEstadoUpdate, CapaRead, CapaUpdate
from app.services.capa_service import CapaService

router = APIRouter(tags=["capas"])


@router.get("/capas", response_model=list[CapaRead])
def listar_capas(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=1000),
    session: Session = Depends(get_session),
    _: Usuario = Depends(require_roles("Administrador")),
) -> list[Capa]:
    """Lista las capas del sistema con paginacion.

    Solo accesible por usuarios con rol **Administrador**.
    """
    return CapaService(session).listar(skip=skip, limit=limit)


@router.get("/capas/{capa_id}", response_model=CapaRead)
def obtener_capa(
    capa_id: int,
    session: Session = Depends(get_session),
    _: Usuario = Depends(require_roles("Administrador")),
) -> Capa:
    """Consulta una capa por su identificador.

    Solo accesible por usuarios con rol **Administrador**.
    """
    service = CapaService(session)
    try:
        return service.obtener_por_id(capa_id)
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        )


@router.patch("/capas/{capa_id}/estado", response_model=CapaRead)
def cambiar_estado_capa(
    capa_id: int,
    datos: CapaEstadoUpdate,
    session: Session = Depends(get_session),
    _: Usuario = Depends(require_roles("Administrador")),
) -> Capa:
    """Activa o desactiva una capa del sistema.

    Solo accesible por usuarios con rol **Administrador**.
    """
    service = CapaService(session)
    try:
        return service.cambiar_estado(capa_id, datos.activa)
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


@router.delete("/capas/{capa_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_capa(
    capa_id: int,
    session: Session = Depends(get_session),
    _: Usuario = Depends(require_roles("Administrador")),
) -> None:
    """Elimina fisicamente una capa del sistema.

    Solo accesible por usuarios con rol **Administrador**.
    """
    service = CapaService(session)
    try:
        service.eliminar(capa_id)
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


@router.put("/capas/{capa_id}", response_model=CapaRead)
def actualizar_capa(
    capa_id: int,
    datos: CapaUpdate,
    session: Session = Depends(get_session),
    _: Usuario = Depends(require_roles("Administrador")),
) -> Capa:
    """Actualiza los datos de una capa existente.

    Solo los campos enviados en el cuerpo seran modificados.
    Solo accesible por usuarios con rol **Administrador**.
    """
    service = CapaService(session)
    try:
        return service.actualizar(capa_id, datos)
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
    "/capas",
    response_model=CapaRead,
    status_code=status.HTTP_201_CREATED,
)
def crear_capa(
    datos: CapaCreate,
    session: Session = Depends(get_session),
    _: Usuario = Depends(require_roles("Administrador")),
) -> Capa:
    """Crea una nueva capa en el sistema.

    Solo accesible por usuarios con rol **Administrador**.
    """
    service = CapaService(session)
    try:
        return service.crear(datos)
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(error),
        )
