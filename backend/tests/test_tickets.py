"""Pruebas del flujo de tickets de hallazgos (responsables, avance y cierre)."""

from unittest.mock import MagicMock, patch

import pytest
from sqlmodel import Session

from app.models.ejecucion_auditoria import EjecucionAuditoria
from app.models.respuesta import Respuesta
from app.services.hallazgo_service import HallazgoService


def _usuario(
    id_: int, rol_nombre: str = "Auditor", areas: list | None = None
) -> MagicMock:
    usuario = MagicMock()
    usuario.id = id_
    usuario.nombre = f"Usuario {id_}"
    usuario.correo = f"u{id_}@lpa.com"
    usuario.activo = True
    rol = MagicMock()
    rol.nombre = rol_nombre
    usuario.rol = rol
    usuario.areas = areas if areas is not None else []
    return usuario


def _area(id_: int) -> MagicMock:
    a = MagicMock()
    a.id = id_
    return a


def _hallazgo(
    estado: str = "abierto",
    area_id: int | None = 5,
    responsables: list | None = None,
) -> MagicMock:
    h = MagicMock()
    h.id = 1
    h.respuesta_id = 100
    h.estado = estado
    h.area_responsable_id = area_id
    h.responsables = responsables or []
    h.fecha_limite = None
    h.fecha_cierre = None
    h.accion_correctiva = None
    return h


