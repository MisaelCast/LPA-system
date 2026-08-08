"""Pruebas para el modulo de Auditorias."""

from unittest.mock import MagicMock, patch

import pytest
from sqlmodel import Session

from app.models.auditoria import Auditoria
from app.models.capa import Capa
from app.models.frecuencia import Frecuencia
from app.schemas.auditoria import AuditoriaCreate, AuditoriaUpdate
from app.services.auditoria_service import AuditoriaService
from app.repositories.auditoria_repository import AuditoriaRepository
from app.services.capa_service import CapaService
from app.services.frecuencia_service import FrecuenciaService


class TestAuditoriaService:
    """Pruebas unitarias para AuditoriaService."""

    def setup_method(self):
        self.mock_session = MagicMock(spec=Session)
        self.service = AuditoriaService(self.mock_session)

    def _mock_fk_get(self):
        """Mock de session.get para enriquecer_read."""
        self.mock_session.get.side_effect = lambda cls, id: MagicMock(
            spec=cls, nombre="Mock"
        )

    def test_crear_auditoria_exitoso(self):
        """Verifica que se pueda crear una auditoria con datos validos."""
        datos = AuditoriaCreate(
            nombre="Auditoria Proceso",
            descripcion="Descripcion de prueba",
            activa=True,
            capa_id=1,
            frecuencia_id=1,
            area_id=1,
        )

        self._mock_fk_get()

        with patch.object(
            CapaService, "obtener_por_id", return_value=MagicMock(spec=Capa)
        ):
            with patch.object(
                FrecuenciaService,
                "obtener_por_id",
                return_value=MagicMock(spec=Frecuencia),
            ):
                with patch.object(
                    AuditoriaRepository, "obtener_por_nombre", return_value=None
                ):
                    with patch.object(
                        AuditoriaRepository,
                        "crear",
                        return_value=Auditoria(id=1, **datos.model_dump()),
                    ):
                        resultado = self.service.crear(datos)

        assert resultado.nombre == "Auditoria Proceso"
        assert resultado.capa_id == 1
        assert resultado.frecuencia_id == 1
        assert resultado.area_id == 1

    def test_crear_auditoria_nombre_duplicado(self):
        """Verifica que no se pueda crear con nombre duplicado."""
        datos = AuditoriaCreate(
            nombre="Duplicada", activa=True, capa_id=1, frecuencia_id=1
        )

        with patch.object(
            AuditoriaRepository,
            "obtener_por_nombre",
            return_value=Auditoria(
                id=1, nombre="Duplicada", capa_id=1, frecuencia_id=1
            ),
        ):
            with pytest.raises(ValueError, match="Ya existe una auditoria"):
                self.service.crear(datos)

    def test_crear_auditoria_capa_inexistente(self):
        """Verifica que falle si la capa no existe."""
        datos = AuditoriaCreate(
            nombre="Test", activa=True, capa_id=999, frecuencia_id=1
        )

        with patch.object(AuditoriaRepository, "obtener_por_nombre", return_value=None):
            with patch.object(
                CapaService,
                "obtener_por_id",
                side_effect=ValueError("Capa no encontrada."),
            ):
                with pytest.raises(ValueError, match="La capa especificada no existe"):
                    self.service.crear(datos)

    def test_obtener_por_id_existe(self):
        """Verifica que se obtenga una auditoria por ID."""
        auditoria = Auditoria(
            id=1,
            nombre="Test",
            activa=True,
            capa_id=1,
            frecuencia_id=1,
        )
        self._mock_fk_get()

        with patch.object(AuditoriaRepository, "obtener_por_id", return_value=auditoria):
            resultado = self.service.obtener_por_id(1)

        assert resultado.id == 1
        assert resultado.nombre == "Test"

    def test_obtener_por_id_no_existe(self):
        """Verifica que se lance error si no existe."""
        with patch.object(AuditoriaRepository, "obtener_por_id", return_value=None):
            with pytest.raises(ValueError, match="Auditoria no encontrada"):
                self.service.obtener_por_id(999)

    def test_actualizar_auditoria_exitoso(self):
        """Verifica que se actualice correctamente."""
        auditoria = Auditoria(
            id=1,
            nombre="Original",
            activa=True,
            capa_id=1,
            frecuencia_id=1,
        )
        datos = AuditoriaUpdate(nombre="Actualizada")

        self._mock_fk_get()

        with patch.object(AuditoriaRepository, "obtener_por_id", return_value=auditoria):
            with patch.object(
                AuditoriaRepository, "obtener_por_nombre", return_value=None
            ):
                with patch.object(
                    AuditoriaRepository, "actualizar", return_value=auditoria
                ) as mock_actualizar:
                    self.service.actualizar(1, datos)
                    mock_actualizar.assert_called_once()

    def test_actualizar_nombre_duplicado(self):
        """Verifica que falle si el nombre ya esta en uso."""
        auditoria = Auditoria(
            id=1,
            nombre="Original",
            activa=True,
            capa_id=1,
            frecuencia_id=1,
        )
        duplicado = Auditoria(
            id=2,
            nombre="EnUso",
            activa=True,
            capa_id=1,
            frecuencia_id=1,
        )

        with patch.object(AuditoriaRepository, "obtener_por_id", return_value=auditoria):
            with patch.object(
                AuditoriaRepository,
                "obtener_por_nombre",
                return_value=duplicado,
            ):
                with pytest.raises(
                    ValueError, match="Ya existe una auditoria"
                ):
                    self.service.actualizar(
                        1, AuditoriaUpdate(nombre="EnUso")
                    )

    def test_cambiar_estado(self):
        """Verifica que se cambie el estado correctamente."""
        auditoria = Auditoria(
            id=1,
            nombre="Test",
            activa=True,
            capa_id=1,
            frecuencia_id=1,
        )
        self._mock_fk_get()

        with patch.object(AuditoriaRepository, "obtener_por_id", return_value=auditoria):
            with patch.object(
                AuditoriaRepository, "actualizar", return_value=auditoria
            ) as mock_actualizar:
                self.service.cambiar_estado(1, False)
                mock_actualizar.assert_called_once()

    def test_cambiar_estado_mismo_valor(self):
        """Verifica que no actualice si el estado es el mismo."""
        auditoria = Auditoria(
            id=1,
            nombre="Test",
            activa=True,
            capa_id=1,
            frecuencia_id=1,
        )
        self._mock_fk_get()

        with patch.object(AuditoriaRepository, "obtener_por_id", return_value=auditoria):
            with patch.object(AuditoriaRepository, "actualizar") as mock_actualizar:
                self.service.cambiar_estado(1, True)
                mock_actualizar.assert_not_called()

    def test_listar_auditorias(self):
        """Verifica que se listen las auditorias."""
        auditorias = [
            Auditoria(
                id=1,
                nombre="A1",
                activa=True,
                capa_id=1,
                frecuencia_id=1,
            ),
            Auditoria(
                id=2,
                nombre="A2",
                activa=False,
                capa_id=2,
                frecuencia_id=2,
            ),
        ]
        self._mock_fk_get()

        with patch.object(AuditoriaRepository, "listar", return_value=auditorias):
            resultado = self.service.listar()

        assert len(resultado) == 2
