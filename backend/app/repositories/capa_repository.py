"""Repositorio para la entidad Capa."""

from sqlmodel import Session, select

from app.models.capa import Capa


class CapaRepository:
    """Acceso a datos para la tabla ``capa``."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def obtener_por_id(self, capa_id: int) -> Capa | None:
        """Busca una capa por su identificador unico."""
        return self._session.exec(
            select(Capa).where(Capa.id == capa_id)
        ).first()

    def obtener_por_nombre(self, nombre: str) -> Capa | None:
        """Busca una capa por su nombre."""
        return self._session.exec(
            select(Capa).where(Capa.nombre == nombre)
        ).first()

    def listar(self, skip: int = 0, limit: int = 100) -> list[Capa]:
        """Lista capas con paginacion basica."""
        return list(
            self._session.exec(
                select(Capa).offset(skip).limit(limit)
            ).all()
        )

    def crear(self, capa: Capa) -> Capa:
        """Inserta una nueva capa en la base de datos."""
        self._session.add(capa)
        self._session.commit()
        self._session.refresh(capa)
        return capa

    def actualizar(self, capa: Capa) -> Capa:
        """Actualiza los datos de una capa existente."""
        self._session.merge(capa)
        self._session.commit()
        self._session.refresh(capa)
        return capa

    def eliminar(self, capa: Capa) -> None:
        """Elimina fisicamente una capa de la base de datos."""
        self._session.delete(capa)
        self._session.commit()
