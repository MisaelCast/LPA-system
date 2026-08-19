"""Pruebas para el modulo de Hallazgos."""

from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest
from sqlmodel import Session

from app.models.auditoria import Auditoria
from app.models.criterio import Criterio
from app.models.ejecucion_auditoria import EjecucionAuditoria
from app.models.hallazgo import Hallazgo
from app.models.respuesta import Respuesta
from app.schemas.hallazgo import HallazgoCreate, HallazgoUpdate
from app.services.hallazgo_service import HallazgoService


def _usuario(id_: int = 1, rol_nombre: str = "Auditor") -> MagicMock:
    usuario = MagicMock()
    usuario.id = id_
    rol = MagicMock()
    rol.nombre = rol_nombre
    usuario.rol = rol
    return usuario


def _ejecucion(
    id_: int = 10, estado: str = "en_proceso", usuario_id: int = 1
) -> MagicMock:
    ej = MagicMock(spec=EjecucionAuditoria)
    ej.id = id_
    ej.estado = estado
    ej.auditoria_id = 1
    ej.usuario_id = usuario_id
    ej.celula_id = None
    return ej


def _respuesta(
    id_: int = 100, valor: str = "A", ejecucion_id: int = 10, criterio_id: int = 1
) -> MagicMock:
    r = MagicMock(spec=Respuesta)
    r.id = id_
    r.valor = valor
    r.ejecucion_auditoria_id = ejecucion_id
    r.criterio_id = criterio_id
    return r


def _criterio(id_: int = 1, orden: int = 1, auditoria_id: int = 1) -> MagicMock:
    c = MagicMock(spec=Criterio)
    c.id = id_
    c.descripcion = "Criterio prueba"
    c.orden = orden
    c.auditoria_id = auditoria_id
    return c


def _auditoria(id_: int = 1, nombre: str = "Ensamble Final") -> MagicMock:
    a = MagicMock(spec=Auditoria)
    a.id = id_
    a.nombre = nombre
    return a


