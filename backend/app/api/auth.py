"""Authentication endpoints (login, logout, etc.)."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from app.auth.dependencies import get_current_active_user
from app.auth.jwt import create_access_token
from app.auth.permissions import require_roles
from app.auth.security import verify_password
from app.db.database import get_session
from app.models.usuario import Usuario
from app.schemas.usuario import Token, UsuarioLogin, UsuarioRead

router = APIRouter(tags=["autenticación"])


@router.post("/auth/login", response_model=Token)
def login(
    credentials: UsuarioLogin,
    session: Session = Depends(get_session),
) -> Token:
    """Authenticate a user and return a JWT access token."""
    user = session.exec(
        select(Usuario).where(Usuario.correo == credentials.correo)
    ).first()

    if not user or not verify_password(credentials.contrasena, user.contrasena_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Correo o contraseña incorrectos.",
        )

    if not user.activo:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="El usuario está inactivo. Contacte al administrador.",
        )

    access_token = create_access_token(subject=str(user.id))

    return Token(access_token=access_token, token_type="bearer")


@router.get("/auth/me", response_model=UsuarioRead)
def read_current_user(
    current_user: Usuario = Depends(get_current_active_user),
) -> Usuario:
    return current_user


@router.get("/auth/admin")
def read_admin(
    current_user: Usuario = Depends(require_roles("Administrador")),
) -> dict[str, str]:
    return {"message": "Acceso autorizado para Administrador."}


@router.get("/auth/supervisor")
def read_supervisor(
    current_user: Usuario = Depends(require_roles("Administrador", "Supervisor")),
) -> dict[str, str]:
    return {"message": "Acceso autorizado para Supervisor/Administrador."}
