"""Pruebas para el modulo de Capas."""

import pytest
from unittest.mock import MagicMock, patch
from sqlmodel import Session

from app.models.capa import Capa
from app.schemas.capa import CapaCreate, CapaUpdate
from app.services.capa_service import CapaService
from app.repositories.capa_repository import CapaRepository


class TestCapaService:
    """Pruebas unitarias para CapaService."""

    def setup_method(self):
        self.mock_session = MagicMock(spec=Session)
        self.service = CapaService(self.mock_session)

    def test_crear_capa_exitoso(self):
        """Verifica que se pueda crear una capa con datos validos."""
        datos = CapaCreate(nombre="Auditor", descripcion="Capa de auditor", activa=True)

        with patch.object(CapaRepository, 'obtener_por_nombre', return_value=None):
            with patch.object(CapaRepository, 'crear', return_value=Capa(id=1, **datos.model_dump())):
                resultado = self.service.crear(datos)

        assert resultado.nombre == "Auditor"
        assert resultado.descripcion == "Capa de auditor"
        assert resultado.activa is True

    def test_crear_capa_nombre_duplicado(self):
        """Verifica que no se pueda crear una capa con nombre duplicado."""
        datos = CapaCreate(nombre="Auditor", activa=True)
        capa_existente = Capa(id=1, nombre="Auditor", activa=True)

        with patch.object(CapaRepository, 'obtener_por_nombre', return_value=capa_existente):
            with pytest.raises(ValueError, match="Ya existe una capa con ese nombre"):
                self.service.crear(datos)

    def test_obtener_por_id_existe(self):
        """Verifica que se pueda obtener una capa por ID."""
        capa_mock = Capa(id=1, nombre="Supervisor", activa=True)

        with patch.object(CapaRepository, 'obtener_por_id', return_value=capa_mock):
            resultado = self.service.obtener_por_id(1)

        assert resultado.id == 1
        assert resultado.nombre == "Supervisor"

    def test_obtener_por_id_no_existe(self):
        """Verifica que se lance error si la capa no existe."""
        with patch.object(CapaRepository, 'obtener_por_id', return_value=None):
            with pytest.raises(ValueError, match="Capa no encontrada"):
                self.service.obtener_por_id(999)

    def test_actualizar_capa_exitoso(self):
        """Verifica que se pueda actualizar una capa."""
        capa_existente = Capa(id=1, nombre="Auditor", descripcion="Original", activa=True)
        datos_update = CapaUpdate(nombre="Auditor Actualizado", descripcion="Nueva descripcion")

        with patch.object(CapaRepository, 'obtener_por_id', return_value=capa_existente):
            with patch.object(CapaRepository, 'obtener_por_nombre', return_value=None):
                with patch.object(CapaRepository, 'actualizar', return_value=capa_existente) as mock_actualizar:
                    self.service.actualizar(1, datos_update)
                    mock_actualizar.assert_called_once()

    def test_actualizar_capa_nombre_duplicado(self):
        """Verifica que no se pueda actualizar con nombre duplicado."""
        capa_existente = Capa(id=1, nombre="Auditor", activa=True)
        capa_duplicada = Capa(id=2, nombre="Supervisor", activa=True)
        datos_update = CapaUpdate(nombre="Supervisor")

        with patch.object(CapaRepository, 'obtener_por_id', return_value=capa_existente):
            with patch.object(CapaRepository, 'obtener_por_nombre', return_value=capa_duplicada):
                with pytest.raises(ValueError, match="Ya existe una capa con ese nombre"):
                    self.service.actualizar(1, datos_update)

    def test_cambiar_estado_exitoso(self):
        """Verifica que se pueda cambiar el estado de una capa."""
        capa_existente = Capa(id=1, nombre="Auditor", activa=True)

        with patch.object(CapaRepository, 'obtener_por_id', return_value=capa_existente):
            with patch.object(CapaRepository, 'actualizar', return_value=capa_existente) as mock_actualizar:
                self.service.cambiar_estado(1, False)
                mock_actualizar.assert_called_once()

    def test_cambiar_estado_mismo_valor(self):
        """Verifica que no se actualice si el estado es el mismo."""
        capa_existente = Capa(id=1, nombre="Auditor", activa=True)

        with patch.object(CapaRepository, 'obtener_por_id', return_value=capa_existente):
            with patch.object(CapaRepository, 'actualizar') as mock_actualizar:
                self.service.cambiar_estado(1, True)
                mock_actualizar.assert_not_called()

    def test_listar_capas(self):
        """Verifica que se puedan listar las capas."""
        capas_mock = [
            Capa(id=1, nombre="Auditor", activa=True),
            Capa(id=2, nombre="Supervisor", activa=True),
            Capa(id=3, nombre="Gerente", activa=True),
        ]

        with patch.object(CapaRepository, 'listar', return_value=capas_mock):
            resultado = self.service.listar()

        assert len(resultado) == 3
        assert resultado[0].nombre == "Auditor"
        assert resultado[1].nombre == "Supervisor"
        assert resultado[2].nombre == "Gerente"
