"""Pruebas de los permisos de gestión de usuarios."""

from unittest.mock import MagicMock

from sqlmodel import Session

from app.models.rol import Rol
from app.models.usuario import Usuario
from app.services.usuario_service import UsuarioService


def _rol(id_: int, nombre: str) -> MagicMock:
    rol = MagicMock(spec=Rol)
    rol.id = id_
    rol.nombre = nombre
    return rol


def _usuario(id_: int, rol_id: int) -> MagicMock:
    usuario = MagicMock(spec=Usuario)
    usuario.id = id_
    usuario.rol_id = rol_id
    return usuario


def _service() -> UsuarioService:
    session = MagicMock(spec=Session)
    roles = {
        1: _rol(1, "Administrador"),
        2: _rol(2, "Gerente"),
        3: _rol(3, "Supervisor"),
        4: _rol(4, "Auditor"),
        5: _rol(5, "Responsable de Manufactura"),
    }

    def get_side_effect(cls, id_):
        if cls is Rol:
            return roles.get(id_)
        return None

    session.get.side_effect = get_side_effect
    return UsuarioService(session)


def test_supervisor_gestiona_y_crea_supervisores_y_auditores():
    service = _service()
    actor = _usuario(10, 3)

    assert service.puede_gestionar(actor, _usuario(11, 3)) is True
    assert service.puede_gestionar(actor, _usuario(12, 4)) is True
    assert service.puede_crear_rol(actor, 3) is True
    assert service.puede_crear_rol(actor, 4) is True


def test_supervisor_no_gestiona_ni_crea_otros_roles():
    service = _service()
    actor = _usuario(10, 3)

    assert service.puede_gestionar(actor, _usuario(20, 2)) is False
    assert service.puede_gestionar(actor, _usuario(1, 1)) is False
    assert service.puede_gestionar(actor, _usuario(30, 5)) is False
    assert service.puede_crear_rol(actor, 2) is False
    assert service.puede_crear_rol(actor, 1) is False
    assert service.puede_crear_rol(actor, 5) is False
