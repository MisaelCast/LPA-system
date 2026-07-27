"""Endpoints para la gestión de usuarios."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from app.auth.permissions import require_roles
from app.auth.security import hash_password
from app.db.database import get_session
from app.models.usuario import Usuario
from app.repositories.usuario_repository import UsuarioRepository
from app.schemas.usuario import UsuarioCreate, UsuarioRead

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
    repo = UsuarioRepository(session)

    if repo.obtener_por_correo(datos.correo):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ya existe un usuario con ese correo electrónico.",
        )

    usuario = Usuario(
        nombre=datos.nombre,
        correo=datos.correo,
        contrasena_hash=hash_password(datos.contrasena),
        activo=datos.activo,
        rol_id=datos.rol_id,
    )

    return repo.crear(usuario)
