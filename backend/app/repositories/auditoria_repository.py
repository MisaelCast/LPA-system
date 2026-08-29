"""Repositorio para la entidad Auditoria."""

from sqlmodel import Session, select
from sqlmodel.sql.expression import SelectOfScalar

from app.models.auditoria import Auditoria


class AuditoriaRepository:
    """Acceso a datos para la tabla ``auditoria``."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def _base_query(self) -> SelectOfScalar[Auditoria]:
        return select(Auditoria)

    def obtener_por_id(self, auditoria_id: int) -> Auditoria | None:
        """Busca una auditoria por su identificador unico."""
        return self._session.exec(
            select(Auditoria).where(Auditoria.id == auditoria_id)
        ).first()

    def obtener_por_nombre(self, nombre: str) -> Auditoria | None:
        """Busca una auditoria por su nombre."""
        return self._session.exec(
            select(Auditoria).where(Auditoria.nombre == nombre)
        ).first()

    def listar(self, skip: int = 0, limit: int = 100) -> list[Auditoria]:
        """Lista auditorias con paginacion basica."""
        return list(
            self._session.exec(
                select(Auditoria).offset(skip).limit(limit)
            ).all()
        )

    def crear(self, auditoria: Auditoria) -> Auditoria:
        """Inserta una nueva auditoria en la base de datos."""
        self._session.add(auditoria)
        self._session.commit()
        self._session.refresh(auditoria)
        return auditoria

    def actualizar(self, auditoria: Auditoria) -> Auditoria:
        """Actualiza los datos de una auditoria existente."""
        self._session.merge(auditoria)
        self._session.commit()
        self._session.refresh(auditoria)
        return auditoria

    def eliminar(self, auditoria: Auditoria) -> None:
        """Elimina fisicamente una auditoria de la base de datos."""
        self._session.delete(auditoria)
        self._session.commit()
