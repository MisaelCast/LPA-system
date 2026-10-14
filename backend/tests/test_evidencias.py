"""Pruebas para el servicio de Evidencias (Supabase Storage)."""

from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest
from sqlmodel import Session

from app.models.ejecucion_auditoria import EjecucionAuditoria
from app.models.evidencia import Evidencia
from app.models.hallazgo import Hallazgo
from app.models.respuesta import Respuesta
from app.services.evidencia_service import EvidenciaService

PNG = b"\x89PNG\r\n\x1a\n" + b"0" * 100


def _usuario(id_: int = 1, rol_nombre: str = "Auditor") -> MagicMock:
    usuario = MagicMock()
    usuario.id = id_
    rol = MagicMock()
    rol.nombre = rol_nombre
    usuario.rol = rol
    return usuario


def _ejecucion(usuario_id: int = 1) -> MagicMock:
    ej = MagicMock(spec=EjecucionAuditoria)
    ej.id = 10
    ej.usuario_id = usuario_id
    return ej


def _respuesta() -> MagicMock:
    r = MagicMock(spec=Respuesta)
    r.id = 100
    r.ejecucion_auditoria_id = 10
    return r


def _hallazgo(id_: int = 7) -> MagicMock:
    h = MagicMock(spec=Hallazgo)
    h.id = id_
    h.respuesta_id = 100
    h.evidencias = []
    return h


class _BucketFake:
    def __init__(self) -> None:
        self.subidas: list[tuple] = []
        self.borradas: list[str] = []

    def upload(self, path, file, file_options=None):
        self.subidas.append((path, file, file_options))
        return {"Key": path}

    def create_signed_url(self, path, expires_in=3600):
        return {"signedURL": f"https://fake.s3/{path}?exp={expires_in}"}

    def remove(self, paths):
        self.borradas.extend(paths)
        return []


class _ClienteFake:
    def __init__(self, bucket: _BucketFake) -> None:
        self.storage = MagicMock()
        self.storage.from_.return_value = bucket


class TestEvidenciaService:
    def setup_method(self):
        self.mock_session = MagicMock(spec=Session)
        self.service = EvidenciaService(self.mock_session)
        self.usuario = _usuario()
        self.bucket = _BucketFake()

        def get_side(cls, _id):
            name = cls.__name__ if hasattr(cls, "__name__") else str(cls)
            if name == "Hallazgo":
                return _hallazgo(_id)
            if name == "Respuesta":
                return _respuesta()
            if name == "EjecucionAuditoria":
                return _ejecucion()
            return None

        self.mock_session.get.side_effect = get_side

    def _parchear_storage(self):
        return patch(
            "app.services.evidencia_service._cliente",
            return_value=_ClienteFake(self.bucket),
        )

    def test_subir_ok_genera_ruta_y_url_firmada(self):
        with self._parchear_storage():
            resultado = self.service.subir(7, "foto.png", PNG, self.usuario)

        assert resultado.url and "fake.s3" in resultado.url
        assert resultado.tipo_archivo == "image/png"
        assert len(self.bucket.subidas) == 1
        ruta, contenido, opciones = self.bucket.subidas[0]
        assert ruta.startswith("7/")
        assert contenido == PNG
        assert opciones["content-type"] == "image/png"
        self.mock_session.add.assert_called_once()

    def test_subir_formato_invalido_rechazado(self):
        with self._parchear_storage():
            with pytest.raises(ValueError, match="Formato no permitido"):
                self.service.subir(7, "foto.gif", PNG, self.usuario)
        assert not self.bucket.subidas

    def test_subir_archivo_sobre_5mb_rechazado(self):
        grande = b"x" * (5 * 1024 * 1024 + 1)
        with self._parchear_storage():
            with pytest.raises(ValueError, match="5 MB"):
                self.service.subir(7, "foto.png", grande, self.usuario)

    def test_subir_sin_permiso_rechazado(self):
        otro = _usuario(id_=99, rol_nombre="Auditor")
        with self._parchear_storage():
            with pytest.raises(ValueError, match="permiso"):
                self.service.subir(7, "foto.png", PNG, otro)
        assert not self.bucket.subidas

    def test_listar_genera_urls_firmadas(self):
        fila = Evidencia(
            id=1,
            ruta_archivo="7/abc.png",
            tipo_archivo="image/png",
            fecha_carga=datetime.now(timezone.utc),
            hallazgo_id=7,
        )
        resultado_rows = [fila]
        self.mock_session.exec.return_value.all.return_value = resultado_rows

        with self._parchear_storage():
            evidencias = self.service.listar(7, self.usuario)

        assert len(evidencias) == 1
        assert evidencias[0].url and "7/abc.png" in evidencias[0].url

    def test_eliminar_borra_storage_y_base(self):
        evidencia = MagicMock(spec=Evidencia)
        evidencia.id = 5
        evidencia.hallazgo_id = 7
        evidencia.ruta_archivo = "7/abc.png"

        def get_side(cls, _id):
            name = cls.__name__ if hasattr(cls, "__name__") else str(cls)
            if name == "Evidencia":
                return evidencia
            if name == "Hallazgo":
                return _hallazgo(_id)
            if name == "Respuesta":
                return _respuesta()
            if name == "EjecucionAuditoria":
                return _ejecucion()
            return None

        self.mock_session.get.side_effect = get_side

        with self._parchear_storage():
            self.service.eliminar(5, self.usuario)

        assert "7/abc.png" in self.bucket.borradas
        self.mock_session.delete.assert_called_once_with(evidencia)
        self.mock_session.commit.assert_called_once()

    def test_hallazgo_inexistente_rechazado(self):
        self.mock_session.get.side_effect = None
        self.mock_session.get.return_value = None
        with pytest.raises(ValueError, match="no encontrado"):
            self.service.subir(999, "foto.png", PNG, self.usuario)
