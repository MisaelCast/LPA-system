"""Logica de negocio para la entidad Capa."""

from sqlmodel import Session

from app.models.capa import Capa
from app.repositories.capa_repository import CapaRepository
from app.schemas.capa import CapaCreate, CapaUpdate


class CapaService:
    """Servicio que encapsula la logica de negocio de capas."""

    def __init__(self, session: Session) -> None:
        self._repo = CapaRepository(session)

    def listar(self, skip: int = 0, limit: int = 100) -> list[Capa]:
        """Obtiene un listado paginado de capas."""
        return self._repo.listar(skip=skip, limit=limit)

    def obtener_por_id(self, capa_id: int) -> Capa:
        """Busca una capa por su identificador.

        Raises:
            ValueError: Si la capa no existe.
        """
        capa = self._repo.obtener_por_id(capa_id)
        if capa is None:
            raise ValueError("Capa no encontrada.")
        return capa

    def crear(self, datos: CapaCreate) -> Capa:
        """Crea una capa aplicando las reglas de negocio.

        Raises:
            ValueError: Si el nombre ya esta registrado.
        """
        if self._repo.obtener_por_nombre(datos.nombre):
            raise ValueError("Ya existe una capa con ese nombre.")

        capa = Capa(
            nombre=datos.nombre,
            descripcion=datos.descripcion,
            activa=datos.activa,
        )

        return self._repo.crear(capa)

    def actualizar(self, capa_id: int, datos: CapaUpdate) -> Capa:
        """Actualiza una capa aplicando las reglas de negocio.

        Raises:
            ValueError: Si la capa no existe o el nombre ya esta en uso.
        """
        capa = self.obtener_por_id(capa_id)

        if datos.nombre is not None and datos.nombre != capa.nombre:
            existente = self._repo.obtener_por_nombre(datos.nombre)
            if existente is not None and existente.id != capa_id:
                raise ValueError("Ya existe una capa con ese nombre.")

        if datos.nombre is not None:
            capa.nombre = datos.nombre
        if datos.descripcion is not None:
            capa.descripcion = datos.descripcion
        if datos.activa is not None:
            capa.activa = datos.activa

        return self._repo.actualizar(capa)

    def cambiar_estado(self, capa_id: int, activa: bool) -> Capa:
        """Activa o desactiva una capa.

        Raises:
            ValueError: Si la capa no existe.
        """
        capa = self.obtener_por_id(capa_id)

        if capa.activa == activa:
            return capa

        capa.activa = activa
        return self._repo.actualizar(capa)
