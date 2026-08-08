"""Logica de negocio para la entidad Auditoria."""

from sqlmodel import Session

from app.models.auditoria import Auditoria
from app.repositories.auditoria_repository import AuditoriaRepository
from app.schemas.auditoria import AuditoriaCreate, AuditoriaUpdate
from app.services.capa_service import CapaService
from app.services.frecuencia_service import FrecuenciaService


class AuditoriaService:
    """Servicio que encapsula la logica de negocio de auditorias."""

    def __init__(self, session: Session) -> None:
        self._repo = AuditoriaRepository(session)
        self._session = session

    def _enriquecer_read(self, auditoria: Auditoria) -> Auditoria:
        """Adjunta nombres de entidades relacionadas para serializacion."""
        object.__setattr__(auditoria, "capa_nombre", "")
        object.__setattr__(auditoria, "frecuencia_nombre", "")
        object.__setattr__(auditoria, "area_nombre", None)

        if auditoria.capa_id is not None:
            from app.models.capa import Capa

            capa = self._session.get(Capa, auditoria.capa_id)
            if capa:
                object.__setattr__(auditoria, "capa_nombre", capa.nombre)

        if auditoria.frecuencia_id is not None:
            from app.models.frecuencia import Frecuencia

            frecuencia = self._session.get(Frecuencia, auditoria.frecuencia_id)
            if frecuencia:
                object.__setattr__(auditoria, "frecuencia_nombre", frecuencia.nombre)

        if auditoria.area_id is not None:
            from app.models.area import Area

            area = self._session.get(Area, auditoria.area_id)
            if area:
                object.__setattr__(auditoria, "area_nombre", area.nombre)

        return auditoria

    def listar(self, skip: int = 0, limit: int = 100) -> list[Auditoria]:
        """Obtiene un listado paginado de auditorias."""
        auditorias = self._repo.listar(skip=skip, limit=limit)
        return [self._enriquecer_read(a) for a in auditorias]

    def obtener_por_id(self, auditoria_id: int) -> Auditoria:
        """Busca una auditoria por su identificador.

        Raises:
            ValueError: Si la auditoria no existe.
        """
        auditoria = self._repo.obtener_por_id(auditoria_id)
        if auditoria is None:
            raise ValueError("Auditoria no encontrada.")
        return self._enriquecer_read(auditoria)

    def crear(self, datos: AuditoriaCreate) -> Auditoria:
        """Crea una auditoria aplicando las reglas de negocio.

        Raises:
            ValueError: Si el nombre ya esta registrado o una FK no existe.
        """
        if self._repo.obtener_por_nombre(datos.nombre):
            raise ValueError("Ya existe una auditoria con ese nombre.")

        capa_service = CapaService(self._session)
        try:
            capa_service.obtener_por_id(datos.capa_id)
        except ValueError:
            raise ValueError("La capa especificada no existe.")

        frecuencia_service = FrecuenciaService(self._session)
        try:
            frecuencia_service.obtener_por_id(datos.frecuencia_id)
        except ValueError:
            raise ValueError("La frecuencia especificada no existe.")

        auditoria = Auditoria(
            nombre=datos.nombre,
            descripcion=datos.descripcion,
            activa=datos.activa,
            capa_id=datos.capa_id,
            frecuencia_id=datos.frecuencia_id,
            area_id=datos.area_id,
        )

        creada = self._repo.crear(auditoria)
        return self._enriquecer_read(creada)

    def actualizar(self, auditoria_id: int, datos: AuditoriaUpdate) -> Auditoria:
        """Actualiza una auditoria aplicando las reglas de negocio.

        Raises:
            ValueError: Si la auditoria no existe,
                        el nombre ya esta en uso,
                        o una FK no existe.
        """
        auditoria = self._repo.obtener_por_id(auditoria_id)
        if auditoria is None:
            raise ValueError("Auditoria no encontrada.")

        if datos.nombre is not None and datos.nombre != auditoria.nombre:
            existente = self._repo.obtener_por_nombre(datos.nombre)
            if existente is not None and existente.id != auditoria_id:
                raise ValueError("Ya existe una auditoria con ese nombre.")

        if datos.capa_id is not None:
            from app.models.capa import Capa

            if self._session.get(Capa, datos.capa_id) is None:
                raise ValueError("La capa especificada no existe.")

        if datos.frecuencia_id is not None:
            from app.models.frecuencia import Frecuencia

            if self._session.get(Frecuencia, datos.frecuencia_id) is None:
                raise ValueError("La frecuencia especificada no existe.")

        if datos.nombre is not None:
            auditoria.nombre = datos.nombre
        if datos.descripcion is not None:
            auditoria.descripcion = datos.descripcion
        if datos.activa is not None:
            auditoria.activa = datos.activa
        if datos.capa_id is not None:
            auditoria.capa_id = datos.capa_id
        if datos.frecuencia_id is not None:
            auditoria.frecuencia_id = datos.frecuencia_id
        if datos.area_id is not None:
            auditoria.area_id = datos.area_id

        actualizada = self._repo.actualizar(auditoria)
        return self._enriquecer_read(actualizada)

    def cambiar_estado(self, auditoria_id: int, activa: bool) -> Auditoria:
        """Activa o desactiva una auditoria.

        Raises:
            ValueError: Si la auditoria no existe.
        """
        auditoria = self._repo.obtener_por_id(auditoria_id)
        if auditoria is None:
            raise ValueError("Auditoria no encontrada.")

        if auditoria.activa == activa:
            return self._enriquecer_read(auditoria)

        auditoria.activa = activa
        actualizada = self._repo.actualizar(auditoria)
        return self._enriquecer_read(actualizada)
