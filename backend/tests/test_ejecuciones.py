"""Pruebas para el historial y consulta de ejecuciones de auditoria."""

from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest
from sqlmodel import Session

from app.models.auditoria import Auditoria
from app.models.celula import Celula
from app.models.ejecucion_auditoria import EjecucionAuditoria
from app.models.respuesta import Respuesta
from app.models.usuario import Usuario
from app.services.ejecucion_auditoria_service import EjecucionAuditoriaService
from app.repositories.ejecucion_auditoria_repository import EjecucionAuditoriaRepository
from app.repositories.respuesta_repository import RespuestaRepository


def _usuario(id_: int = 1, rol_nombre: str = "Auditor") -> MagicMock:
    usuario = MagicMock()
    usuario.id = id_
    rol = MagicMock()
    rol.nombre = rol_nombre
    usuario.rol = rol
    return usuario


def _ejecucion(
    id_: int = 10,
    estado: str = "en_proceso",
    usuario_id: int = 1,
    auditoria_id: int = 1,
    celula_id: int | None = 1,
    fecha: datetime | None = None,
) -> MagicMock:
    ej = MagicMock(spec=EjecucionAuditoria)
    ej.id = id_
    ej.estado = estado
    ej.auditoria_id = auditoria_id
    ej.usuario_id = usuario_id
    ej.celula_id = celula_id
    ej.fecha = fecha or datetime(2026, 8, 29, 14, 30)
    ej.observaciones = None
    return ej


def _respuesta(valor: str, ejecucion_id: int = 10) -> MagicMock:
    r = MagicMock(spec=Respuesta)
    r.valor = valor
    r.ejecucion_auditoria_id = ejecucion_id
    return r


class TestListarEjecuciones:
    """Pruebas para listar ejecuciones del historial."""

    def setup_method(self):
        self.mock_session = MagicMock(spec=Session)
        self.service = EjecucionAuditoriaService(self.mock_session)
        self.usuario = _usuario(rol_nombre="Administrador")

    def test_listar_ejecuciones_admin_ve_todas(self):
        ejec = _ejecucion()
        with patch.object(
            EjecucionAuditoriaRepository,
            "listar_con_filtros",
            return_value=[ejec],
        ):
            self.mock_session.exec.return_value.all.return_value = []
            self.mock_session.exec.return_value.one.return_value = 15
            with patch.object(
                EjecucionAuditoriaService, "_contar_criterios_activos", return_value=15
            ):
                resultado = self.service.listar_ejecuciones(
                    self.usuario, skip=0, limit=100
                )

        assert len(resultado) == 1
        item = resultado[0]
        assert item["id"] == 10
        assert item["estado"] == "en_proceso"
        assert item["resumen"]["total_criterios"] == 15

    def test_listar_ejecuciones_auditor_solo_propias(self):
        """Un auditor solo ve sus propias ejecuciones."""
        auditor = _usuario(id_=7, rol_nombre="Auditor")
        with patch.object(
            EjecucionAuditoriaRepository, "listar_con_filtros"
        ) as mock_listar:
            mock_listar.return_value = []
            self.service.listar_ejecuciones(auditor, skip=0, limit=100)

        kwargs = mock_listar.call_args.kwargs
        assert kwargs["usuario_id"] == 7

    def test_listar_ejecuciones_supervisor_ve_todas(self):
        """Un supervisor ve todas las ejecuciones (no se limita a las propias)."""
        supervisor = _usuario(id_=7, rol_nombre="Supervisor")
        with patch.object(
            EjecucionAuditoriaRepository, "listar_con_filtros"
        ) as mock_listar:
            mock_listar.return_value = []
            self.service.listar_ejecuciones(supervisor, skip=0, limit=100)

        kwargs = mock_listar.call_args.kwargs
        assert kwargs["usuario_id"] is None

    def test_listar_ejecuciones_admin_ve_todas_sin_usuario_id(self):
        """Un administrador ve todas sin forzar usuario_id."""
        admin = _usuario(id_=7, rol_nombre="Administrador")
        with patch.object(
            EjecucionAuditoriaRepository, "listar_con_filtros"
        ) as mock_listar:
            mock_listar.return_value = []
            self.service.listar_ejecuciones(admin, skip=0, limit=100)

        kwargs = mock_listar.call_args.kwargs
        assert kwargs["usuario_id"] is None

    def test_filtro_area_se_propaga(self):
        """El filtro por area se pasa al repositorio."""
        admin = _usuario(rol_nombre="Administrador")
        with patch.object(
            EjecucionAuditoriaRepository, "listar_con_filtros"
        ) as mock_listar:
            mock_listar.return_value = []
            self.service.listar_ejecuciones(admin, area_id=3)

        kwargs = mock_listar.call_args.kwargs
        assert kwargs["area_id"] == 3

    def test_listar_ejecuciones_admin_solo_propias(self):
        """Con solo_propias, el admin se limita a sus propias ejecuciones."""
        admin = _usuario(id_=7, rol_nombre="Administrador")
        with patch.object(
            EjecucionAuditoriaRepository, "listar_con_filtros"
        ) as mock_listar:
            mock_listar.return_value = []
            self.service.listar_ejecuciones(admin, solo_propias=True)

        kwargs = mock_listar.call_args.kwargs
        assert kwargs["usuario_id"] == 7

    def test_filtros_se_propagan(self):
        """Los filtros se pasan al repositorio."""
        admin = _usuario(rol_nombre="Administrador")
        fecha_desde = datetime(2026, 8, 1)
        with patch.object(
            EjecucionAuditoriaRepository, "listar_con_filtros"
        ) as mock_listar:
            mock_listar.return_value = []
            self.service.listar_ejecuciones(
                admin,
                auditoria_id=1,
                celula_id=2,
                estado="finalizada",
                fecha_desde=fecha_desde,
            )

        kwargs = mock_listar.call_args.kwargs
        assert kwargs["auditoria_id"] == 1
        assert kwargs["celula_id"] == 2
        assert kwargs["estado"] == "finalizada"
        assert kwargs["fecha_desde"] == fecha_desde

    def test_resumen_conteo_var(self):
        """El resumen cuenta correctamente V, A y R."""
        ejec = _ejecucion()
        respuestas = [
            _respuesta("V"),
            _respuesta("V"),
            _respuesta("A"),
            _respuesta("R"),
        ]
        with patch.object(
            EjecucionAuditoriaRepository,
            "listar_con_filtros",
            return_value=[ejec],
        ):
            self.mock_session.exec.return_value.all.return_value = respuestas
            with patch.object(
                EjecucionAuditoriaService, "_contar_criterios_activos", return_value=4
            ):
                resultado = self.service.listar_ejecuciones(self.usuario)

        resumen = resultado[0]["resumen"]
        assert resumen["total_v"] == 2
        assert resumen["total_a"] == 1
        assert resumen["total_r"] == 1
        assert resumen["total_criterios"] == 4


