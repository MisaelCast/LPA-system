"""Pruebas para el modulo de Criterios."""

from unittest.mock import MagicMock, patch

import pytest
from sqlmodel import Session

from app.models.criterio import Criterio
from app.schemas.criterio import CriterioCreate, CriterioUpdate
from app.services.criterio_service import CriterioService
from app.repositories.criterio_repository import CriterioRepository


class TestCriterioService:
    """Pruebas unitarias para CriterioService."""

    def setup_method(self):
        self.mock_session = MagicMock(spec=Session)
        self.service = CriterioService(self.mock_session)

    def test_crear_criterio_exitoso(self):
        """Verifica que se cree un criterio correctamente."""
        datos = CriterioCreate(
            descripcion="Verificar proceso",
            orden=1,
            activo=True,
        )
        self.mock_session.get.return_value = MagicMock()

        with patch.object(CriterioRepository, "obtener_por_auditoria_y_orden", return_value=None):
            with patch.object(
                CriterioRepository,
                "crear",
                return_value=Criterio(
                    id=1,
                    descripcion="Verificar proceso",
                    orden=1,
                    activo=True,
                    auditoria_id=1,
                ),
            ):
                resultado = self.service.crear(1, datos)

        assert resultado.descripcion == "Verificar proceso"
        assert resultado.orden == 1
        assert resultado.auditoria_id == 1

    def test_crear_criterio_orden_ocupado(self):
        """Verifica que se asigne el siguiente orden si el deseado esta ocupado."""
        datos = CriterioCreate(descripcion="Test", orden=1, activo=True)
        self.mock_session.get.return_value = MagicMock()
        existente = Criterio(id=1, descripcion="Existente", orden=1, auditoria_id=1)

        with patch.object(
            CriterioRepository, "obtener_por_auditoria_y_orden", return_value=existente
        ):
            with patch.object(CriterioRepository, "max_orden", return_value=5):
                with patch.object(
                    CriterioRepository,
                    "crear",
                    return_value=Criterio(
                        id=2, descripcion="Test", orden=6, auditoria_id=1
                    ),
                ):
                    resultado = self.service.crear(1, datos)

        assert resultado.orden == 6

    def test_crear_criterio_auditoria_inexistente(self):
        """Verifica que falle si la auditoria no existe."""
        datos = CriterioCreate(descripcion="Test", orden=1, activo=True)
        self.mock_session.get.return_value = None

        with pytest.raises(ValueError, match="La auditoria especificada no existe"):
            self.service.crear(999, datos)

    def test_obtener_por_id_existe(self):
        """Verifica que se obtenga un criterio por ID."""
        criterio = Criterio(id=1, descripcion="Test", orden=1, auditoria_id=1)

        with patch.object(CriterioRepository, "obtener_por_id", return_value=criterio):
            resultado = self.service.obtener_por_id(1)

        assert resultado.id == 1

    def test_obtener_por_id_no_existe(self):
        """Verifica que lance error si no existe."""
        with patch.object(CriterioRepository, "obtener_por_id", return_value=None):
            with pytest.raises(ValueError, match="Criterio no encontrado"):
                self.service.obtener_por_id(999)

    def test_actualizar_criterio_exitoso(self):
        """Verifica que se actualice correctamente."""
        criterio = Criterio(id=1, descripcion="Old", orden=1, auditoria_id=1)
        datos = CriterioUpdate(descripcion="New")

        with patch.object(CriterioRepository, "obtener_por_id", return_value=criterio):
            with patch.object(
                CriterioRepository, "actualizar", return_value=criterio
            ) as mock_actualizar:
                self.service.actualizar(1, datos)
                mock_actualizar.assert_called_once()

    def test_actualizar_criterio_swap_orden(self):
        """Verifica que se intercambien ordenes si hay conflicto."""
        criterio_a = Criterio(id=1, descripcion="A", orden=1, auditoria_id=1)
        criterio_b = Criterio(id=2, descripcion="B", orden=2, auditoria_id=1)
        datos = CriterioUpdate(orden=2)

        with patch.object(CriterioRepository, "obtener_por_id", return_value=criterio_a):
            with patch.object(
                CriterioRepository,
                "obtener_por_auditoria_y_orden",
                return_value=criterio_b,
            ):
                with patch.object(
                    CriterioRepository, "actualizar", return_value=criterio_a
                ) as mock_actualizar:
                    self.service.actualizar(1, datos)
                    assert mock_actualizar.call_count >= 1

    def test_cambiar_estado(self):
        """Verifica que se cambie el estado correctamente."""
        criterio = Criterio(id=1, descripcion="Test", orden=1, activo=True, auditoria_id=1)

        with patch.object(CriterioRepository, "obtener_por_id", return_value=criterio):
            with patch.object(
                CriterioRepository, "actualizar", return_value=criterio
            ) as mock_actualizar:
                self.service.cambiar_estado(1, False)
                mock_actualizar.assert_called_once()

    def test_cambiar_estado_mismo_valor(self):
        """Verifica que no actualice si el estado es el mismo."""
        criterio = Criterio(id=1, descripcion="Test", orden=1, activo=False, auditoria_id=1)

        with patch.object(CriterioRepository, "obtener_por_id", return_value=criterio):
            with patch.object(CriterioRepository, "actualizar") as mock_actualizar:
                self.service.cambiar_estado(1, False)
                mock_actualizar.assert_not_called()

    def test_listar_por_auditoria(self):
        """Verifica que se listen los criterios de una auditoria."""
        criterios = [
            Criterio(id=1, descripcion="C1", orden=1, auditoria_id=1),
            Criterio(id=2, descripcion="C2", orden=2, auditoria_id=1),
        ]

        with patch.object(CriterioRepository, "listar_por_auditoria", return_value=criterios):
            resultado = self.service.listar_por_auditoria(1)

        assert len(resultado) == 2
        assert resultado[0].orden == 1
        assert resultado[1].orden == 2
