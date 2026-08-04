"""Seed inicial de datos mínimos para una base de datos vacía."""

from sqlmodel import Session, select

from app.auth.security import hash_password
from app.config import settings
from app.db.database import SessionLocal
from app.models.rol import Rol
from app.models.usuario import Usuario

_ROLES_INICIALES = ["Administrador", "Supervisor", "Auditor"]

_ADMIN_CORREO = "admin@lpa.com"
_ADMIN_NOMBRE = "Administrador"


def _seed_roles(session: Session) -> Rol:
    """Crea los roles que no existan aún. Retorna el rol Administrador."""
    rol_admin = None
    for nombre in _ROLES_INICIALES:
        existente = session.exec(select(Rol).where(Rol.nombre == nombre)).first()
        if existente is None:
            rol = Rol(nombre=nombre, descripcion=f"Rol de {nombre.lower()}")
            session.add(rol)
            session.flush()
            existente = rol

        if nombre == "Administrador":
            rol_admin = existente

    session.commit()
    return rol_admin  # type: ignore[return-value]


def _seed_admin(session: Session, rol_admin: Rol) -> None:
    """Crea el usuario administrador si no existe."""
    existente = session.exec(select(Usuario).where(Usuario.correo == _ADMIN_CORREO)).first()
    if existente is not None:
        return

    admin = Usuario(
        nombre=_ADMIN_NOMBRE,
        correo=_ADMIN_CORREO,
        contrasena_hash=hash_password(settings.default_admin_password),
        activo=True,
        rol_id=rol_admin.id,  # type: ignore[arg-type]
    )
    session.add(admin)
    session.commit()


def seed_inicial() -> None:
    """Ejecuta el seed de datos mínimos para que el sistema sea utilizable.

    Es idempotente: no duplica roles ni el usuario administrador.
    """
    with SessionLocal() as session:
        rol_admin = _seed_roles(session)
        _seed_admin(session, rol_admin)
