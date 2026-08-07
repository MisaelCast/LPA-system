"""Endpoints para la gestion de areas."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import Session

from app.auth.permissions import require_roles
from app.db.database import get_session
from app.models.area import Area
from app.models.usuario import Usuario
from app.schemas.area import AreaCreate, AreaEstadoUpdate, AreaRead, AreaUpdate
from app.services.area_service import AreaService

router = APIRouter(tags=["areas"])


@router.get("/areas", response_model=list[AreaRead])
def listar_areas(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=1000),
    session: Session = Depends(get_session),
    _: Usuario = Depends(require_roles("Administrador")),
) -> list[Area]:
    """Lista las areas del sistema con paginacion.

    Solo accesible por usuarios con rol **Administrador**.
    """
    return AreaService(session).listar(skip=skip, limit=limit)


@router.get("/areas/{area_id}", response_model=AreaRead)
def obtener_area(
    area_id: int,
    session: Session = Depends(get_session),
    _: Usuario = Depends(require_roles("Administrador")),
) -> Area:
    """Consulta un area por su identificador.

    Solo accesible por usuarios con rol **Administrador**.
    """
    service = AreaService(session)
    try:
        return service.obtener_por_id(area_id)
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        )


@router.patch("/areas/{area_id}/estado", response_model=AreaRead)
def cambiar_estado_area(
    area_id: int,
    datos: AreaEstadoUpdate,
    session: Session = Depends(get_session),
    _: Usuario = Depends(require_roles("Administrador")),
) -> Area:
    """Activa o desactiva un area del sistema.

    Solo accesible por usuarios con rol **Administrador**.
    """
    service = AreaService(session)
    try:
        return service.cambiar_estado(area_id, datos.activa)
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


@router.put("/areas/{area_id}", response_model=AreaRead)
def actualizar_area(
    area_id: int,
    datos: AreaUpdate,
    session: Session = Depends(get_session),
    _: Usuario = Depends(require_roles("Administrador")),
) -> Area:
    """Actualiza los datos de un area existente.

    Solo los campos enviados en el cuerpo seran modificados.
    Solo accesible por usuarios con rol **Administrador**.
    """
    service = AreaService(session)
    try:
        return service.actualizar(area_id, datos)
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
    "/areas",
    response_model=AreaRead,
    status_code=status.HTTP_201_CREATED,
)
def crear_area(
    datos: AreaCreate,
    session: Session = Depends(get_session),
    _: Usuario = Depends(require_roles("Administrador")),
) -> Area:
    """Crea una nueva area en el sistema.

    Solo accesible por usuarios con rol **Administrador**.
    """
    service = AreaService(session)
    try:
        return service.crear(datos)
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(error),
        )
