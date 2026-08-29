"""Repositorio para la entidad Area."""

from sqlmodel import Session, select

from app.models.area import Area


class AreaRepository:
    """Acceso a datos para la tabla ``area``."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def obtener_por_id(self, area_id: int) -> Area | None:
        """Busca un area por su identificador unico."""
        return self._session.exec(
            select(Area).where(Area.id == area_id)
        ).first()

    def obtener_por_nombre(self, nombre: str) -> Area | None:
        """Busca un area por su nombre."""
        return self._session.exec(
            select(Area).where(Area.nombre == nombre)
        ).first()

    def listar(self, skip: int = 0, limit: int = 100) -> list[Area]:
        """Lista areas con paginacion basica."""
        return list(
            self._session.exec(
                select(Area).offset(skip).limit(limit)
            ).all()
        )

    def crear(self, area: Area) -> Area:
        """Inserta una nueva area en la base de datos."""
        self._session.add(area)
        self._session.commit()
        self._session.refresh(area)
        return area

    def actualizar(self, area: Area) -> Area:
        """Actualiza los datos de un area existente."""
        self._session.merge(area)
        self._session.commit()
        self._session.refresh(area)
        return area

    def eliminar(self, area: Area) -> None:
        """Elimina fisicamente un area de la base de datos."""
        self._session.delete(area)
        self._session.commit()
