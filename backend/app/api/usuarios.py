"""Endpoints para la gestión de usuarios."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import Session

from app.auth.permissions import require_roles
from app.db.database import get_session
from app.models.usuario import Usuario
from app.schemas.usuario import UsuarioCreate, UsuarioRead
from app.services.usuario_service import UsuarioService

router = APIRouter(tags=["usuarios"])


@router.get("/usuarios", response_model=list[UsuarioRead])
def listar_usuarios(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=1000),
    session: Session = Depends(get_session),
    _: Usuario = Depends(require_roles("Administrador")),
) -> list[Usuario]:
    """Lista los usuarios del sistema con paginación.

    Solo accesible por usuarios con rol **Administrador**.
    """
    return UsuarioService(session).listar(skip=skip, limit=limit)


@router.post(
    "/usuarios",
    response_model=UsuarioRead,
    status_code=status.HTTP_201_CREATED,
)
def crear_usuario(
    datos: UsuarioCreate,
    session: Session = Depends(get_session),
    _: Usuario = Depends(require_roles("Administrador")),
) -> Usuario:
    """Crea un nuevo usuario en el sistema.

    Solo accesible por usuarios con rol **Administrador**.
    """
    service = UsuarioService(session)
    try:
        return service.crear(datos)
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(error),
        )
