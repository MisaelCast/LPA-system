"""Servicio de evidencias (fotos) de hallazgos en Supabase Storage."""

import uuid
from datetime import datetime, timezone

from sqlmodel import Session, select
from supabase import Client, create_client

from app.config import settings
from app.models.ejecucion_auditoria import EjecucionAuditoria
from app.models.evidencia import Evidencia
from app.models.hallazgo import Hallazgo
from app.models.respuesta import Respuesta
from app.models.usuario import Usuario
from app.schemas.evidencia import EvidenciaOut

_MAXIMO_BYTES = 5 * 1024 * 1024  # 5 MB
_EXTENSIONES: dict[str, str] = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".webp": "image/webp",
}


def _cliente() -> Client:
    return create_client(settings.supabase_url, settings.supabase_service_key)


def url_firmada(ruta: str) -> str | None:
    """URL firmada (temporal) para una ruta del bucket privado."""
    if not settings.supabase_url or not settings.supabase_service_key:
        return None
    try:
        bucket = _cliente().storage.from_(settings.supabase_bucket)
        datos = bucket.create_signed_url(
            ruta, expires_in=settings.evidencia_url_expira_segundos
        )
        return (
            datos.get("signedURL")
            or datos.get("signed_url")
            or datos.get("signedUrl")
        )
    except Exception:
        return None


class EvidenciaService:
    """Carga, consulta y borrado de fotos de hallazgos."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def _hallazgo_autorizado(
        self, hallazgo_id: int, usuario: Usuario
    ) -> Hallazgo:
        hallazgo = self._session.get(Hallazgo, hallazgo_id)
        if hallazgo is None:
            raise ValueError("Hallazgo no encontrado.")
        respuesta = self._session.get(Respuesta, hallazgo.respuesta_id)
        if respuesta is None:
            raise ValueError("Respuesta no encontrada.")
        ejecucion = self._session.get(
            EjecucionAuditoria, respuesta.ejecucion_auditoria_id
        )
        if ejecucion is None:
            raise ValueError("Ejecucion de auditoria no encontrada.")
        rol = getattr(getattr(usuario, "rol", None), "nombre", "")
        if usuario.id != ejecucion.usuario_id and rol != "Administrador":
            raise ValueError(
                "No tiene permiso para gestionar las evidencias de este "
                "hallazgo."
            )
        return hallazgo

    def subir(
        self,
        hallazgo_id: int,
        nombre_archivo: str | None,
        contenido: bytes,
        usuario: Usuario,
    ) -> EvidenciaOut:
        hallazgo = self._hallazgo_autorizado(hallazgo_id, usuario)

        if not contenido:
            raise ValueError("El archivo esta vacio.")
        if len(contenido) > _MAXIMO_BYTES:
            raise ValueError("La imagen supera el limite de 5 MB.")

        partes = (nombre_archivo or "").rsplit(".", 1)
        extension = f".{partes[-1].lower()}" if len(partes) > 1 else ""
        if extension not in _EXTENSIONES:
            raise ValueError(
                "Formato no permitido. Use archivos JPG, PNG o WEBP."
            )

        if not settings.supabase_url or not settings.supabase_service_key:
            raise ValueError("El almacenamiento (Supabase) no esta configurado.")

        tipo = _EXTENSIONES[extension]
        ruta = f"{hallazgo.id}/{uuid.uuid4().hex}{extension}"
        try:
            bucket = _cliente().storage.from_(settings.supabase_bucket)
            bucket.upload(
                path=ruta,
                file=contenido,
                file_options={"content-type": tipo, "x-upsert": "false"},
            )
        except Exception as error:
            raise ValueError(
                f"No se pudo subir la imagen al almacenamiento: {error}"
            ) from error

        evidencia = Evidencia(
            ruta_archivo=ruta,
            tipo_archivo=tipo,
            fecha_carga=datetime.now(timezone.utc),
            hallazgo_id=hallazgo.id,
        )
        self._session.add(evidencia)
        self._session.commit()
        self._session.refresh(evidencia)
        return EvidenciaOut(
            id=evidencia.id or 0,
            fecha_carga=evidencia.fecha_carga,
            tipo_archivo=evidencia.tipo_archivo,
            url=url_firmada(ruta),
        )

    def listar(self, hallazgo_id: int, usuario: Usuario) -> list[EvidenciaOut]:
        hallazgo = self._hallazgo_autorizado(hallazgo_id, usuario)
        filas = self._session.exec(
            select(Evidencia)
            .where(Evidencia.hallazgo_id == hallazgo.id)
            .order_by(Evidencia.id)
        ).all()
        return [
            EvidenciaOut(
                id=e.id or 0,
                fecha_carga=e.fecha_carga,
                tipo_archivo=e.tipo_archivo,
                url=url_firmada(e.ruta_archivo),
            )
            for e in filas
        ]

    def eliminar(self, evidencia_id: int, usuario: Usuario) -> None:
        evidencia = self._session.get(Evidencia, evidencia_id)
        if evidencia is None:
            raise ValueError("Evidencia no encontrada.")
        self._hallazgo_autorizado(evidencia.hallazgo_id, usuario)
        self._borrar_de_storage([evidencia.ruta_archivo])
        self._session.delete(evidencia)
        self._session.commit()

    def eliminar_de_hallazgo(self, hallazgo: Hallazgo) -> None:
        """Borra del storage y de la BD todas las evidencias del hallazgo.

        No hace commit: forma parte de la transacción del borrado del
        hallazgo (el caller debe confirmarla).
        """
        filas = self._session.exec(
            select(Evidencia).where(Evidencia.hallazgo_id == hallazgo.id)
        ).all()
        if not filas:
            return
        self._borrar_de_storage([e.ruta_archivo for e in filas])
        for fila in filas:
            self._session.delete(fila)

    @staticmethod
    def _borrar_de_storage(rutas: list[str]) -> None:
        """Borra rutas del bucket (mejor esfuerzo: no bloquea la operación)."""
        if not rutas or not settings.supabase_url:
            return
        try:
            _cliente().storage.from_(settings.supabase_bucket).remove(rutas)
        except Exception:
            pass
