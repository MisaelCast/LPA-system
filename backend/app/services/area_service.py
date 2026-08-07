"""Logica de negocio para la entidad Area."""

from sqlmodel import Session

from app.models.area import Area
from app.repositories.area_repository import AreaRepository
from app.schemas.area import AreaCreate, AreaUpdate


class AreaService:
    """Servicio que encapsula la logica de negocio de areas."""

    def __init__(self, session: Session) -> None:
        self._repo = AreaRepository(session)

    def listar(self, skip: int = 0, limit: int = 100) -> list[Area]:
        """Obtiene un listado paginado de areas."""
        return self._repo.listar(skip=skip, limit=limit)

    def obtener_por_id(self, area_id: int) -> Area:
        """Busca un area por su identificador.

        Raises:
            ValueError: Si el area no existe.
        """
        area = self._repo.obtener_por_id(area_id)
        if area is None:
            raise ValueError("Area no encontrada.")
        return area

    def crear(self, datos: AreaCreate) -> Area:
        """Crea un area aplicando las reglas de negocio.

        Raises:
            ValueError: Si el nombre ya esta registrado.
        """
        if self._repo.obtener_por_nombre(datos.nombre):
            raise ValueError("Ya existe un area con ese nombre.")

        area = Area(
            nombre=datos.nombre,
            descripcion=datos.descripcion,
            activa=datos.activa,
        )

        return self._repo.crear(area)

    def actualizar(self, area_id: int, datos: AreaUpdate) -> Area:
        """Actualiza un area aplicando las reglas de negocio.

        Raises:
            ValueError: Si el area no existe o el nombre ya esta en uso.
        """
        area = self.obtener_por_id(area_id)

        if datos.nombre is not None and datos.nombre != area.nombre:
            existente = self._repo.obtener_por_nombre(datos.nombre)
            if existente is not None and existente.id != area_id:
                raise ValueError("Ya existe un area con ese nombre.")

        if datos.nombre is not None:
            area.nombre = datos.nombre
        if datos.descripcion is not None:
            area.descripcion = datos.descripcion
        if datos.activa is not None:
            area.activa = datos.activa

        return self._repo.actualizar(area)

    def cambiar_estado(self, area_id: int, activa: bool) -> Area:
        """Activa o desactiva un area.

        Raises:
            ValueError: Si el area no existe.
        """
        area = self.obtener_por_id(area_id)

        if area.activa == activa:
            return area

        area.activa = activa
        return self._repo.actualizar(area)