class TestFlujoTickets:
    def setup_method(self):
        self.session = MagicMock(spec=Session)
        self.service = HallazgoService(self.session)

        self.auditor = _usuario(1, "Auditor")
        # La ejecución pertenece al auditor dueño (usuario_id = 1).
        self.ejecucion = MagicMock(spec=EjecucionAuditoria)
        self.ejecucion.id = 10
        self.ejecucion.usuario_id = 1
        self.respuesta = MagicMock(spec=Respuesta)
        self.respuesta.id = 100
        self.respuesta.ejecucion_auditoria_id = 10
        self.responsable = _usuario(
            9, "Responsable de Manufactura", areas=[_area(5)]
        )

        self.service._enriquecer = MagicMock(return_value=MagicMock())
        self.service._repo.obtener_por_id = MagicMock()
        self.service._repo.actualizar = MagicMock(side_effect=lambda h: h)
        self.service._respuesta_repo.obtener_por_id = MagicMock(
            return_value=self.respuesta
        )

        def get_side(cls, _id):
            name = cls.__name__ if hasattr(cls, "__name__") else str(cls)
            if name == "EjecucionAuditoria":
                return self.ejecucion
            if name == "Usuario":
                return self.responsable
            return None

        self.session.get.side_effect = get_side

    # --- Asignación ---

    def test_asignar_responsable_ok(self):
        hallazgo = _hallazgo()
        self.service._repo.obtener_por_id.return_value = hallazgo

        self.service.asignar_responsable(1, 9, None, self.auditor)

        assert hallazgo.responsables == [self.responsable]
        assert hallazgo.fecha_limite is not None  # plazo automático
        self.session.add.assert_called_once()  # entrada de historial

    def test_asignar_responsable_area_incorrecta(self):
        hallazgo = _hallazgo(area_id=5)
        self.service._repo.obtener_por_id.return_value = hallazgo
        self.responsable.areas = [_area(6)]  # otra área

        with pytest.raises(ValueError, match="no pertenece al area"):
            self.service.asignar_responsable(1, 9, None, self.auditor)

    def test_asignar_responsable_rol_incorrecto(self):
        hallazgo = _hallazgo()
        self.service._repo.obtener_por_id.return_value = hallazgo
        self.responsable = _usuario(9, "Auditor", areas=[_area(5)])

        with pytest.raises(ValueError, match="no es Responsable"):
            self.service.asignar_responsable(1, 9, None, self.auditor)

    def test_asignar_responsable_sin_permiso(self):
        hallazgo = _hallazgo()
        self.service._repo.obtener_por_id.return_value = hallazgo
        otro = _usuario(2, "Auditor")

        with pytest.raises(ValueError, match="auditor"):
            self.service.asignar_responsable(1, 9, None, otro)

    # --- Avance ---

    def test_registrar_avance_transiciona_a_en_correccion(self):
        hallazgo = _hallazgo(estado="abierto", responsables=[self.responsable])
        self.service._repo.obtener_por_id.return_value = hallazgo

        self.service.registrar_avance(
            1, "Se ajustó la fixtura", None, self.responsable
        )

        assert hallazgo.estado == "en_correccion"
        assert hallazgo.accion_correctiva == "Se ajustó la fixtura"
        self.session.add.assert_called_once()

    def test_registrar_avance_solo_responsable(self):
        hallazgo = _hallazgo(responsables=[self.responsable])
        self.service._repo.obtener_por_id.return_value = hallazgo
        otro = _usuario(3, "Auditor")

        with pytest.raises(ValueError, match="responsable asignado"):
            self.service.registrar_avance(1, "x", None, otro)

    # --- Cierre ---

    def test_solicitar_cierre_requiere_en_correccion(self):
        hallazgo = _hallazgo(estado="abierto", responsables=[self.responsable])
        self.service._repo.obtener_por_id.return_value = hallazgo

        with pytest.raises(ValueError, match="en corrección"):
            self.service.solicitar_cierre(1, "listo", self.responsable)

    def test_solicitar_cierre_ok(self):
        hallazgo = _hallazgo(
            estado="en_correccion", responsables=[self.responsable]
        )
        self.service._repo.obtener_por_id.return_value = hallazgo

        self.service.solicitar_cierre(1, "corregido", self.responsable)

        assert hallazgo.estado == "cierre_solicitado"
        self.session.add.assert_called_once()

    def test_resolver_cierre_aprueba(self):
        hallazgo = _hallazgo(
            estado="cierre_solicitado", responsables=[self.responsable]
        )
        self.service._repo.obtener_por_id.return_value = hallazgo
        self.ejecucion.usuario_id = self.auditor.id

        self.service.resolver_cierre(1, True, "ok", self.auditor)

        assert hallazgo.estado == "cerrado"
        assert hallazgo.fecha_cierre is not None

    def test_resolver_cierre_rechaza_vuelve_a_en_correccion(self):
        hallazgo = _hallazgo(
            estado="cierre_solicitado", responsables=[self.responsable]
        )
        self.service._repo.obtener_por_id.return_value = hallazgo

        self.service.resolver_cierre(1, False, "falta limpiar", self.auditor)

        assert hallazgo.estado == "en_correccion"
        assert hallazgo.fecha_cierre is None

    def test_responsable_no_aprueba_su_propio_cierre(self):
        # El responsable también es el auditor dueño de la ejecución.
        responsable_dueno = _usuario(
            1, "Responsable de Manufactura", areas=[_area(5)]
        )
        hallazgo = _hallazgo(
            estado="cierre_solicitado", responsables=[responsable_dueno]
        )
        self.service._repo.obtener_por_id.return_value = hallazgo

        with pytest.raises(ValueError, match="propio hallazgo"):
            self.service.resolver_cierre(1, True, "ok", responsable_dueno)

    def test_resolver_cierre_sin_solicitud(self):
        hallazgo = _hallazgo(estado="en_correccion", responsables=[self.responsable])
        self.service._repo.obtener_por_id.return_value = hallazgo

        with pytest.raises(ValueError, match="solicitud de cierre pendiente"):
            self.service.resolver_cierre(1, True, None, self.auditor)


class TestResponsablesDelArea:
    def setup_method(self):
        self.session = MagicMock(spec=Session)
        self.service = HallazgoService(self.session)
        self.usuario = _usuario(1, "Auditor")

    def test_responsables_del_area(self):
        hallazgo = _hallazgo(area_id=5)
        self.service._repo.obtener_por_id = MagicMock(return_value=hallazgo)
        responsable = _usuario(9, "Responsable de Manufactura")
        self.session.exec.return_value.all.return_value = [responsable]

        resultado = self.service.responsables_del_area(1, self.usuario)

        assert len(resultado) == 1
        assert resultado[0].nombre == responsable.nombre

    def test_responsables_del_area_sin_area(self):
        hallazgo = _hallazgo(area_id=None)
        self.service._repo.obtener_por_id = MagicMock(return_value=hallazgo)

        assert self.service.responsables_del_area(1, self.usuario) == []