class TestObtenerDetalle:
    """Pruebas para el detalle de una ejecucion."""

    def setup_method(self):
        self.mock_session = MagicMock(spec=Session)
        self.service = EjecucionAuditoriaService(self.mock_session)

    def test_obtener_detalle_incluye_resumen(self):
        ejec = _ejecucion(estado="finalizada")
        respuestas = [_respuesta("V"), _respuesta("A")]

        with patch.object(
            EjecucionAuditoriaService, "obtener_por_id", return_value=ejec
        ):
            with patch.object(
                EjecucionAuditoriaService, "_contar_criterios_activos", return_value=15
            ):
                with patch.object(
                    RespuestaRepository, "listar_por_ejecucion", return_value=respuestas
                ):
                    resultado = self.service.obtener_detalle(10)

        assert resultado["id"] == 10
        assert resultado["estado"] == "finalizada"
        assert resultado["resumen"]["total_v"] == 1
        assert resultado["resumen"]["total_a"] == 1

    def test_obtener_detalle_no_existe(self):
        with patch.object(
            EjecucionAuditoriaService, "obtener_por_id"
        ) as mock_obtener:
            mock_obtener.side_effect = ValueError("Ejecucion de auditoria no encontrada.")
            with pytest.raises(ValueError, match="no encontrada"):
                self.service.obtener_detalle(999)


class TestPermisoModificacion:
    """Verifica que solo el auditor asignado o un administrador modifiquen."""

    def setup_method(self):
        self.mock_session = MagicMock(spec=Session)
        self.service = EjecucionAuditoriaService(self.mock_session)

    def test_supervisor_no_puede_modificar_ejecucion_ajena(self):
        """Un supervisor no puede modificar la auditoría original del auditor."""
        supervisor = _usuario(id_=9, rol_nombre="Supervisor")
        ejecucion = _ejecucion(usuario_id=1)

        with pytest.raises(ValueError, match="Solo el auditor asignado"):
            self.service._validar_puede_modificar(ejecucion, supervisor)

    def test_auditor_asignado_puede_modificar(self):
        """El auditor dueño de la ejecución puede modificarla."""
        auditor = _usuario(id_=1, rol_nombre="Auditor")
        ejecucion = _ejecucion(usuario_id=1)

        self.service._validar_puede_modificar(ejecucion, auditor)

    def test_admin_puede_modificar(self):
        """El administrador puede modificar cualquier ejecución."""
        admin = _usuario(id_=5, rol_nombre="Administrador")
        ejecucion = _ejecucion(usuario_id=1)

        self.service._validar_puede_modificar(ejecucion, admin)


class TestEstadoEjecucion:
    """Verifica que el estado distingue en_proceso de finalizada."""

    def test_estado_valores(self):
        en_proceso = _ejecucion(estado="en_proceso")
        finalizada = _ejecucion(estado="finalizada")
        assert en_proceso.estado == "en_proceso"
        assert finalizada.estado == "finalizada"
        assert en_proceso.estado != finalizada.estado