class TestHallazgoService:
    """Pruebas unitarias para HallazgoService."""

    def setup_method(self):
        self.mock_session = MagicMock(spec=Session)
        self.service = HallazgoService(self.mock_session)
        self.usuario = _usuario()

    def _configurar_lookups(
        self,
        respuesta: Respuesta | None,
        ejecucion: EjecucionAuditoria | None,
        criterio: Criterio | None = None,
        auditoria: Auditoria | None = None,
    ) -> None:
        """Configura session.get para responder segun la clase consultada."""

        def get_side(cls, _id):
            name = cls.__name__ if hasattr(cls, "__name__") else str(cls)
            if name == "EjecucionAuditoria":
                return ejecucion
            if name == "Criterio":
                return criterio
            if name == "Auditoria":
                return auditoria
            return None

        self.mock_session.get.side_effect = get_side

    def test_crear_hallazgo_para_respuesta_A(self):
        """Caso 1: crear hallazgo cuando la respuesta es A (menor)."""
        respuesta = _respuesta(valor="A")
        ejecucion = _ejecucion()
        criterio = _criterio()
        auditoria = _auditoria()
        self._configurar_lookups(respuesta, ejecucion, criterio, auditoria)

        with patch.object(
            type(self.service._respuesta_repo),
            "obtener_por_id",
            return_value=respuesta,
        ):
            with patch.object(
                type(self.service._repo),
                "obtener_por_respuesta",
                return_value=None,
            ):
                with patch.object(
                    type(self.service._repo),
                    "crear",
                    return_value=Hallazgo(
                        id=1,
                        descripcion="Detalle",
                        fecha_creacion=datetime.utcnow(),
                        respuesta_id=respuesta.id,
                    ),
                ):
                    datos = HallazgoCreate(
                        descripcion="Detalle", respuesta_id=respuesta.id
                    )
                    resultado = self.service.crear(datos, self.usuario)

        assert resultado.tipo == "A"
        assert resultado.descripcion == "Detalle"
        assert resultado.respuesta_id == respuesta.id
        assert resultado.auditoria_nombre == "Ensamble Final"

    def test_crear_hallazgo_para_respuesta_R(self):
        """Caso 2: crear hallazgo cuando la respuesta es R (mayor)."""
        respuesta = _respuesta(valor="R")
        ejecucion = _ejecucion()
        criterio = _criterio()
        auditoria = _auditoria()
        self._configurar_lookups(respuesta, ejecucion, criterio, auditoria)

        with patch.object(
            type(self.service._respuesta_repo),
            "obtener_por_id",
            return_value=respuesta,
        ):
            with patch.object(
                type(self.service._repo),
                "obtener_por_respuesta",
                return_value=None,
            ):
                with patch.object(
                    type(self.service._repo),
                    "crear",
                    return_value=Hallazgo(
                        id=2,
                        descripcion="Mayor",
                        fecha_creacion=datetime.utcnow(),
                        respuesta_id=respuesta.id,
                    ),
                ):
                    datos = HallazgoCreate(
                        descripcion="Mayor", respuesta_id=respuesta.id
                    )
                    resultado = self.service.crear(datos, self.usuario)

        assert resultado.tipo == "R"

    def test_rechazar_hallazgo_para_respuesta_V(self):
        """Caso 3: rechazar hallazgo cuando la respuesta es V."""
        respuesta = _respuesta(valor="V")
        ejecucion = _ejecucion()
        self._configurar_lookups(respuesta, ejecucion)

        with patch.object(
            type(self.service._respuesta_repo),
            "obtener_por_id",
            return_value=respuesta,
        ):
            with pytest.raises(ValueError, match="Solo se pueden crear"):
                self.service.crear(
                    HallazgoCreate(
                        descripcion="x", respuesta_id=respuesta.id
                    ),
                    self.usuario,
                )

    def test_rechazar_hallazgo_respuesta_inexistente(self):
        """Caso 4: 404 cuando la respuesta no existe."""
        with patch.object(
            type(self.service._respuesta_repo),
            "obtener_por_id",
            return_value=None,
        ):
            with pytest.raises(ValueError, match="Respuesta no encontrada"):
                self.service.crear(
                    HallazgoCreate(descripcion="x", respuesta_id=999),
                    self.usuario,
                )

    def test_rechazar_hallazgo_duplicado(self):
        """Caso 5: rechazar segundo hallazgo para la misma respuesta."""
        respuesta = _respuesta()
        ejecucion = _ejecucion()
        criterio = _criterio()
        self._configurar_lookups(respuesta, ejecucion, criterio)

        existente = Hallazgo(
            id=1, descripcion="previo", fecha_creacion=datetime.utcnow(), respuesta_id=respuesta.id
        )

        with patch.object(
            type(self.service._respuesta_repo),
            "obtener_por_id",
            return_value=respuesta,
        ):
            with patch.object(
                type(self.service._repo),
                "obtener_por_respuesta",
                return_value=existente,
            ):
                with pytest.raises(ValueError, match="Ya existe un hallazgo"):
                    self.service.crear(
                        HallazgoCreate(
                            descripcion="nuevo", respuesta_id=respuesta.id
                        ),
                        self.usuario,
                    )

    def test_obtener_hallazgo(self):
        """Caso 6: obtener hallazgo enriquecido."""
        hallazgo = Hallazgo(
            id=5,
            descripcion="Detalle",
            fecha_creacion=datetime.utcnow(),
            respuesta_id=100,
        )
        respuesta = _respuesta(valor="A")
        criterio = _criterio(orden=3)
        ejecucion = _ejecucion()
        auditoria = _auditoria()
        self._configurar_lookups(respuesta, ejecucion, criterio, auditoria)

        with patch.object(
            type(self.service._repo), "obtener_por_id", return_value=hallazgo
        ):
            with patch.object(
                type(self.service._respuesta_repo),
                "obtener_por_id",
                return_value=respuesta,
            ):
                resultado = self.service.obtener_por_id(5)

        assert resultado.id == 5
        assert resultado.tipo == "A"
        assert resultado.criterio_orden == 3
        assert resultado.ejecucion_id == 10
        assert resultado.auditoria_nombre == "Ensamble Final"

    def test_obtener_hallazgo_no_existe(self):
        with patch.object(
            type(self.service._repo), "obtener_por_id", return_value=None
        ):
            with pytest.raises(ValueError, match="Hallazgo no encontrado"):
                self.service.obtener_por_id(999)

    def test_actualizar_hallazgo(self):
        """Caso 7: actualizar descripcion del hallazgo."""
        hallazgo = Hallazgo(
            id=1,
            descripcion="Vieja",
            fecha_creacion=datetime.utcnow(),
            respuesta_id=100,
        )
        respuesta = _respuesta()
        ejecucion = _ejecucion()
        criterio = _criterio()
        auditoria = _auditoria()
        self._configurar_lookups(respuesta, ejecucion, criterio, auditoria)

        with patch.object(
            type(self.service._repo), "obtener_por_id", return_value=hallazgo
        ):
            with patch.object(
                type(self.service._respuesta_repo),
                "obtener_por_id",
                return_value=respuesta,
            ):
                with patch.object(
                    type(self.service._repo),
                    "actualizar",
                    return_value=hallazgo,
                ) as mock_actualizar:
                    resultado = self.service.actualizar(
                        1,
                        HallazgoUpdate(descripcion="Nueva"),
                        self.usuario,
                    )

        assert resultado.descripcion == "Nueva"
        mock_actualizar.assert_called_once()

    def test_actualizar_hallazgo_ejecucion_finalizada(self):
        """Caso 10: no permitir modificar en ejecucion finalizada."""
        hallazgo = Hallazgo(
            id=1, descripcion="x", fecha_creacion=datetime.utcnow(), respuesta_id=100
        )
        respuesta = _respuesta()
        ejecucion = _ejecucion(estado="finalizada")
        self._configurar_lookups(respuesta, ejecucion)

        with patch.object(
            type(self.service._repo), "obtener_por_id", return_value=hallazgo
        ):
            with patch.object(
                type(self.service._respuesta_repo),
                "obtener_por_id",
                return_value=respuesta,
            ):
                with pytest.raises(ValueError, match="finalizada"):
                    self.service.actualizar(
                        1, HallazgoUpdate(descripcion="y"), self.usuario
                    )

    def test_listar_por_ejecucion(self):
        """Caso 8: listar hallazgos por ejecucion, ordenados por criterio.orden."""
        ejecucion = _ejecucion()
        respuesta_a = _respuesta(id_=101, valor="A", criterio_id=1)
        respuesta_r = _respuesta(id_=102, valor="R", criterio_id=2)
        criterio1 = _criterio(id_=1, orden=1)
        criterio2 = _criterio(id_=2, orden=2)
        auditoria = _auditoria()

        self._configurar_lookups(
            respuesta_a, ejecucion, criterio1, auditoria
        )

        hallazgo_a = Hallazgo(
            id=1,
            descripcion="a",
            fecha_creacion=datetime.utcnow(),
            respuesta_id=101,
        )
        hallazgo_r = Hallazgo(
            id=2,
            descripcion="r",
            fecha_creacion=datetime.utcnow(),
            respuesta_id=102,
        )

        # _obtener_ejecucion
        def get_side(cls, _id):
            name = cls.__name__ if hasattr(cls, "__name__") else str(cls)
            if name == "EjecucionAuditoria":
                return ejecucion
            if name == "Criterio":
                return {1: criterio1, 2: criterio2}.get(_id)
            if name == "Auditoria":
                return auditoria
            return None

        self.mock_session.get.side_effect = get_side

        with patch.object(
            type(self.service._repo),
            "listar_por_ejecucion",
            return_value=[hallazgo_r, hallazgo_a],
        ):
            with patch.object(
                type(self.service._respuesta_repo),
                "obtener_por_id",
                side_effect=lambda rid: {101: respuesta_a, 102: respuesta_r}.get(
                    rid
                ),
            ):
                resultado = self.service.listar_por_ejecucion(10, self.usuario)

        assert len(resultado) == 2
        assert resultado[0].criterio_orden == 1
        assert resultado[1].criterio_orden == 2
        assert resultado[0].tipo == "A"
        assert resultado[1].tipo == "R"

    def test_no_crear_hallazgo_en_ejecucion_finalizada(self):
        """Caso 9: no permitir crear hallazgo en ejecucion finalizada."""
        respuesta = _respuesta()
        ejecucion = _ejecucion(estado="finalizada")
        self._configurar_lookups(respuesta, ejecucion)

        with patch.object(
            type(self.service._respuesta_repo),
            "obtener_por_id",
            return_value=respuesta,
        ):
            with pytest.raises(ValueError, match="finalizada"):
                self.service.crear(
                    HallazgoCreate(descripcion="x", respuesta_id=respuesta.id),
                    self.usuario,
                )

    def test_relaciones_correctas(self):
        """Caso 11: verificar que el hallazgo expone respuesta, criterio,
        ejecucion, auditoria y celula."""
        hallazgo = Hallazgo(
            id=1,
            descripcion="d",
            fecha_creacion=datetime.utcnow(),
            respuesta_id=100,
        )
        respuesta = _respuesta(valor="R")
        criterio = _criterio(id_=7, orden=4)
        ejecucion = MagicMock(spec=EjecucionAuditoria)
        ejecucion.id = 10
        ejecucion.estado = "en_proceso"
        ejecucion.auditoria_id = 1
        ejecucion.celula_id = None
        auditoria = _auditoria(nombre="Ensamble Final")

        def get_side(cls, _id):
            name = cls.__name__ if hasattr(cls, "__name__") else str(cls)
            if name == "EjecucionAuditoria":
                return ejecucion
            if name == "Criterio":
                return criterio
            if name == "Auditoria":
                return auditoria
            return None

        self.mock_session.get.side_effect = get_side

        with patch.object(
            type(self.service._repo), "obtener_por_id", return_value=hallazgo
        ):
            with patch.object(
                type(self.service._respuesta_repo),
                "obtener_por_id",
                return_value=respuesta,
            ):
                resultado = self.service.obtener_por_id(1)

        assert resultado.respuesta_id == 100
        assert resultado.criterio_id == 7
        assert resultado.criterio_orden == 4
        assert resultado.ejecucion_id == 10
        assert resultado.auditoria_id == 1
        assert resultado.auditoria_nombre == "Ensamble Final"
        assert resultado.tipo == "R"

class TestHallazgoEndpoint:
    """Pruebas del endpoint HTTP de hallazgos (smoke test del schema)."""

    def test_body_solo_descripcion_es_valido(self):
        """El body del POST debe aceptar solo descripcion (respuesta_id viene del path)."""
        from app.schemas.hallazgo import HallazgoBase

        # Esto NO debe lanzar ValidationError
        payload = HallazgoBase(descripcion="salto de paso")
        assert payload.descripcion == "salto de paso"

    def test_body_sin_descripcion_es_invalido(self):
        from pydantic import ValidationError
        from app.schemas.hallazgo import HallazgoBase

        with pytest.raises(ValidationError):
            HallazgoBase()  # type: ignore[call-arg]
