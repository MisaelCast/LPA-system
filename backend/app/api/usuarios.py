"""Endpoints para la gestión de usuarios."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from app.auth.permissions import require_roles
from app.db.database import get_session
from app.models.usuario import Usuario
from app.schemas.usuario import UsuarioCreate, UsuarioRead
from app.services.usuario_service import UsuarioService

router = APIRouter(tags=["usuarios"])


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
