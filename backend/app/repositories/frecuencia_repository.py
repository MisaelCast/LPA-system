"""Repositorio para la entidad Frecuencia."""

from sqlmodel import Session, select

from app.models.frecuencia import Frecuencia


class FrecuenciaRepository:
    """Acceso a datos para la tabla ``frecuencia``."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def obtener_por_id(self, frecuencia_id: int) -> Frecuencia | None:
        """Busca una frecuencia por su identificador unico."""
        return self._session.exec(
            select(Frecuencia).where(Frecuencia.id == frecuencia_id)
        ).first()

    def listar(self) -> list[Frecuencia]:
        """Lista todas las frecuencias."""
        return list(self._session.exec(select(Frecuencia)).all())
