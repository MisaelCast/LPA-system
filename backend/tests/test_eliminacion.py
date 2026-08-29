"""Pruebas de eliminacion fisica de entidades de configuracion."""

from unittest.mock import MagicMock, patch

import pytest
from sqlmodel import Session

from app.models.area import Area
from app.models.auditoria import Auditoria
from app.models.capa import Capa
from app.models.celula import Celula
from app.repositories.area_repository import AreaRepository
from app.repositories.auditoria_repository import AuditoriaRepository
from app.repositories.capa_repository import CapaRepository
from app.repositories.celula_repository import CelulaRepository
from app.services.area_service import AreaService
from app.services.auditoria_service import AuditoriaService
from app.services.capa_service import CapaService
from app.services.celula_service import CelulaService


def _session_con_conteo(count: int) -> MagicMock:
    mock = MagicMock(spec=Session)
    mock.exec.return_value.one.return_value = count
    return mock


class TestEliminarCapa:
    def setup_method(self):
        self.mock_session = _session_con_conteo(0)
        self.service = CapaService(self.mock_session)

    def test_eliminar_capa_exitoso(self):
        capa = Capa(id=1, nombre="Auditor", activa=True)
        with patch.object(CapaRepository, "obtener_por_id", return_value=capa):
            with patch.object(CapaRepository, "eliminar") as mock_eliminar:
                self.service.eliminar(1)
        mock_eliminar.assert_called_once_with(capa)

    def test_eliminar_capa_inexistente(self):
        with patch.object(CapaRepository, "obtener_por_id", return_value=None):
            with pytest.raises(ValueError, match="Capa no encontrada"):
                self.service.eliminar(999)

    def test_eliminar_capa_con_auditorias(self):
        capa = Capa(id=1, nombre="Auditor", activa=True)
        self.mock_session.exec.return_value.one.return_value = 3
        with patch.object(CapaRepository, "obtener_por_id", return_value=capa):
            with pytest.raises(ValueError, match="auditorías asociadas"):
                self.service.eliminar(1)


class TestEliminarArea:
    def setup_method(self):
        self.mock_session = _session_con_conteo(0)
        self.service = AreaService(self.mock_session)

    def test_eliminar_area_exitoso(self):
        area = Area(id=1, nombre="Ensamble", activa=True)
        with patch.object(AreaRepository, "obtener_por_id", return_value=area):
            with patch.object(AreaRepository, "eliminar") as mock_eliminar:
                self.service.eliminar(1)
        mock_eliminar.assert_called_once_with(area)

    def test_eliminar_area_inexistente(self):
        with patch.object(AreaRepository, "obtener_por_id", return_value=None):
            with pytest.raises(ValueError, match="Area no encontrada"):
                self.service.eliminar(999)

    def test_eliminar_area_con_celulas(self):
        area = Area(id=1, nombre="Ensamble", activa=True)
        with patch.object(AreaRepository, "obtener_por_id", return_value=area):
            self.mock_session.exec.return_value.one.return_value = 2
            with pytest.raises(ValueError, match="células asociadas"):
                self.service.eliminar(1)


class TestEliminarCelula:
    def setup_method(self):
        self.mock_session = _session_con_conteo(0)
        self.service = CelulaService(self.mock_session)

    def test_eliminar_celula_exitoso(self):
        celula = Celula(id=1, numero=1, area_id=1, activa=True)
        with patch.object(CelulaRepository, "obtener_por_id", return_value=celula):
            with patch.object(CelulaRepository, "eliminar") as mock_eliminar:
                self.service.eliminar(1)
        mock_eliminar.assert_called_once_with(celula)

    def test_eliminar_celula_inexistente(self):
        with patch.object(CelulaRepository, "obtener_por_id", return_value=None):
            with pytest.raises(ValueError, match="Celula no encontrada"):
                self.service.eliminar(999)

    def test_eliminar_celula_con_ejecuciones(self):
        celula = Celula(id=1, numero=1, area_id=1, activa=True)
        self.mock_session.exec.return_value.one.return_value = 5
        with patch.object(CelulaRepository, "obtener_por_id", return_value=celula):
            with pytest.raises(ValueError, match="auditorías realizadas asociadas"):
                self.service.eliminar(1)


class TestEliminarAuditoria:
    def setup_method(self):
        self.mock_session = _session_con_conteo(0)
        self.service = AuditoriaService(self.mock_session)

    def test_eliminar_auditoria_exitoso_sin_criterios(self):
        auditoria = Auditoria(
            id=1, nombre="Proceso", activa=True, capa_id=1, frecuencia_id=1
        )
        self.mock_session.exec.return_value.one.return_value = 0
        self.mock_session.exec.return_value.all.return_value = []
        with patch.object(
            AuditoriaRepository, "obtener_por_id", return_value=auditoria
        ):
            with patch.object(AuditoriaRepository, "eliminar") as mock_eliminar:
                self.service.eliminar(1)
        mock_eliminar.assert_called_once_with(auditoria)

    def test_eliminar_auditoria_inexistente(self):
        with patch.object(AuditoriaRepository, "obtener_por_id", return_value=None):
            with pytest.raises(ValueError, match="Auditoria no encontrada"):
                self.service.eliminar(999)

    def test_eliminar_auditoria_con_ejecuciones(self):
        auditoria = Auditoria(
            id=1, nombre="Proceso", activa=True, capa_id=1, frecuencia_id=1
        )
        self.mock_session.exec.return_value.one.return_value = 4
        with patch.object(
            AuditoriaRepository, "obtener_por_id", return_value=auditoria
        ):
            with pytest.raises(ValueError, match="ejecuciones realizadas asociadas"):
                self.service.eliminar(1)
