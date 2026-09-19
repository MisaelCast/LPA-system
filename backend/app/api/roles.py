"""Endpoints para consultar roles."""

from fastapi import APIRouter, Depends
from sqlmodel import Session, select

from app.auth.permissions import require_roles
from app.db.database import get_session
from app.models.rol import Rol
from app.models.usuario import Usuario
from app.schemas.rol import RolRead

router = APIRouter(tags=["roles"])


@router.get("/roles", response_model=list[RolRead])
def listar_roles(
    session: Session = Depends(get_session),
    _: Usuario = Depends(require_roles("Administrador")),
) -> list[Rol]:
    """Lista los roles asignables al crear/editar usuarios.

    Excluye el rol ``Administrador``: es un rol único que no puede
    asignarse a nuevos usuarios.
    """
    return list(session.exec(select(Rol).where(Rol.nombre != "Administrador")).all())
