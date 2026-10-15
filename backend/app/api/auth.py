"""Authentication endpoints (login, logout, etc.)."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

import jwt

from app.auth.dependencies import get_current_active_user
from app.auth.jwt import (
    create_access_token,
    create_refresh_token,
    decode_refresh_token,
)
from app.auth.permissions import require_roles
from app.auth.security import verify_password
from app.config import settings
from app.db.database import get_session
from app.models.usuario import Usuario
from app.schemas.usuario import (
    RefreshTokenRequest,
    Token,
    UsuarioLogin,
    UsuarioRead,
)

router = APIRouter(tags=["autenticación"])


@router.post("/auth/login", response_model=Token)
def login(
    credentials: UsuarioLogin,
    session: Session = Depends(get_session),
) -> Token:
    """Authenticate a user and return JWT access and refresh tokens."""
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
    refresh_token = create_refresh_token(subject=str(user.id))

    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=settings.access_token_expire_minutes * 60,
    )


@router.post("/auth/refresh", response_model=Token)
def refresh_token(
    datos: RefreshTokenRequest,
    session: Session = Depends(get_session),
) -> Token:
    """Intercambia un refresh token válido por un nuevo par de tokens.

    El refresh token se rota (se emite uno nuevo) en cada llamada exitosa.
    """
    try:
        payload = decode_refresh_token(datos.refresh_token)
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="La sesión ha expirado. Inicia sesión nuevamente.",
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token inválido.",
        )

    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token inválido.",
        )

    user = session.get(Usuario, int(user_id))
    if user is None or not user.activo:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="La sesión ya no es válida.",
        )

    new_access = create_access_token(subject=str(user.id))
    new_refresh = create_refresh_token(subject=str(user.id))

    return Token(
        access_token=new_access,
        refresh_token=new_refresh,
        token_type="bearer",
        expires_in=settings.access_token_expire_minutes * 60,
    )


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
