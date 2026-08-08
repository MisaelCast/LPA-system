"""Logica de negocio para la entidad Criterio."""

from sqlmodel import Session

from app.models.criterio import Criterio
from app.repositories.criterio_repository import CriterioRepository
from app.schemas.criterio import CriterioCreate, CriterioUpdate


class CriterioService:
    """Servicio que encapsula la logica de negocio de criterios."""

    def __init__(self, session: Session) -> None:
        self._repo = CriterioRepository(session)

    def listar_por_auditoria(self, auditoria_id: int) -> list[Criterio]:
        """Obtiene los criterios de una auditoria ordenados."""
        return self._repo.listar_por_auditoria(auditoria_id)

    def obtener_por_id(self, criterio_id: int) -> Criterio:
        """Busca un criterio por su identificador.

        Raises:
            ValueError: Si el criterio no existe.
        """
        criterio = self._repo.obtener_por_id(criterio_id)
        if criterio is None:
            raise ValueError("Criterio no encontrado.")
        return criterio

    def crear(self, auditoria_id: int, datos: CriterioCreate) -> Criterio:
        """Crea un criterio para una auditoria.

        Si el orden ya esta ocupado, se asigna automaticamente
        el maximo orden + 1 para evitar duplicados.

        Raises:
            ValueError: Si la auditoria no existe.
        """
        from app.models.auditoria import Auditoria

        auditoria = self._repo._session.get(Auditoria, auditoria_id)
        if auditoria is None:
            raise ValueError("La auditoria especificada no existe.")

        orden = datos.orden
        existente = self._repo.obtener_por_auditoria_y_orden(
            auditoria_id, orden
        )
        if existente is not None:
            orden = self._repo.max_orden(auditoria_id) + 1

        criterio = Criterio(
            descripcion=datos.descripcion,
            orden=orden,
            activo=datos.activo,
            auditoria_id=auditoria_id,
        )

        return self._repo.crear(criterio)

    def actualizar(self, criterio_id: int, datos: CriterioUpdate) -> Criterio:
        """Actualiza un criterio.

        Si se cambia el orden a uno ya ocupado por otro criterio
        de la misma auditoria, se intercambian (swap).

        Raises:
            ValueError: Si el criterio no existe.
        """
        criterio = self._repo.obtener_por_id(criterio_id)
        if criterio is None:
            raise ValueError("Criterio no encontrado.")

        if datos.descripcion is not None:
            criterio.descripcion = datos.descripcion
        if datos.activo is not None:
            criterio.activo = datos.activo

        if (
            datos.orden is not None
            and datos.orden != criterio.orden
        ):
            existente = self._repo.obtener_por_auditoria_y_orden(
                criterio.auditoria_id, datos.orden
            )
            if existente is not None and existente.id != criterio_id:
                existente.orden = criterio.orden
                self._repo.actualizar(existente)

            criterio.orden = datos.orden

        return self._repo.actualizar(criterio)

    def cambiar_estado(self, criterio_id: int, activo: bool) -> Criterio:
        """Activa o desactiva un criterio.

        Raises:
            ValueError: Si el criterio no existe.
        """
        criterio = self._repo.obtener_por_id(criterio_id)
        if criterio is None:
            raise ValueError("Criterio no encontrado.")

        if criterio.activo == activo:
            return criterio

        criterio.activo = activo
        return self._repo.actualizar(criterio)
